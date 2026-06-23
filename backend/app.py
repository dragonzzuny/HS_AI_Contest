#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
화성ON 백엔드 — 다국어 외국인 생활민원 AI 안내사.

단일 FastAPI 앱: 프론트 서빙 + 인용기반 답변 + 처리보조(서류초안·체크리스트·딥링크).
LLM/벡터DB가 없어도 'MOCK 모드'로 즉시 작동(키워드 검색 + 템플릿 답변)하여 UX 검증 가능.
Ollama/Weaviate가 잡히면 자동으로 실동작(하이브리드 검색 + 그라운딩 생성)으로 승격.

실행:
  pip install -r backend/requirements.txt
  uvicorn backend.app:app --host 0.0.0.0 --port 5200
환경변수(선택):
  OLLAMA_HOST=http://localhost:11434   GEN_MODEL=qwen2.5:14b   EMBED_MODEL=bge-m3
  WEAVIATE_HOST=localhost
"""
import json
import os
import re
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parent.parent
KB_JSON = ROOT / "kb" / "build" / "kb.json"
ORD_JSON = ROOT / "kb" / "build" / "ordinances_chunks.json"
WEB_DIR = ROOT / "web"

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "").strip()      # 비면 MOCK 생성
GEN_MODEL = os.environ.get("GEN_MODEL", "qwen2.5:14b").strip()
EMBED_MODEL = os.environ.get("EMBED_MODEL", "bge-m3").strip()
WEAVIATE_HOST = os.environ.get("WEAVIATE_HOST", "").strip()  # 비면 KB 키워드 검색

LANGS = {
    "ko": "한국어", "en": "English", "zh": "中文",
    "vi": "Tiếng Việt", "th": "ภาษาไทย", "km": "ភាសាខ្មែរ",
}

# ── 처리보조: 도메인별 신청 딥링크 ─────────────────────────────
DEEPLINKS = {
    "체류": [
        {"label": "하이코리아 전자민원/방문예약", "url": "https://www.hikorea.go.kr"},
    ],
    "노무": [
        {"label": "고용노동부 노동포털(진정서 온라인 접수)", "url": "https://labor.moel.go.kr"},
    ],
    "건강보험": [
        {"label": "국민건강보험공단 민원여기요", "url": "https://www.nhis.or.kr"},
    ],
    "폐기물": [
        {"label": "대형폐기물 신고(빼기)", "url": "https://bbegi.com"},
        {"label": "폐가전 무상방문수거", "url": "https://www.15990903.or.kr"},
    ],
    "보육교육": [
        {"label": "아이사랑(어린이집 입소대기)", "url": "https://www.childcare.go.kr"},
    ],
    "운전면허": [
        {"label": "도로교통공단 안전운전 통합민원", "url": "https://www.safedriving.or.kr"},
    ],
    "행정": [
        {"label": "정부24", "url": "https://www.gov.kr"},
    ],
    "지원기관": [],
}

# ── 처리보조: 서류초안 입력 스키마(빈칸 → 한국어 공식 서류) ──────
FORM_SCHEMAS = {
    "노무": {
        "title": "임금체불 진정서",
        "desc": "고용노동부 노동포털 진정서 작성용 한국어 초안을 만듭니다.",
        "fields": [
            {"key": "name", "label": "이름", "ph": "Nguyen Van A"},
            {"key": "nationality", "label": "국적", "ph": "베트남"},
            {"key": "phone", "label": "연락처", "ph": "010-0000-0000"},
            {"key": "company", "label": "사업장명", "ph": "○○산업(주)"},
            {"key": "company_addr", "label": "사업장 주소", "ph": "화성시 향남읍 ..."},
            {"key": "start_date", "label": "입사일", "ph": "2025-03-01"},
            {"key": "end_date", "label": "퇴사일(재직 중이면 '재직')", "ph": "재직"},
            {"key": "amount", "label": "체불 금액(원)", "ph": "3000000"},
            {"key": "period", "label": "체불 기간", "ph": "2026-03 ~ 2026-05"},
        ],
    },
    "폐기물": {
        "title": "대형폐기물 배출 신고",
        "desc": "빼기(bbegi)/화성시 청소행정포털 신청용 내용을 정리합니다.",
        "fields": [
            {"key": "item", "label": "품목", "ph": "2인용 소파"},
            {"key": "qty", "label": "수량", "ph": "1"},
            {"key": "date", "label": "배출 희망일", "ph": "2026-06-25"},
            {"key": "location", "label": "배출 장소", "ph": "○○아파트 분리수거장"},
            {"key": "phone", "label": "연락처", "ph": "010-0000-0000"},
        ],
    },
}


def _f(fields, key, default="(미입력)"):
    v = (fields or {}).get(key, "")
    return v.strip() if isinstance(v, str) and v.strip() else default


def render_draft(domain, fields, today="년 월 일"):
    """입력값 → 한국어 공식 서류 초안(템플릿). LLM 없이도 동작."""
    if domain == "노무":
        amount = _f(fields, "amount", "")
        amount_s = f"{int(amount):,}" if amount.isdigit() else _f(fields, "amount")
        return (
            "진 정 서 (임금체불)\n\n"
            "1. 진정인\n"
            f"  - 성명: {_f(fields,'name')}\n"
            f"  - 국적: {_f(fields,'nationality')}\n"
            f"  - 연락처: {_f(fields,'phone')}\n\n"
            "2. 피진정인(사업주)\n"
            f"  - 사업장명: {_f(fields,'company')}\n"
            f"  - 사업장 소재지: {_f(fields,'company_addr')}\n\n"
            "3. 진정 내용\n"
            f"  본인은 {_f(fields,'company')}에서 "
            + (f"{_f(fields,'start_date')}부터 현재까지 재직 중이며, "
               if _f(fields, 'end_date') in ("재직", "재직중", "현재") else
               f"{_f(fields,'start_date')}부터 {_f(fields,'end_date')}까지 근무하였으며, ")
            + f"{_f(fields,'period')} 기간의 임금 합계 금 {amount_s}원을 "
            "정당한 사유 없이 지급받지 못하였기에, 「근로기준법」에 따라 "
            "체불 임금의 지급을 요청하고자 본 진정서를 제출합니다.\n\n"
            f"4. 요구사항: 체불 임금 {amount_s}원의 즉시 지급\n\n"
            f"{today}\n"
            f"진정인: {_f(fields,'name')} (서명)\n\n"
            "중부지방고용노동청 경기지청장 귀하\n\n"
            "※ 제출: 고용노동부 노동포털(labor.moel.go.kr) 온라인 진정 / 통역상담 ☎1350"
        )
    if domain == "폐기물":
        return (
            "[대형폐기물 배출 신고 내용]\n\n"
            f"  - 배출 품목: {_f(fields,'item')}\n"
            f"  - 수량: {_f(fields,'qty')}\n"
            f"  - 배출 희망일: {_f(fields,'date')}\n"
            f"  - 배출 장소: {_f(fields,'location')}\n"
            f"  - 신청인 연락처: {_f(fields,'phone')}\n\n"
            "※ 신청: 빼기(bbegi.com) 앱 또는 화성시 청소행정포털에 위 내용으로 신청 →\n"
            "  결제 후 발급된 예약번호를 폐기물에 부착하여 배출하세요.\n"
            "  문의: 화성시 자원순환과 ☎031-5189-6818"
        )
    return ""


class ChatRequest(BaseModel):
    message: str
    lang: str = "ko"


class DraftRequest(BaseModel):
    domain: str
    fields: dict = {}
    lang: str = "ko"
    today: str = "년    월    일"


def _tokens(s: str):
    s = (s or "").lower()
    words = [t for t in re.split(r"[^0-9a-z가-힣]+", s) if len(t) >= 2]
    # CJK(한자)는 단어경계가 없으므로 문자 bigram으로 보강
    cjk = re.findall(r"[一-鿿]", s)
    words += [cjk[i] + cjk[i + 1] for i in range(len(cjk) - 1)]
    return words


# 도메인별 다국어 트리거(부분일치) — 목 모드 교차언어 라우팅용.
# (실동작에서는 BGE-M3 교차언어 임베딩이 이 역할을 대체)
DOMAIN_TRIGGERS = {
    "체류": ["외국인등록", "체류", "비자", "등록증", "register", "foreigner", "alien", "visa",
            "residence", "外国人", "登录", "居留", "签证", "đăng ký", "người nước ngoài",
            "thị thực", "cư trú", "ngoại", "ต่างชาติ", "ลงทะเบียน", "วีซ่า",
            "ជនបរទេស", "ចុះឈ្មោះ", "ទិដ្ឋាការ"],
    "폐기물": ["쓰레기", "분리수거", "종량제", "대형폐기물", "음식물", "재활용",
             "trash", "garbage", "waste", "rubbish", "recycle", "垃圾", "扔垃圾", "分类",
             "rác", "vứt rác", "ขยะ", "ทิ้งขยะ", "សំរាម", "បោះសំរាម"],
    "노무": ["임금", "월급", "급여", "체불", "근로", "노동", "산재", "퇴직금",
            "wage", "salary", "unpaid", "labor", "labour", "work", "工资", "拖欠", "劳动",
            "lương", "tiền lương", "nợ lương", "ค่าจ้าง", "เงินเดือน", "ប្រាក់ឈ្នួល"],
    "건강보험": ["건강보험", "보험료", "병원", "의료", "health insurance", "premium", "hospital",
              "medical", "健康保险", "医院", "保险", "bảo hiểm", "bệnh viện",
              "ประกันสุขภาพ", "โรงพยาบาล", "ធានារ៉ាប់រង", "មន្ទីរពេទ្យ"],
    "보육교육": ["어린이집", "유치원", "학교", "입학", "보육", "교육", "자녀",
              "daycare", "kindergarten", "school", "enroll", "child", "幼儿园", "学校", "入学",
              "nhà trẻ", "trường học", "โรงเรียน", "อนุบาล", "សាលា", "កុមារ"],
    "운전면허": ["운전면허", "면허", "운전", "driver", "license", "licence", "driving",
              "驾照", "驾驶", "bằng lái", "lái xe", "ใบขับขี่", "ប័ណ្ណបើកបរ"],
    "행정": ["전입신고", "주소", "이사", "주민센터", "move", "address", "搬家", "地址",
            "chuyển nhà", "địa chỉ", "ย้ายบ้าน", "ផ្លាស់ប្ដូរ"],
}


class Corpus:
    """KB(L1) + 자치법규(L2) 로드 및 키워드 검색(폴백)."""
    def __init__(self):
        self.items = []
        if KB_JSON.exists():
            for it in json.loads(KB_JSON.read_text(encoding="utf-8")):
                self.items.append({
                    "id": it["id"], "layer": "L1",
                    "title": it.get("title", ""), "domain": it.get("domain", ""),
                    "answer": it.get("answer", ""), "target": it.get("target", ""),
                    "documents": it.get("documents", ""), "dept": it.get("dept", ""),
                    "phone": it.get("phone", ""), "location": it.get("location", ""),
                    "source": it.get("source", ""),
                    "confidence": (it.get("confidence", "") or "").split()[0],
                    "questions": it.get("questions", []),
                    "_blob": " ".join([it.get("title", ""), it.get("target", ""),
                                       it.get("answer", ""), it.get("documents", ""),
                                       " ".join(it.get("questions", []))]),
                })
        if ORD_JSON.exists():
            for c in json.loads(ORD_JSON.read_text(encoding="utf-8")):
                self.items.append({
                    "id": c["id"], "layer": "L2",
                    "title": f"{c.get('law_name','')} {c.get('article','')}",
                    "domain": "법령", "answer": c.get("content", ""), "target": "",
                    "documents": "", "dept": c.get("kind", ""), "phone": "",
                    "location": "", "source": c.get("source", ""),
                    "confidence": "확인됨", "questions": [],
                    "_blob": f"{c.get('law_name','')} {c.get('content','')}",
                })

    def search(self, query: str, k: int = 4):
        ql = (query or "").lower()
        q = set(_tokens(query))
        # 법령 의도가 명시된 질의만 L2(조례)를 상위 노출
        law_intent = any(w in ql for w in
                         ["조례", "규칙", "법령", "조문", "자치법규", "law", "ordinance", "article"])
        # 다국어 트리거로 매칭된 도메인(교차언어 라우팅)
        boosted = {dom for dom, kws in DOMAIN_TRIGGERS.items()
                   if any(kw.lower() in ql for kw in kws)}
        scored = []
        for it in self.items:
            blob = set(_tokens(it["_blob"]))
            overlap = len(q & blob)
            if it["layer"] == "L1":
                score = overlap * 1.5
                for qx in it.get("questions", []):
                    if q & set(_tokens(qx)):
                        score += 3
                if it["domain"] in boosted:
                    score += 10          # 교차언어: 같은 도메인 L1 강하게 부스팅
            else:  # L2 자치법규
                score = overlap * (0.8 if law_intent else 0.25)
                if it["domain"] in boosted:
                    score += 1
            if score > 0:
                scored.append((score, it))
        scored.sort(key=lambda x: x[0], reverse=True)
        ordered = [it for _, it in scored]
        if not law_intent:  # 생활민원 질의는 L1을 항상 우선
            ordered = [it for it in ordered if it["layer"] == "L1"] + \
                      [it for it in ordered if it["layer"] == "L2"]
        return ordered[:k]


CORPUS = Corpus()
app = FastAPI(title="화성ON")


def build_actions(hits):
    """검색된 항목에서 처리보조(딥링크·체크리스트·서류초안) 구성."""
    actions = []
    seen = set()
    for h in hits:
        dom = h["domain"]
        for dl in DEEPLINKS.get(dom, []):
            if dl["url"] not in seen:
                actions.append({"type": "link", **dl})
                seen.add(dl["url"])
        if h.get("documents"):
            actions.append({"type": "checklist", "title": f"{h['title']} 필요서류",
                            "items": [x.strip() for x in re.split(r"[,·]", h["documents"]) if x.strip()]})
        if dom in FORM_SCHEMAS and not any(a["type"] == "form" for a in actions):
            sc = FORM_SCHEMAS[dom]
            actions.append({"type": "form", "domain": dom,
                            "title": sc["title"], "desc": sc["desc"], "fields": sc["fields"]})
    return actions[:6]


GROUNDED_SYS = (
    "당신은 화성시 거주 외국인을 돕는 '화성ON' 민원 안내사다. "
    "반드시 아래 제공된 [근거]만 사용해 답하라. 근거에 없는 내용은 지어내지 말고 "
    "'정확한 확인을 위해 담당기관에 문의하세요'라고 안내하라. "
    "답변은 사용자 언어({lang})로 쓰되, 핵심 절차는 단계별로, 마지막에 담당부서·전화를 제시하라. "
    "사용한 근거의 ID를 문장 끝에 [id] 형태로 표기하라."
)


def make_context(hits):
    blocks = []
    for h in hits:
        blocks.append(
            f"[{h['id']}] {h['title']}\n대상:{h.get('target','')}\n"
            f"내용:{h['answer']}\n담당:{h.get('dept','')} 전화:{h.get('phone','')}\n"
            f"출처:{h.get('source','')} 신뢰도:{h.get('confidence','')}"
        )
    return "\n\n".join(blocks)


def mock_answer(query, lang, hits):
    if not hits:
        return ("죄송합니다. 해당 민원 정보를 찾지 못했습니다. "
                "화성시 콜센터 ☎1688-0911 또는 다누리콜센터 ☎1577-1366으로 문의하세요. "
                "(MOCK 모드 — Ollama 연결 시 다국어 실답변)")
    top = hits[0]
    note = "" if lang == "ko" else f"\n\n[{LANGS.get(lang, lang)} 답변은 Ollama 연결 시 제공됩니다 — 현재 MOCK]"
    dept, phone = top.get("dept", ""), top.get("phone", "")
    meta = f"📌 담당: {dept}" + (f" {phone}" if phone else "")   # phone에 이미 ☎ 포함
    return f"{top['answer']}\n\n{meta} [{top['id']}]{note}"


async def ollama_generate(query, lang, hits) -> Optional[str]:
    if not OLLAMA_HOST:
        return None
    prompt = (f"[근거]\n{make_context(hits)}\n\n[질문]\n{query}\n\n"
              f"위 근거만으로 {LANGS.get(lang,'한국어')}로 답하라.")
    try:
        async with httpx.AsyncClient(timeout=120) as cli:
            r = await cli.post(f"{OLLAMA_HOST}/api/chat", json={
                "model": GEN_MODEL, "stream": False,
                "messages": [
                    {"role": "system", "content": GROUNDED_SYS.format(lang=LANGS.get(lang, "한국어"))},
                    {"role": "user", "content": prompt},
                ],
            })
            r.raise_for_status()
            return r.json().get("message", {}).get("content", "").strip()
    except Exception as e:
        return f"[Ollama 오류: {e}] " + mock_answer(query, lang, hits)


@app.post("/api/draft")
async def draft(req: DraftRequest):
    base = render_draft(req.domain, req.fields, req.today)
    if not base:
        return JSONResponse({"draft": "", "error": "지원하지 않는 서식입니다."}, status_code=400)
    # Ollama가 있으면 자연스럽게 다듬고(한국어 서식 유지) + 사용자 언어 요약 병기
    if OLLAMA_HOST and req.lang != "ko":
        try:
            async with httpx.AsyncClient(timeout=120) as cli:
                r = await cli.post(f"{OLLAMA_HOST}/api/chat", json={
                    "model": GEN_MODEL, "stream": False,
                    "messages": [
                        {"role": "system", "content":
                            "다음 한국어 공식 서류 초안을 그대로 유지하되, 맨 아래에 "
                            f"'--- {LANGS.get(req.lang)} 요약 ---' 구분선과 함께 {LANGS.get(req.lang)}로 "
                            "핵심 내용을 3줄 요약해 덧붙여라. 한국어 본문은 절대 바꾸지 마라."},
                        {"role": "user", "content": base},
                    ],
                })
                r.raise_for_status()
                polished = r.json().get("message", {}).get("content", "").strip()
                if polished:
                    return JSONResponse({"draft": polished, "mode": "ollama"})
        except Exception:
            pass
    return JSONResponse({"draft": base, "mode": "mock"})


@app.get("/api/health")
def health():
    return {
        "ok": True,
        "corpus": len(CORPUS.items),
        "l1": sum(1 for i in CORPUS.items if i["layer"] == "L1"),
        "l2": sum(1 for i in CORPUS.items if i["layer"] == "L2"),
        "mode": "ollama" if OLLAMA_HOST else "mock",
        "gen_model": GEN_MODEL if OLLAMA_HOST else None,
        "langs": LANGS,
    }


@app.post("/api/chat")
async def chat(req: ChatRequest):
    hits = CORPUS.search(req.message, k=4)
    answer = await ollama_generate(req.message, req.lang, hits)
    if answer is None:
        answer = mock_answer(req.message, req.lang, hits)
    citations = [{
        "id": h["id"], "title": h["title"], "layer": h["layer"],
        "snippet": (h["answer"][:200] + ("…" if len(h["answer"]) > 200 else "")),
        "dept": h.get("dept", ""), "phone": h.get("phone", ""),
        "source": h.get("source", ""), "confidence": h.get("confidence", ""),
    } for h in hits]
    return JSONResponse({
        "answer": answer,
        "citations": citations,
        "actions": build_actions(hits),
        "mode": "ollama" if OLLAMA_HOST else "mock",
    })


# 프론트 정적 서빙 (맨 마지막에 마운트)
if WEB_DIR.exists():
    app.mount("/", StaticFiles(directory=str(WEB_DIR), html=True), name="web")
