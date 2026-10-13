-- Preparazione separata: NON applicata al database live.
-- Stato globale indipendente dalle chiusure per singola data.
begin;
set local lock_timeout = '5s';

create table if not exists private.site_maintenance (
  id boolean primary key default true check (id = true),
  active boolean not null default false,
  updated_at timestamptz not null default now(),
  updated_by text
);
alter table private.site_maintenance enable row level security;
revoke all on private.site_maintenance from public, anon, authenticated, service_role;
insert into private.site_maintenance (id, active)
values (true, false) on conflict (id) do nothing;

create table if not exists private.site_maintenance_history (
  id bigint generated always as identity primary key,
  active boolean not null,
  actor_id text not null,
  created_at timestamptz not null default now()
);
alter table private.site_maintenance_history enable row level security;
revoke all on private.site_maintenance_history from public, anon, authenticated, service_role;

commit;
