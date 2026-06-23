#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
화성시 자치법규(조례·규칙) 전수 수집기 — 법제처 국가법령정보 Open API.

목록조회(target=ordin) -> 화성시 필터 -> 본문조회 -> 정규화 JSON 저장 -> 조문 단위 청킹(Weaviate 적재용).

사전 준비:
  1) https://open.law.go.kr 회원가입 후 OPEN API 신청 (무료)
  2) 발급된 OC 값(보통 가입 이메일의 ID 부분)을 환경변수로 설정
       (PowerShell)  $env:LAW_OC = "your_oc"
       (bash)        export LAW_OC=your_oc
실행:
  python scripts/collect_ordinances.py
산출물:
  data/ordinances/raw/{자치법규ID}.json   원본 본문
  data/ordinances/index.json               목록 메타
  kb/build/ordinances_chunks.json          조문 단위 청크(L2 코퍼스, Weaviate 적재 입력)
"""
import json
import os
import re
import sys
import time
from pathlib import Path

try:
    import requests
except ImportError:
    print("[ERROR] requests 필요: pip install requests", file=sys.stderr)
    sys.exit(2)

ROOT = Path(__file__).resolve().parent.parent
RAW_DIR = ROOT / "data" / "ordinances" / "raw"
INDEX_FILE = ROOT / "data" / "ordinances" / "index.json"
CHUNKS_FILE = ROOT / "kb" / "build" / "ordinances_chunks.json"

SEARCH_URL = "http://www.law.go.kr/DRF/lawSearch.do"
SERVICE_URL = "http://www.law.go.kr/DRF/lawService.do"

OC = os.environ.get("LAW_OC", "").strip()
# 화성시는 경기도 소속. org=시도, sborg=시군구 코드. 코드 불확실 시 query+이름필터로 안전 수집.
ORG = os.environ.get("LAW_ORG", "").strip()       # 예: 경기도 코드 (선택)
SBORG = os.environ.get("LAW_SBORG", "").strip()   # 예: 화성시 코드 (선택)
QUERY = os.environ.get("LAW_QUERY", "화성시").strip()
NAME_FILTER = "화성"   # 지자체기관명에 이 문자열이 포함된 것만 채택


def _get(url, params, retries=3):
    params = {**params, "OC": OC, "type": "JSON"}
    for i in range(retries):
        try:
            r = requests.get(url, params=params, timeout=30)
            r.raise_for_status()
            return r.json()
        except Exception as e:
            if i == retries - 1:
                print(f"[WARN] 요청 실패({url}): {e}", file=sys.stderr)
                return None
            time.sleep(1.5 * (i + 1))
    return None


def _find_list(obj, keys=("ordin", "law", "List")):
    """응답 JSON에서 결과 리스트를 방어적으로 탐색."""
    if isinstance(obj, list):
        return obj
    if not isinstance(obj, dict):
        return []
    # 1단계: 루트 컨테이너(OrdinSearch 등) 안으로
    for v in obj.values():
        if isinstance(v, dict):
            for k, vv in v.items():
                if any(key.lower() in k.lower() for key in keys) and isinstance(vv, (list, dict)):
                    return vv if isinstance(vv, list) else [vv]
        if isinstance(v, list):
            return v
    return []


def _g(d, *names):
    """여러 후보 키 중 먼저 매칭되는 값."""
    if not isinstance(d, dict):
        return ""
    for n in names:
        for k, v in d.items():
            if n.replace(" ", "") in str(k).replace(" ", ""):
                return v
    return ""


def collect_list():
    items, page = [], 1
    while True:
        params = {"target": "ordin", "query": QUERY, "display": 100, "page": page}
        if ORG:
            params["org"] = ORG
        if SBORG:
            params["sborg"] = SBORG
        data = _get(SEARCH_URL, params)
        if not data:
            break
        rows = _find_list(data)
        if not rows:
            break
        for row in rows:
            org_name = str(_g(row, "지자체기관명", "기관명"))
            if NAME_FILTER and NAME_FILTER not in org_name:
                continue
            items.append({
                "id": str(_g(row, "자치법규일련번호", "자치법규ID", "ID")),
                "name": str(_g(row, "자치법규명", "법령명")),
                "kind": str(_g(row, "자치법규종류", "종류")),
                "org": org_name,
                "enforce_date": str(_g(row, "시행일자")),
                "promulgate_date": str(_g(row, "공포일자")),
                "link": str(_g(row, "자치법규상세링크", "상세링크")),
            })
        print(f"  목록 page {page}: 누적 {len(items)}건")
        if len(rows) < 100:
            break
        page += 1
        time.sleep(0.5)
    return items


def collect_body(law_id):
    out = RAW_DIR / f"{law_id}.json"
    if out.exists():  # 멱등성
        return json.loads(out.read_text(encoding="utf-8"))
    data = _get(SERVICE_URL, {"target": "ordin", "MST": law_id})
    if not data:
        return None
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    time.sleep(0.4)
    return data


def extract_articles(body, meta):
    """본문 JSON(LawService.조문.조)에서 조문 텍스트를 추출해 조문 단위 청크로."""
    chunks = []
    ls = body.get("LawService") if isinstance(body, dict) else None
    ls = ls if isinstance(ls, dict) else (body if isinstance(body, dict) else {})
    # 공개 검색 링크(OC 키 노출 금지 — 공고 유의사항 준수)
    from urllib.parse import quote
    src = f"https://www.law.go.kr/LSW/lsAstSc.do?menuId=1&query={quote(meta['name'])}"

    jomun = ls.get("조문") or {}
    jo = jomun.get("조") if isinstance(jomun, dict) else None
    if isinstance(jo, dict):
        jo = [jo]
    if isinstance(jo, list):
        for i, a in enumerate(jo, 1):
            if not isinstance(a, dict):
                continue
            # 인코딩/키명 무관: 가장 긴 문자열 값 = 조문 본문
            content = ""
            for v in a.values():
                if isinstance(v, str) and len(v) > len(content):
                    content = v
            content = re.sub(r"\s+", " ", content).strip()
            if len(content) < 5:
                continue
            m = re.match(r"(제\s*\d+\s*조(?:의\s*\d+)?)", content)
            label = m.group(1).replace(" ", "") if m else f"조문{i}"
            chunks.append({
                "id": f"ord-{meta['id']}-{i}",
                "law_id": meta["id"],
                "law_name": meta["name"],
                "kind": meta["kind"],
                "article": label,
                "content": content[:2000],
                "enforce_date": meta["enforce_date"],
                "source": f"[{meta['name']} {label}]({src})",
                "lang": "ko",
            })

    if not chunks:  # 조문 파싱 실패 시 폴백(별표/부칙만 있는 경우 등)
        flat = re.sub(r"\s+", " ", json.dumps(ls, ensure_ascii=False))
        chunks.append({
            "id": f"ord-{meta['id']}-full", "law_id": meta["id"],
            "law_name": meta["name"], "kind": meta["kind"], "article": "전문",
            "content": flat[:2000], "enforce_date": meta["enforce_date"],
            "source": f"[{meta['name']}]({src})", "lang": "ko",
        })
    return chunks


def main():
    if not OC:
        print("[안내] 환경변수 LAW_OC 가 없습니다.\n"
              "  1) https://open.law.go.kr 가입 → OPEN API 신청(무료)\n"
              "  2) PowerShell:  $env:LAW_OC = \"발급받은OC\"  설정 후 재실행\n"
              "  (테스트 없이 스크립트 구조만 확인하려면 LAW_OC=dummy 로 실행 가능 — 단 데이터는 안 받아짐)",
              file=sys.stderr)
        return 2

    print(f"[1/3] 자치법규 목록 조회 (query='{QUERY}', filter='{NAME_FILTER}')")
    items = collect_list()
    if not items:
        print("[경고] 수집된 목록이 없습니다. OC 값/네트워크/파라미터를 확인하세요.", file=sys.stderr)
        return 1
    INDEX_FILE.parent.mkdir(parents=True, exist_ok=True)
    INDEX_FILE.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"      목록 {len(items)}건 -> {INDEX_FILE.relative_to(ROOT)}")

    print(f"[2/3] 본문 조회 + 조문 청킹")
    all_chunks = []
    for i, m in enumerate(items, 1):
        body = collect_body(m["id"])
        if body:
            all_chunks.extend(extract_articles(body, m))
        if i % 20 == 0:
            print(f"      {i}/{len(items)} 처리, 청크 {len(all_chunks)}")

    CHUNKS_FILE.parent.mkdir(parents=True, exist_ok=True)
    CHUNKS_FILE.write_text(json.dumps(all_chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[3/3] 조문 청크 {len(all_chunks)}개 -> {CHUNKS_FILE.relative_to(ROOT)}")
    print(f"      법령 {len(items)}건 / 평균 {len(all_chunks)/max(len(items),1):.1f} 청크")
    return 0


if __name__ == "__main__":
    sys.exit(main())
