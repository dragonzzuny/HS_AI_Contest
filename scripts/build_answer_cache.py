# -*- coding: utf-8 -*-
"""자주 묻는 질문 답변을 미리 생성해 캐시에 저장(언어별) → 배포 시 즉시 응답.

L1 FAQ(온톨로지 토픽) 각각에 대해 6개 언어 그라운딩 답변을 LLM으로 1회 생성하여
kb/build/answer_cache.json 에 저장한다. 이 파일을 커밋하면 GPU 없는 서버에서도
흔한 질문은 6개 언어 즉시 응답(롱테일만 런타임 LLM).

사용(Ollama 필요):
  set OLLAMA_HOST=http://localhost:11434  (PowerShell: $env:OLLAMA_HOST=...)
  set GEN_MODEL=gemma3:4b
  python scripts/build_answer_cache.py --langs en,zh,vi,th,km [--limit 5] [--overwrite]
GPU 머신에서 돌리면 빠릅니다(CPU는 답변당 수십초~분).
"""
import argparse
import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

if not os.environ.get("OLLAMA_HOST"):
    print("OLLAMA_HOST 미설정 — LLM이 필요합니다. 예) set OLLAMA_HOST=http://localhost:11434")
    sys.exit(1)

from backend import app  # noqa: E402  (env 설정 후 import)


def to_hit(it):
    return {
        "id": it["id"], "layer": "L1", "title": it.get("title", ""),
        "domain": it.get("domain", ""), "answer": it.get("answer", ""),
        "target": it.get("target", ""), "documents": it.get("documents", ""),
        "dept": it.get("dept", ""), "phone": it.get("phone", ""),
        "location": it.get("location", ""), "source": it.get("source", ""),
        "confidence": (it.get("confidence", "") or "").split()[0],
        "questions": it.get("questions", []),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--langs", default="en,zh,vi,th,km")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    langs = [x.strip() for x in args.langs.split(",") if x.strip()]

    kb = json.loads(app.KB_JSON.read_text(encoding="utf-8"))
    if args.limit:
        kb = kb[: args.limit]

    total = len(kb) * len(langs)
    done = 0
    for it in kb:
        hit = to_hit(it)
        query = (it.get("questions") or [it.get("title", "")])[0]
        for lang in langs:
            done += 1
            if not args.overwrite and app._cache_get(it["id"], lang):
                print(f"  [{done}/{total}] skip {it['id']}/{lang} (이미 있음)")
                continue
            ans = None
            for attempt in range(2):        # 지명 환각 시 1회 재생성
                cand = asyncio.run(app.ollama_generate(query, lang, [hit]))
                if cand and "[Ollama 오류" not in cand and app.answer_geo_ok(cand, [hit]):
                    ans = cand
                    break
            if ans:
                app._cache_put(it["id"], lang, ans)
                print(f"  [{done}/{total}] OK {it['id']}/{lang} ({len(ans)}자)")
            else:
                print(f"  [{done}/{total}] SKIP {it['id']}/{lang} (생성실패/지명환각)")

    n = sum(len(v) for v in app.ANSWER_CACHE.values())
    print(f"\n캐시 항목 {n}개 저장 → {app.CACHE_JSON}")


if __name__ == "__main__":
    main()
