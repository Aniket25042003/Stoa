-- Create waitlist table to store registration name and email
create table if not exists public.waitlist (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  email text not null unique,
  created_at timestamptz not null default now()
);

-- Enable Row Level Security
alter table public.waitlist enable row level security;

-- Allow anonymous inserts to the waitlist table
create policy "Allow anonymous inserts" on public.waitlist
  for insert with check (true);
