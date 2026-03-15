-- Run this in your Supabase SQL editor to create the articles table

create table if not exists articles (
  id            text primary key,           -- MD5 hash of article URL
  title         text not null,
  excerpt       text,
  url           text not null,
  source_name   text not null,
  source_logo   text,                       -- domain like "bbc.com" for favicon
  category      text not null,
  image_url     text,
  published_at  timestamptz,
  fetched_at    timestamptz default now(),
  tags          text[]
);

-- Index for fast category + date filtering (used by the API)
create index if not exists idx_articles_category_date
  on articles (category, published_at desc);

-- Index for fast date-ordered queries on homepage
create index if not exists idx_articles_published
  on articles (published_at desc);

-- Enable Row Level Security (RLS) and allow public read access
alter table articles enable row level security;

create policy "Public read access"
  on articles for select
  using (true);
