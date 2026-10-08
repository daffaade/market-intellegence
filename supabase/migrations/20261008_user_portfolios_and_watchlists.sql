-- Applied to Supabase via MCP on 2026-10-08. Kept out of backend/db/migrations
-- because sqlc parses that folder and does not know the auth schema.
create table public.user_portfolios (
  user_id uuid primary key references auth.users(id) on delete cascade,
  holdings jsonb not null default '[]'::jsonb check (jsonb_typeof(holdings) = 'array'),
  updated_at timestamptz not null default now()
);

create table public.user_watchlists (
  user_id uuid primary key references auth.users(id) on delete cascade,
  symbols text[] not null default '{}',
  updated_at timestamptz not null default now()
);

alter table public.user_portfolios enable row level security;
alter table public.user_watchlists enable row level security;

create policy "own portfolio: select" on public.user_portfolios for select to authenticated using ((select auth.uid()) = user_id);
create policy "own portfolio: insert" on public.user_portfolios for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "own portfolio: update" on public.user_portfolios for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

create policy "own watchlist: select" on public.user_watchlists for select to authenticated using ((select auth.uid()) = user_id);
create policy "own watchlist: insert" on public.user_watchlists for insert to authenticated with check ((select auth.uid()) = user_id);
create policy "own watchlist: update" on public.user_watchlists for update to authenticated using ((select auth.uid()) = user_id) with check ((select auth.uid()) = user_id);

revoke all on public.user_portfolios, public.user_watchlists from anon;
grant select, insert, update on public.user_portfolios, public.user_watchlists to authenticated;
