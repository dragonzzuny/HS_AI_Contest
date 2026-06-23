# 화성ON DB 설계 (Supabase / Postgres + pgvector)

> KB markdown(`_SCHEMA.md`) → 청크 → 임베딩 → 아래 테이블에 적재.
> 무료 티어, Vercel 연동, 관계형+벡터 한 곳. 심사 "계속성·확장성" 근거.

## 확장
```sql
create extension if not exists vector;
```

## 테이블

### departments — 담당부서/연락처 (구조화 필터·라우팅용)
```sql
create table departments (
  id          bigserial primary key,
  name        text not null,          -- 예: 화성시 여성다문화과 외국인주민지원팀
  org         text,                   -- 상위기관 (화성시 / 수원출입국 / 건강보험공단 등)
  phone       text,
  address     text,
  hours       text,                   -- 운영시간
  url         text,
  languages   text[],                 -- 통번역 가능 언어
  updated_at  timestamptz default now()
);
```

### minwon — 민원 항목(메타)
```sql
create table minwon (
  id          text primary key,       -- c-stay-01 등 청크ID 접두 일치
  title       text not null,
  domain      text not null,          -- stay/labor/health/waste/edu/license/admin/support
  target      text,                   -- 대상(예: 90일 이상 체류 외국인)
  dept_id     bigint references departments(id),
  source_url  text,
  source_name text,
  confidence  text default 'TODO검증',-- 확인됨/부분확인/TODO검증
  checked_at  date,
  updated_at  timestamptz default now()
);
```

### chunks — RAG 검색 단위 (인용 추적의 핵심)
```sql
create table chunks (
  id          text primary key,       -- c-stay-01, c-stay-01-2 ...
  minwon_id   text references minwon(id) on delete cascade,
  lang        text default 'ko',      -- 원문 언어(근거는 ko 유지)
  content     text not null,          -- 청크 본문(답변 근거 원문)
  embedding   vector(1536),           -- 임베딩 차원은 모델에 맞춰 조정
  token_count int
);
create index on chunks using ivfflat (embedding vector_cosine_ops);
```

## 검색 쿼리 (RAG)
```sql
-- 질문 임베딩 q 와 코사인 유사도 top-k
select c.id, c.content, m.title, m.source_url, m.source_name,
       d.name as dept, d.phone, d.url as dept_url,
       1 - (c.embedding <=> :q) as score
from chunks c
join minwon m on m.id = c.minwon_id
left join departments d on d.id = m.dept_id
order by c.embedding <=> :q
limit :k;
```
→ 반환된 `c.id`가 답변 인라인 인용칩(`[c-stay-01]`)과 연결, 클릭 시 원문+출처+부서 표시.

## 적재 파이프라인 (빌드 스크립트)
1. `kb/*.md` 파싱 → 항목별 필드 추출
2. departments/minwon upsert
3. content 청킹 → 임베딩 호출 → chunks insert
4. 멱등성: id 기준 upsert (재실행 안전)

## 비용/운영
Supabase Free(500MB DB, pgvector 포함) + Vercel Free → **전체 무료, 공개 URL, 설치 불필요** = 공고 제출요건 충족.
