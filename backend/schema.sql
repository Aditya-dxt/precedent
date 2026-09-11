-- ==============================================================================
-- Precedent — Database Schema for Supabase (PostgreSQL)
-- Horizon 2026: AI Exam Pattern & Revision Platform
-- ==============================================================================

-- 1. Enable UUID extension
create extension if not exists "uuid-ossp";

-- 2. Institutions table
create table if not exists public.institutions (
  id uuid primary key default uuid_generate_v4(),
  name text not null unique,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 3. Courses table
create table if not exists public.courses (
  id uuid primary key default uuid_generate_v4(),
  institution_id uuid references public.institutions(id) on delete cascade not null,
  name text not null,
  code text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(institution_id, name, code)
);

-- 4. Subjects table
create table if not exists public.subjects (
  id uuid primary key default uuid_generate_v4(),
  course_id uuid references public.courses(id) on delete cascade not null,
  name text not null,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null,
  unique(course_id, name)
);

-- 5. Submissions table
create table if not exists public.submissions (
  id uuid primary key default uuid_generate_v4(),
  subject_id uuid references public.subjects(id) on delete cascade,
  syllabus_url text,
  uploaded_by text default 'anonymous',
  status text default 'pending',
  job_data jsonb default '{}'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 6. PYQs table (tagged by year)
create table if not exists public.pyqs (
  id uuid primary key default uuid_generate_v4(),
  submission_id uuid references public.submissions(id) on delete cascade,
  year integer not null,
  file_url text,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 7. Topics table (pattern analysis output)
create table if not exists public.topics (
  id uuid primary key default uuid_generate_v4(),
  subject_id uuid references public.subjects(id) on delete cascade,
  name text not null,
  frequency_score double precision default 0.0,
  marks_weight double precision default 0.0,
  cluster_data jsonb default '{}'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 8. Revision plans table (knapsack solver output)
create table if not exists public.revision_plans (
  id uuid primary key default uuid_generate_v4(),
  user_id text default 'anonymous',
  subject_id uuid references public.subjects(id) on delete cascade,
  days_available integer not null,
  hours_per_day double precision not null,
  plan_json jsonb not null default '{}'::jsonb,
  created_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- 9. Mock papers table (inferred format simulated papers)
create table if not exists public.mock_papers (
  id uuid primary key default uuid_generate_v4(),
  subject_id uuid references public.subjects(id) on delete cascade,
  version integer default 1,
  content_json jsonb not null default '{}'::jsonb,
  file_url text,
  generated_at timestamp with time zone default timezone('utc'::text, now()) not null
);

-- Row Level Security (RLS) Configuration
-- For MVP: enable public read/write access or configure as appropriate
alter table public.institutions enable row level security;
alter table public.courses enable row level security;
alter table public.subjects enable row level security;
alter table public.submissions enable row level security;
alter table public.pyqs enable row level security;
alter table public.topics enable row level security;
alter table public.revision_plans enable row level security;
alter table public.mock_papers enable row level security;

-- Public access policies (for client anon key and API operations)
create policy "Allow public read access on institutions" on public.institutions for select using (true);
create policy "Allow public insert on institutions" on public.institutions for insert with check (true);

create policy "Allow public read access on courses" on public.courses for select using (true);
create policy "Allow public insert on courses" on public.courses for insert with check (true);

create policy "Allow public read access on subjects" on public.subjects for select using (true);
create policy "Allow public insert on subjects" on public.subjects for insert with check (true);

create policy "Allow public read access on submissions" on public.submissions for select using (true);
create policy "Allow public insert on submissions" on public.submissions for insert with check (true);
create policy "Allow public update on submissions" on public.submissions for update using (true);

create policy "Allow public read access on pyqs" on public.pyqs for select using (true);
create policy "Allow public insert on pyqs" on public.pyqs for insert with check (true);

create policy "Allow public read access on topics" on public.topics for select using (true);
create policy "Allow public insert on topics" on public.topics for insert with check (true);
create policy "Allow public delete on topics" on public.topics for delete using (true);

create policy "Allow public read access on revision_plans" on public.revision_plans for select using (true);
create policy "Allow public insert on revision_plans" on public.revision_plans for insert with check (true);

create policy "Allow public read access on mock_papers" on public.mock_papers for select using (true);
create policy "Allow public insert on mock_papers" on public.mock_papers for insert with check (true);
