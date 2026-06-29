# -*- coding: utf-8 -*-
"""화성ON 종합 QC 하네스 — 6개 언어 전수 + 엣지/에러 처리 + 문서생성 + 온톨로지.

실행(서버 5200 기동 상태): PYTHONUTF8=1 python scripts/qc.py
종료코드: 모든 검사 통과 시 0.
"""
import io
import json
import sys
import urllib.request
import urllib.error
import zipfile
import xml.dom.minidom as M

B = "http://127.0.0.1:5200"
LANGS = ["ko", "en", "zh", "vi", "th", "km"]
FAILS = []
N = [0]


def check(name, cond, extra=""):
    N[0] += 1
    if not cond:
        FAILS.append(name + ((" — " + extra) if extra else ""))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}{(' — ' + extra) if extra else ''}")


def post(path, payload):
    return urllib.request.urlopen(urllib.request.Request(
        B + path, data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}), timeout=60)


def chat(m, l="ko"):
    return json.loads(post("/api/chat", {"message": m, "lang": l}).read())


# 도메인 대표 질의(언어별) — 라우팅 기대 prefix
Q = {
    "c-waste": {"ko": "쓰레기 어떻게 버려요?", "en": "How do I throw out trash?", "zh": "垃圾怎么扔?",
                "vi": "Vứt rác thế nào?", "th": "ทิ้งขยะอย่างไร?", "km": "តើបោះសំរាមយ៉ាងណា?"},
    "c-labor": {"ko": "월급을 못 받았어요", "en": "I wasn't paid my wages", "zh": "老板没发工资",
                "vi": "Tôi chưa được trả lương", "th": "ยังไม่ได้รับเงินเดือน", "km": "ខ្ញុំមិនបានទទួលប្រាក់ឈ្នួល"},
    "c-stay": {"ko": "외국인등록 어떻게 해요?", "en": "How do I register as a foreigner?", "zh": "如何办理外国人登录?",
               "vi": "Đăng ký người nước ngoài thế nào?", "th": "ลงทะเบียนคนต่างชาติอย่างไร?", "km": "តើខ្ញុំចុះឈ្មោះជនបរទេសយ៉ាងដូចម្ដេច?"},
    "c-health": {"ko": "건강보험 가입", "en": "How do I join health insurance?", "zh": "如何加入健康保险?",
                 "vi": "Đăng ký bảo hiểm y tế thế nào?", "th": "สมัครประกันสุขภาพอย่างไร?", "km": "តើចូលរួមធានារ៉ាប់រងសុខភាពយ៉ាងណា?"},
}
OOS = {"ko": "비트코인 시세 알려줘", "en": "What's the weather today?", "zh": "推荐一部电影",
       "vi": "Giá vàng hôm nay?", "th": "วันนี้อากาศเป็นอย่างไร", "km": "តម្លៃមាសថ្ងៃនេះ"}
# 온톨로지 info 라벨(언어별 첫 단어)
INFO_LABEL = {"ko": "대상", "en": "Eligibility", "zh": "对象", "vi": "Đối tượng", "th": "ผู้มีสิทธิ์", "km": "អ្នកមានសិទ្ធិ"}


def main():
    print("■ A. 6개 언어 × 도메인 라우팅·근거")
    for exp, langs in Q.items():
        for l in LANGS:
            if l not in langs:
                continue
            d = chat(langs[l], l)
            ids = [c["id"] for c in d.get("citations", [])]
            check(f"{l}/{exp} 라우팅+근거", d.get("grounded") and any(i.startswith(exp) for i in ids),
                  f"top={ids[0] if ids else '-'}")

    print("\n■ B. 6개 언어 환각 거부(범위 밖)")
    for l in LANGS:
        d = chat(OOS[l], l)
        check(f"{l} OOS 안전거부", d.get("refused") is True and not d.get("citations"))

    print("\n■ C. 온톨로지 보강(법적근거/정책/자격) + 현지화")
    for l in LANGS:
        d = chat(Q["c-labor"][l], l)
        legal = [c for c in d["citations"] if c.get("kind") == "법적근거"]
        pol = [a for a in d["actions"] if a["type"] == "policy"]
        info = [a for a in d["actions"] if a["type"] == "info"]
        check(f"{l} 노무 법적근거(실효조문)", len(legal) > 0)
        check(f"{l} 노무 지원정책", len(pol) > 0)
        # 현지화: ko/en은 info 라벨 언어 확인
        if l in ("ko", "en") and info:
            txt = " ".join(info[0]["items"])
            check(f"{l} 자격안내 현지화", INFO_LABEL[l] in txt, txt[:40])

    print("\n■ D. 엣지/에러 처리")
    # 빈 입력 / 공백 / 특수문자 / 초장문 / 미지원 언어
    check("빈 메시지 → 거부", chat("", "ko").get("refused") is True)
    check("공백 메시지 → 거부", chat("   ", "ko").get("refused") is True)
    xss = chat('<script>alert(1)</script> & "test" 쓰레기', "ko")
    check("특수문자 입력 처리(쓰레기 라우팅)", xss.get("grounded") and any(c["id"].startswith("c-waste") for c in xss["citations"]))
    check("초장문 입력 처리", isinstance(chat("쓰레기 " * 500, "ko"), dict))
    check("미지원 언어코드(fallback)", isinstance(chat("쓰레기 어떻게 버려요?", "xx"), dict))
    # draft 에러 경로
    try:
        post("/api/draft", {"domain": "없는도메인", "fields": {}})
        check("잘못된 도메인 draft → 400", False)
    except urllib.error.HTTPError as e:
        check("잘못된 도메인 draft → 400", e.code == 400)
    # draft 정상(미입력 필드 허용)
    dr = json.loads(post("/api/draft", {"domain": "노무", "fields": {}, "lang": "ko"}).read())
    check("draft 미입력 필드 허용(미입력 표기)", "진 정 서" in dr.get("draft", ""))

    print("\n■ E. 문서 생성(HWPX/DOCX/TXT) — 폼 도메인")
    flds = {"name": "<홍&길동>", "amount": "3200000", "company": "○○산업(주)", "period": "2026-03~05"}
    for dom in ["노무", "폐기물"]:
        # HWPX
        h = post("/api/draft/hwpx", {"domain": dom, "fields": flds, "lang": "ko"})
        hb = h.read()
        z = zipfile.ZipFile(io.BytesIO(hb))
        xmlok = True
        for n2 in z.namelist():
            if n2.endswith(".xml"):
                try:
                    M.parseString(z.read(n2))
                except Exception:
                    xmlok = False
        i0 = z.infolist()[0]
        check(f"{dom} HWPX 유효(zip·mimetype·XML, 특수문자 안전)",
              h.headers.get("content-type") == "application/hwp+zip" and i0.filename == "mimetype"
              and i0.compress_type == zipfile.ZIP_STORED and xmlok)
        # DOCX
        dx = post("/api/draft/docx", {"domain": dom, "fields": flds, "lang": "ko"})
        check(f"{dom} DOCX 유효", dx.headers.get("content-type").endswith("wordprocessingml.document") and len(dx.read()) > 4000)

    print("\n■ F. 카탈로그/서식 노출")
    d = chat(Q["c-labor"]["ko"], "ko")
    cat = [a for a in d["actions"] if a["type"] == "link" and "공식 서식" in a.get("label", "")]
    check("노무 공식 서식 카탈로그 노출", len(cat) > 0)

    print(f"\n=== QC 종합: {N[0]-len(FAILS)}/{N[0]} PASS ===")
    if FAILS:
        print("실패 항목:")
        for f in FAILS:
            print("  -", f)
        sys.exit(1)
    print("✅ 전 항목 통과")


if __name__ == "__main__":
    main()
