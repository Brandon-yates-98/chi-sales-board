-- Chicago Public Sector Sales Board: shared tracking marks.
-- One row per (person, role). Last write wins on updated_at; the page enforces that.
-- The board itself is public and the marks are two people's job-hunt notes, so the
-- anon key may read and write this one table and nothing else.

create table if not exists public.marks (
  person      text        not null check (person in ('stephen', 'frank')),
  role_id     integer     not null check (role_id > 0),
  status      text        check (status in ('Interested', 'Applied', 'Interviewing', 'Offer', 'Passed')),
  rating      smallint    check (rating between 1 and 5),
  updated_at  timestamptz not null default now(),
  primary key (person, role_id),
  check (status is not null or rating is not null)
);

comment on table public.marks is 'Per-person status and star rating for roles on the sales board.';

alter table public.marks enable row level security;

drop policy if exists "board can read marks"   on public.marks;
drop policy if exists "board can insert marks" on public.marks;
drop policy if exists "board can update marks" on public.marks;
drop policy if exists "board can delete marks" on public.marks;

create policy "board can read marks"   on public.marks for select to anon, authenticated using (true);
create policy "board can insert marks" on public.marks for insert to anon, authenticated with check (true);
create policy "board can update marks" on public.marks for update to anon, authenticated using (true) with check (true);
create policy "board can delete marks" on public.marks for delete to anon, authenticated using (true);

-- Newer-wins guard: an update whose updated_at is older than the stored row is a no-op.
create or replace function public.marks_keep_newer()
returns trigger language plpgsql as $$
begin
  if tg_op = 'UPDATE' and new.updated_at < old.updated_at then
    return null;
  end if;
  return new;
end $$;

drop trigger if exists marks_keep_newer on public.marks;
create trigger marks_keep_newer before update on public.marks
  for each row execute function public.marks_keep_newer();

-- Live updates for the page.
do $$
begin
  if not exists (
    select 1 from pg_publication_tables
    where pubname = 'supabase_realtime' and schemaname = 'public' and tablename = 'marks'
  ) then
    alter publication supabase_realtime add table public.marks;
  end if;
end $$;

-- The anon key must not see anything else in the public schema by default.
revoke all on all tables in schema public from anon;
grant select, insert, update, delete on public.marks to anon, authenticated;
