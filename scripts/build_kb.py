#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
KB markdown(kb/0*.md) -> 정규화 JSON(kb/build/kb.json) 변환·검증기.

앱/DB/임베딩이 공통으로 소비하는 단일 정규화 산출물을 만든다.
API 키 불필요. 실행: python scripts/build_kb.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB_DIR = ROOT / "kb"
OUT_DIR = KB_DIR / "build"
OUT_FILE = OUT_DIR / "kb.json"

# 한국어 필드 라벨 -> JSON 키
FIELD_MAP = {
    "분야": "domain",
    "대상": "target",
    "질문예시": "questions",
    "답변요지(한국어)": "answer",
    "필요서류": "documents",
    "담당기관/부서": "dept",
    "연락처": "phone",
    "위치/방문": "location",
    "출처": "source",
    "신뢰도": "confidence",
}

# "### [c-stay-01] 외국인등록증 발급"
HEADER_RE = re.compile(r"^###\s*\[(?P<id>[a-z0-9\-]+)\]\s*(?P<title>.+?)\s*$")
# "- 분야: 체류"
FIELD_RE = re.compile(r"^-\s*(?P<label>[^:：]+?)\s*[:：]\s*(?P<value>.*)$")


def parse_file(path: Path):
    items = []
    cur = None
    domain_file = path.stem  # 01_stay -> 01_stay
    for lineno, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = raw.rstrip()
        m = HEADER_RE.match(line)
        if m:
            if cur:
                items.append(cur)
            cur = {
                "id": m.group("id"),
                "title": m.group("title"),
                "_file": path.name,
                "_line": lineno,
            }
            continue
        if cur is None:
            continue
        fm = FIELD_RE.match(line)
        if fm:
            label = fm.group("label").strip()
            value = fm.group("value").strip()
            key = FIELD_MAP.get(label)
            if key:
                cur[key] = value
    if cur:
        items.append(cur)
    return items


def split_questions(q: str):
    # "한국어 질문" / "English question" -> [ko, en]
    if not q:
        return []
    parts = [p.strip().strip('"').strip() for p in q.split("/")]
    return [p for p in parts if p]


def main():
    if not KB_DIR.exists():
        print(f"[ERROR] KB 디렉터리 없음: {KB_DIR}", file=sys.stderr)
        return 2

    files = sorted(KB_DIR.glob("0*.md"))
    if not files:
        print(f"[ERROR] kb/0*.md 파일이 없음", file=sys.stderr)
        return 2

    all_items = []
    errors = []
    REQUIRED = ["domain", "answer", "source", "confidence"]

    for f in files:
        items = parse_file(f)
        for it in items:
            it["questions"] = split_questions(it.get("questions", ""))
            # 인용용 검색 본문: 제목+대상+답변+서류 결합
            it["content"] = " ".join(
                x for x in [
                    it.get("title", ""),
                    it.get("target", ""),
                    it.get("answer", ""),
                    it.get("documents", ""),
                ] if x
            )
            missing = [r for r in REQUIRED if not it.get(r)]
            if missing:
                errors.append(f"{it['_file']}:{it['_line']} [{it['id']}] 필수필드 누락: {missing}")
        all_items.extend(items)

    # ID 중복 검사
    seen = {}
    for it in all_items:
        if it["id"] in seen:
            errors.append(f"중복 ID: {it['id']} ({it['_file']} & {seen[it['id']]})")
        seen[it["id"]] = it["_file"]

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(
        json.dumps(all_items, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # 통계
    by_domain = {}
    by_conf = {}
    for it in all_items:
        by_domain[it.get("domain", "?")] = by_domain.get(it.get("domain", "?"), 0) + 1
        c = it.get("confidence", "?").split()[0] if it.get("confidence") else "?"
        by_conf[c] = by_conf.get(c, 0) + 1

    print(f"[OK] 항목 {len(all_items)}개 -> {OUT_FILE.relative_to(ROOT)}")
    print(f"  분야별: {by_domain}")
    print(f"  신뢰도별: {by_conf}")
    if errors:
        print(f"\n[경고] {len(errors)}건:")
        for e in errors:
            print("  - " + e)
        return 1
    print("  검증 통과 (필수필드/중복 ID 이상 없음)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
