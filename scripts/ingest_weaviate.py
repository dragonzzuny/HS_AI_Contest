#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
L1(정제 FAQ) + L2(자치법규 조문) 코퍼스를 BGE-M3로 임베딩하여 Weaviate에 적재.

전제:
  - docker compose -f docker-compose.weaviate.yml up -d  (Weaviate 가동, localhost:8080)
  - pip install -r requirements.txt
  - python scripts/build_kb.py           (kb/build/kb.json 생성 — 완료됨)
  - python scripts/collect_ordinances.py (kb/build/ordinances_chunks.json 생성 — OC 키 필요)
실행:
  python scripts/ingest_weaviate.py
설계:
  단일 컬렉션 KbChunk. content는 BM25 인덱싱(키워드) + BGE-M3 벡터 → Weaviate 하이브리드 검색.
  layer 속성(L1/L2)으로 답변 우선순위(정제 FAQ 우선) 제어. 멱등 upsert(uuid5).
"""
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
KB_JSON = ROOT / "kb" / "build" / "kb.json"
ORD_JSON = ROOT / "kb" / "build" / "ordinances_chunks.json"

NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # 고정 네임스페이스(멱등)


def load_records():
    recs = []
    # L1: 정제 FAQ
    if KB_JSON.exists():
        for it in json.loads(KB_JSON.read_text(encoding="utf-8")):
            recs.append({
                "chunk_id": it["id"],
                "layer": "L1",
                "title": it.get("title", ""),
                "domain": it.get("domain", ""),
                "content": it.get("content", "") or it.get("answer", ""),
                "answer": it.get("answer", ""),
                "dept": it.get("dept", ""),
                "phone": it.get("phone", ""),
                "source": it.get("source", ""),
                "confidence": (it.get("confidence", "") or "").split()[0],
            })
    else:
        print(f"[경고] {KB_JSON} 없음 — build_kb.py 먼저 실행", file=sys.stderr)
    # L2: 자치법규 조문
    if ORD_JSON.exists():
        for c in json.loads(ORD_JSON.read_text(encoding="utf-8")):
            recs.append({
                "chunk_id": c["id"],
                "layer": "L2",
                "title": f"{c.get('law_name','')} {c.get('article','')}",
                "domain": "법령",
                "content": c.get("content", ""),
                "answer": "",
                "dept": c.get("kind", ""),
                "phone": "",
                "source": c.get("source", ""),
                "confidence": "확인됨",
            })
    else:
        print(f"[안내] {ORD_JSON} 없음 — 자치법규(L2)는 collect_ordinances.py 실행 후 적재됨", file=sys.stderr)
    return recs


def main():
    recs = load_records()
    if not recs:
        print("[ERROR] 적재할 레코드가 없습니다.", file=sys.stderr)
        return 2
    print(f"[1/3] 코퍼스 {len(recs)}건 로드 (L1+L2)")

    try:
        from sentence_transformers import SentenceTransformer
        import weaviate
        from weaviate.classes.config import Configure, Property, DataType
        from weaviate.classes.data import DataObject
    except ImportError as e:
        print(f"[ERROR] 의존성 누락: {e}\n  pip install -r requirements.txt", file=sys.stderr)
        return 2

    print("[2/3] BGE-M3 임베딩 (최초 실행 시 모델 다운로드)")
    model = SentenceTransformer("BAAI/bge-m3")
    texts = [r["content"] for r in recs]
    vectors = model.encode(texts, normalize_embeddings=True, show_progress_bar=True)

    print("[3/3] Weaviate 적재")
    client = weaviate.connect_to_local()
    try:
        name = "KbChunk"
        if not client.collections.exists(name):
            client.collections.create(
                name=name,
                vectorizer_config=Configure.Vectorizer.none(),  # BYO 벡터
                properties=[
                    Property(name="chunk_id", data_type=DataType.TEXT),
                    Property(name="layer", data_type=DataType.TEXT),
                    Property(name="title", data_type=DataType.TEXT),
                    Property(name="domain", data_type=DataType.TEXT),
                    Property(name="content", data_type=DataType.TEXT),
                    Property(name="answer", data_type=DataType.TEXT),
                    Property(name="dept", data_type=DataType.TEXT),
                    Property(name="phone", data_type=DataType.TEXT),
                    Property(name="source", data_type=DataType.TEXT),
                    Property(name="confidence", data_type=DataType.TEXT),
                ],
            )
            print(f"      컬렉션 '{name}' 생성")
        coll = client.collections.get(name)
        objs = []
        for r, v in zip(recs, vectors):
            objs.append(DataObject(
                properties=r,
                vector=v.tolist(),
                uuid=uuid.uuid5(NAMESPACE, r["chunk_id"]),  # 멱등 upsert
            ))
        coll.data.insert_many(objs)
        cnt = coll.aggregate.over_all(total_count=True).total_count
        print(f"      적재 완료. 컬렉션 총 {cnt}건")
    finally:
        client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
