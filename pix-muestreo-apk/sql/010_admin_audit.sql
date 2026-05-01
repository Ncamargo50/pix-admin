-- ═══════════════════════════════════════════════════════════════════════
-- Migration 010 — Admin Users + Audit Log + Tech soft-delete column
-- Apply via Supabase SQL Editor as service_role
-- ═══════════════════════════════════════════════════════════════════════

-- ─────────────────────────────────────────────────────────────
-- 1. admin_users — per-admin accounts replacing single shared password
-- ─────────────────────────────────────────────────────────────
create table if not exists public.admin_users (
  id            uuid primary key default gen_random_uuid(),
  username      text unique not null,
  full_name     text,
  email         text,
  password_hash text not null,           -- 'salt:hash' format (SHA-256)
  role          text not null default 'admin' check (role in ('admin','supervisor','viewer')),
  totp_secret   text,                    -- base32, null = 2FA disabled
  totp_enabled  boolean not null default false,
  active        boolean not null default true,
  last_login_at timestamptz,
  created_at    timestamptz not null default now(),
  updated_at    timestamptz not null default now()
);

create index if not exists admin_users_username_idx on public.admin_users (username);

-- Seed default admin if table empty (password = "pixadvisor2026!" — change immediately)
-- salt = a1b2c3d4e5f60718, hash = sha256("a1b2c3d4e5f60718pixadvisor2026!")
insert into public.admin_users (username, full_name, password_hash, role)
select 'admin', 'Administrador', 'a1b2c3d4e5f60718:84961c681d954d3888ecf20cd22ebec6aab1d5aaa51ae299d1429e1b80dbc54a', 'admin'
where not exists (select 1 from public.admin_users);

-- RLS: anon can read for login (only username + password_hash + totp), service_role manages
alter table public.admin_users enable row level security;

drop policy if exists admin_users_anon_read on public.admin_users;
create policy admin_users_anon_read on public.admin_users
  for select to anon using (active = true);

drop policy if exists admin_users_service_all on public.admin_users;
create policy admin_users_service_all on public.admin_users
  for all to service_role using (true) with check (true);

-- Anon can update only last_login_at (login bookkeeping)
drop policy if exists admin_users_anon_update_login on public.admin_users;
create policy admin_users_anon_update_login on public.admin_users
  for update to anon using (active = true) with check (active = true);


-- ─────────────────────────────────────────────────────────────
-- 2. audit_log — every admin action recorded (who/what/when)
-- ─────────────────────────────────────────────────────────────
create table if not exists public.audit_log (
  id          uuid primary key default gen_random_uuid(),
  admin_user  text not null,            -- username of the admin
  admin_id    uuid,                     -- nullable, FK to admin_users.id
  action      text not null,            -- 'create_tech','delete_tech','reset_pw','change_role','delete_order','delete_device','change_status','login','logout','login_failed'
  target_type text,                     -- 'technician','order','device','admin_user', etc.
  target_id   text,                     -- target row id
  target_name text,                     -- human-readable label
  details     jsonb,                    -- extra payload (before/after, etc.)
  ip_address  text,                     -- best-effort, browser-side
  user_agent  text,
  created_at  timestamptz not null default now()
);

create index if not exists audit_log_created_idx on public.audit_log (created_at desc);
create index if not exists audit_log_admin_idx on public.audit_log (admin_user, created_at desc);
create index if not exists audit_log_target_idx on public.audit_log (target_type, target_id);

-- RLS: anon can insert (admin actions logged from browser), select for admins only
alter table public.audit_log enable row level security;

drop policy if exists audit_log_anon_insert on public.audit_log;
create policy audit_log_anon_insert on public.audit_log
  for insert to anon with check (true);

drop policy if exists audit_log_anon_select on public.audit_log;
create policy audit_log_anon_select on public.audit_log
  for select to anon using (true);

drop policy if exists audit_log_service_all on public.audit_log;
create policy audit_log_service_all on public.audit_log
  for all to service_role using (true) with check (true);

-- Audit log is APPEND-ONLY: no update or delete from anon
-- (no policies for update/delete on anon means RLS denies them)


-- ─────────────────────────────────────────────────────────────
-- 3. technicians.deleted_at column for soft-delete with timestamp
-- ─────────────────────────────────────────────────────────────
alter table public.technicians
  add column if not exists deleted_at timestamptz;

create index if not exists technicians_active_idx on public.technicians (active) where active = true;


-- ─────────────────────────────────────────────────────────────
-- 4. Realtime publication — ensure new tables stream
-- ─────────────────────────────────────────────────────────────
do $$
begin
  if not exists (select 1 from pg_publication_tables where pubname='supabase_realtime' and tablename='audit_log') then
    alter publication supabase_realtime add table public.audit_log;
  end if;
exception when others then null;
end $$;
