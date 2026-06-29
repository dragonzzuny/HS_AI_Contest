# -*- coding: utf-8 -*-
"""kb/ontology.json(원본) → kb/build/ontology.json(해석본)

도메인의 legal_basis_laws(법령명)를 실제 자치법규의 **실효 조문** ID로 해석한다.
- 'article_keywords'로 사용자 질문과 관련된 조문(배출방법·수수료·보육료 등)을 우선 선택.
- '제1조(목적)·제2조(정의)·장 제목·수집실패(오류) 청크'는 제외(보일러플레이트/헛링크 방지).
- 도메인별 FAQ ID·필요서류·담당부서·지원정책도 함께 집계.

실행:  python scripts/build_ontology.py
"""
import json
import re
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB = ROOT / "kb" / "build" / "kb.json"
ORD = ROOT / "kb" / "build" / "ordinances_chunks.json"
SRC = ROOT / "kb" / "ontology.json"
OUT = ROOT / "kb" / "build" / "ontology.json"

CHAPTER_RE = re.compile(r"^제\s*\d+\s*장")        # '제2장 ...' 장 제목
BOILER_RE = re.compile(r"^제\s*\d+\s*조\s*\(\s*(목적|정의|용어)")  # 목적/정의/용어 조(보일러플레이트)


def is_garbage(content: str) -> bool:
    s = (content or "").strip()
    return (not s) or ("일치하는 자치법규가 없" in s) or (s.startswith("{") and '"Law"' in s[:40])


def is_operative(c) -> bool:
    """실효 조문 여부(목적/정의/장제목/오류 제외)."""
    content = (c.get("content") or "").strip()
    art = (c.get("article") or "").strip()
    if is_garbage(content):
        return False
    if CHAPTER_RE.match(content) or art in ("전문", "조문1"):
        return False
    if BOILER_RE.match(content):
        return False
    return True


def select_legal_articles(chunks, keywords, max_n=2):
    """질문 관련 실효 조문을 점수순으로 선택. 없으면 첫 실효조문, 그것도 없으면 빈 리스트."""
    cands = [c for c in chunks if is_operative(c)]
    if not cands:
        return []
    kws = [k for k in (keywords or []) if k]
    scored = []
    for c in cands:
        ct = c.get("content", "")
        score = sum(ct.count(k) for k in kws)
        scored.append((score, c))
    scored.sort(key=lambda x: (-x[0], cands.index(x[1])))
    top = [c for s, c in scored if s > 0][:max_n]
    if not top:                      # 키워드 매칭 0이면 첫 실효조문 1건만(목적/정의 아님)
        top = [cands[0]]
    return top


def main():
    kb = json.loads(KB.read_text(encoding="utf-8"))
    ords = json.loads(ORD.read_text(encoding="utf-8"))
    src = json.loads(SRC.read_text(encoding="utf-8"))

    dom_faqs, dom_docs, dom_dept = defaultdict(list), defaultdict(set), {}
    for it in kb:
        d = it.get("domain", "")
        dom_faqs[d].append(it["id"])
        for x in str(it.get("documents", "")).replace("·", ",").split(","):
            if x.strip():
                dom_docs[d].add(x.strip())
        dom_dept.setdefault(d, {"dept": it.get("dept", ""), "phone": it.get("phone", "")})

    by_law = defaultdict(list)
    for c in ords:
        by_law[c.get("law_name", "")].append(c)

    domains, link_count, skipped = {}, 0, []
    for name, d in src["domains"].items():
        legal = []
        for law in d.get("legal_basis_laws", []):
            chunks = by_law.get(law, [])
            picks = select_legal_articles(chunks, d.get("article_keywords", []))
            if not picks:
                skipped.append(f"{name}/{law}(실효조문 없음·수집실패)")
                continue
            for rep in picks:
                legal.append({
                    "id": rep["id"], "law_name": law, "article": rep.get("article", ""),
                    "content": rep.get("content", "")[:140],
                    "source": rep.get("source", ""),
                    "enforce_date": rep.get("enforce_date", ""),
                })
                link_count += 1
        domains[name] = {
            "label": d.get("label", {}),
            "eligibility": d.get("eligibility", {}),
            "national_law": d.get("national_law"),
            "prerequisites": d.get("prerequisites", []),
            "support_policies": d.get("support_policies", []),
            "faq_ids": dom_faqs.get(name, []),
            "required_docs": sorted(dom_docs.get(name, [])),
            "dept": dom_dept.get(name, {}).get("dept", ""),
            "phone": dom_dept.get(name, {}).get("phone", ""),
            "legal_basis": legal,
        }

    out = {"version": src.get("version", "1.1"), "domains": domains,
           "relations": src.get("relations", [])}
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"온톨로지 빌드 완료 → {OUT}")
    print(f"  도메인 {len(domains)}개 · 법적근거(실효조문) {link_count}건 · 관계 {len(out['relations'])}개")
    for name, dd in domains.items():
        lb = "; ".join(f"{l['article']}" for l in dd["legal_basis"]) or "(국가법 영역 — 링크 없음)"
        pol = len(dd["support_policies"])
        print(f"  - {name:6} FAQ {len(dd['faq_ids'])} · 지원정책 {pol} · 근거조문: {lb}")
    if skipped:
        print("  [제외]", "; ".join(skipped))


if __name__ == "__main__":
    main()
