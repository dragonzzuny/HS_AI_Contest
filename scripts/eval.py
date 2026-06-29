# -*- coding: utf-8 -*-
"""화성ON 평가 하네스 — 라우팅 정확도 · 인용 무결성 · 환각(헛소리) 거부율 측정.

목적: "근거 있는 질문은 정확히, 근거 없는 질문은 단정하지 않고 안전 거부"를 정량 검증.

실행(서버가 5200에 떠 있어야 함):
  PYTHONUTF8=1 python scripts/eval.py
  PYTHONUTF8=1 python scripts/eval.py --json   # 기계판독용 결과
종료코드: 모든 지표가 기준치 이상이면 0, 아니면 1 (CI 게이트용).
"""
import argparse
import json
import sys
import urllib.request

URL = "http://127.0.0.1:5200/api/chat"

# ── 1) 정상 질의: (언어, 질문, 기대 도메인 prefix) ────────────────
# 6개 언어 × 8개 도메인 교차언어 라우팅 검증.
POSITIVE = [
    # 폐기물
    ("ko", "쓰레기는 어떻게 버려요?", "c-waste"),
    ("en", "How do I throw out trash?", "c-waste"),
    ("zh", "垃圾怎么扔?", "c-waste"),
    ("vi", "Vứt rác thế nào?", "c-waste"),
    ("th", "ทิ้งขยะอย่างไร?", "c-waste"),
    ("km", "តើបោះសំរាមយ៉ាងណា?", "c-waste"),
    # 체류
    ("ko", "외국인등록 어떻게 해요?", "c-stay"),
    ("en", "How do I register as a foreigner?", "c-stay"),
    ("zh", "如何办理外国人登录?", "c-stay"),
    ("vi", "Đăng ký người nước ngoài thế nào?", "c-stay"),
    ("th", "ลงทะเบียนคนต่างชาติอย่างไร?", "c-stay"),
    ("km", "តើខ្ញុំចុះឈ្មោះជនបរទេសយ៉ាងដូចម្ដេច?", "c-stay"),
    # 노무
    ("ko", "월급을 못 받았어요", "c-labor"),
    ("en", "I wasn't paid my wages", "c-labor"),
    ("vi", "Tôi chưa được trả lương", "c-labor"),
    ("zh", "老板没发工资", "c-labor"),
    # 건강보험
    ("ko", "건강보험 어떻게 가입해요?", "c-health"),
    ("en", "How do I join health insurance?", "c-health"),
    ("vi", "Đăng ký bảo hiểm y tế thế nào?", "c-health"),
    # 보육교육
    ("ko", "아이 어린이집 신청하고 싶어요", "c-edu"),
    ("en", "I want to apply for daycare", "c-edu"),
    # 운전면허
    ("ko", "외국인 운전면허 어떻게 따요?", "c-license"),
    ("en", "How can a foreigner get a driver's license?", "c-license"),
    # 행정
    ("ko", "전입신고 어떻게 해요?", "c-admin"),
    # 지원기관
    ("ko", "외국인 상담은 어디서 받아요?", "c-support"),
    ("en", "Where can I get counseling for foreigners?", "c-support"),
]

# ── 2) 범위 밖 질의: 근거가 없으므로 '안전 거부'해야 함 ──────────────
# 답을 지어내면(=grounded 주장) 환각. refused=True 여야 통과.
OUT_OF_SCOPE = [
    ("ko", "오늘 비트코인 시세 알려줘"),
    ("ko", "근처 맛집 추천해줘"),
    ("ko", "삼성전자 주가 어때?"),
    ("en", "What's the weather today?"),
    ("en", "Tell me a joke"),
    ("en", "Who won the World Cup in 2022?"),
    ("vi", "Giá vàng hôm nay bao nhiêu?"),
    ("zh", "推荐一部电影"),
]


def ask(lang, msg):
    body = json.dumps({"message": msg, "lang": lang}).encode()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()

    rows = []
    # 정상 질의
    pos_top1 = pos_topk = pos_cited = 0
    bad_cites = 0
    for lang, msg, exp in POSITIVE:
        d = ask(lang, msg)
        cites = d.get("citations", [])
        ids = [c["id"] for c in cites]
        idset = set(ids)
        top1 = bool(ids) and ids[0].startswith(exp)
        topk = any(i.startswith(exp) for i in ids)
        cited = len(cites) > 0 and not d.get("refused", False)
        # 인용 무결성: 답변 본문이 인용한 [id]가 실제 근거 목록에 존재하는가
        answer = d.get("answer", "")
        import re
        used = re.findall(r"\[([a-z]+-[a-z]+-\d+|ord-[\w-]+)\]", answer)
        fabricated = [u for u in used if u not in idset]
        if fabricated:
            bad_cites += 1
        pos_top1 += top1; pos_topk += topk; pos_cited += cited
        rows.append({"kind": "pos", "lang": lang, "exp": exp, "top": ids[0] if ids else "—",
                     "top1": top1, "topk": topk, "cited": cited, "fabricated": fabricated, "q": msg})

    # 범위 밖 질의
    oos_refused = 0
    for lang, msg in OUT_OF_SCOPE:
        d = ask(lang, msg)
        refused = bool(d.get("refused", False))
        oos_refused += refused
        rows.append({"kind": "oos", "lang": lang, "refused": refused,
                     "top": (d.get("citations") or [{}])[0].get("id", "—"), "q": msg})

    nP, nO = len(POSITIVE), len(OUT_OF_SCOPE)
    metrics = {
        "routing_top1": pos_top1 / nP,
        "routing_topk": pos_topk / nP,
        "citation_rate": pos_cited / nP,
        "citation_integrity": 1 - (bad_cites / nP),   # 지어낸 인용 없음 비율
        "oos_refusal": oos_refused / nO,              # 환각 거부율(높을수록 안전)
    }
    # 합격 기준(제품화 게이트)
    GATES = {"routing_top1": 0.90, "routing_topk": 0.95, "citation_rate": 0.98,
             "citation_integrity": 1.0, "oos_refusal": 0.90}
    passed = all(metrics[k] >= GATES[k] for k in GATES)

    if args.json:
        print(json.dumps({"metrics": metrics, "gates": GATES, "passed": passed, "rows": rows},
                         ensure_ascii=False, indent=2))
        sys.exit(0 if passed else 1)

    print("\n=== 정상 질의 (라우팅·인용) ===")
    print(f"{'lang':4} {'expect':10} {'top hit':13} top1 topk cite  q")
    print("-" * 78)
    for r in rows:
        if r["kind"] != "pos":
            continue
        flag = " ⚠FAB" if r["fabricated"] else ""
        print(f"{r['lang']:4} {r['exp']:10} {r['top']:13} "
              f"{'✓' if r['top1'] else '·'}    {'✓' if r['topk'] else '·'}    "
              f"{'✓' if r['cited'] else '✗'}   {r['q'][:30]}{flag}")

    print("\n=== 범위 밖 질의 (환각 거부 — refused=✓ 여야 안전) ===")
    print(f"{'lang':4} {'refused':8} {'top':13} q")
    print("-" * 70)
    for r in rows:
        if r["kind"] != "oos":
            continue
        print(f"{r['lang']:4} {'✓ 거부' if r['refused'] else '✗ 답변(위험)':8} {r['top']:13} {r['q'][:34]}")

    print("\n=== 지표 ===")
    for k, v in metrics.items():
        mark = "PASS" if v >= GATES[k] else "FAIL"
        print(f"  {k:20} {v*100:5.1f}%   (기준 {GATES[k]*100:.0f}%)  [{mark}]")
    print(f"\n총평: {'✅ 제품화 게이트 통과' if passed else '❌ 기준 미달 — 가드레일 보강 필요'}")
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
