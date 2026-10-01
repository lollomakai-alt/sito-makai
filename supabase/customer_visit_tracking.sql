begin;

alter table public.bookings
  add column if not exists arrived_at timestamptz,
  add column if not exists marketing_visit_counted_at timestamptz;

alter table public.marketing_contacts
  add column if not exists visite_totali integer not null default 0,
  add column if not exists ultima_visita timestamptz;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'marketing_contacts_visits_check'
      and conrelid = 'public.marketing_contacts'::regclass
  ) then
    alter table public.marketing_contacts
      add constraint marketing_contacts_visits_check check (visite_totali >= 0);
  end if;
end
$$;

commit;
