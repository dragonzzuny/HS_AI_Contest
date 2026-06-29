# -*- coding: utf-8 -*-
"""온톨로지 무결성 검증 — 헛링크·쓰레기·보일러플레이트·끊긴 참조를 자동 차단.

검사 항목:
  1. 모든 legal_basis.id 가 자치법규 코퍼스에 실재하는가
  2. 그 조문이 수집실패(오류)·장제목·목적/정의(보일러플레이트)가 아닌 '실효 조문'인가
  3. 모든 faq_id 가 L1(kb)에 실재하는가
  4. prerequisites / relations 의 도메인 참조가 실재하는가
  5. 각 도메인 필수 메타(label·eligibility·dept) 충족
  6. support_policies 항목이 name·url·desc 를 갖추는가

실행:  python scripts/validate_ontology.py   (이상 있으면 종료코드 1)
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "kb" / "build" / "kb.json"
ORD = ROOT / "kb" / "build" / "ordinances_chunks.json"
ONT = ROOT / "kb" / "build" / "ontology.json"

CHAPTER_RE = re.compile(r"^제\s*\d+\s*장")
BOILER_RE = re.compile(r"^제\s*\d+\s*조\s*\(\s*(목적|정의|용어)")


def is_garbage(s):
    s = (s or "").strip()
    return (not s) or ("일치하는 자치법규가 없" in s) or (s.startswith("{") and '"Law"' in s[:40])


def main():
    kb = {it["id"] for it in json.loads(KB.read_text(encoding="utf-8"))}
    ords = {c["id"]: c for c in json.loads(ORD.read_text(encoding="utf-8"))}
    ont = json.loads(ONT.read_text(encoding="utf-8"))
    domains = ont["domains"]

    errors, warns = [], []
    n_legal = n_pol = 0

    for name, d in domains.items():
        # 5) 필수 메타
        if not d.get("label"):
            errors.append(f"[{name}] label 없음")
        if not d.get("eligibility"):
            warns.append(f"[{name}] eligibility 없음")
        if not d.get("dept"):
            warns.append(f"[{name}] dept 없음")

        # 1~2) 법적근거 무결성
        for lb in d.get("legal_basis", []):
            n_legal += 1
            cid = lb["id"]
            c = ords.get(cid)
            if not c:
                errors.append(f"[{name}] 법적근거 ID 없음(코퍼스 미존재): {cid}")
                continue
            ct = c.get("content", "")
            if is_garbage(ct):
                errors.append(f"[{name}] 법적근거가 수집실패/오류 청크: {cid}")
            elif CHAPTER_RE.match(ct.strip()) or c.get("article") in ("전문", "조문1"):
                errors.append(f"[{name}] 법적근거가 장제목/전문(실효조문 아님): {cid} {c.get('article')}")
            elif BOILER_RE.match(ct.strip()):
                warns.append(f"[{name}] 법적근거가 목적/정의(보일러플레이트): {cid} {c.get('article')}")

        # 3) faq_id 무결성
        for fid in d.get("faq_ids", []):
            if fid not in kb:
                errors.append(f"[{name}] faq_id 없음: {fid}")

        # 4) prerequisites 참조
        for pre in d.get("prerequisites", []):
            if pre not in domains:
                errors.append(f"[{name}] prerequisite 도메인 없음: {pre}")

        # 6) support_policies 형식
        for p in d.get("support_policies", []):
            n_pol += 1
            if not (p.get("name") and p.get("url") and p.get("desc")):
                errors.append(f"[{name}] support_policy 필드 누락: {p.get('name','?')}")

    # 4) relations 참조
    for r in ont.get("relations", []):
        for side in ("from", "to"):
            if r.get(side) not in domains:
                errors.append(f"[relation] {side} 도메인 없음: {r.get(side)}")

    # 리포트
    nat_only = [n for n, d in domains.items() if not d.get("legal_basis")]
    print("=== 온톨로지 무결성 검증 ===")
    print(f"  도메인 {len(domains)} · 법적근거(실효조문) {n_legal} · 지원정책 {n_pol} · 관계 {len(ont.get('relations', []))}")
    print(f"  국가법 영역(자치법규 링크 없음): {', '.join(nat_only) or '없음'}")
    if warns:
        print("\n[경고]")
        for w in warns:
            print("  -", w)
    if errors:
        print("\n[오류]")
        for e in errors:
            print("  -", e)
        print(f"\n❌ 검증 실패 — 오류 {len(errors)}건")
        sys.exit(1)
    print(f"\n✅ 검증 통과 — 오류 0건 (경고 {len(warns)}건)")
    sys.exit(0)


if __name__ == "__main__":
    main()
