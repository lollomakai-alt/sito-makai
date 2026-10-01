begin;

alter table public.marketing_contacts
  add column if not exists phone text,
  add column if not exists booking_id bigint,
  add column if not exists canale text,
  add column if not exists consenso_testo text,
  add column if not exists consenso_versione text,
  add column if not exists privacy_versione text,
  add column if not exists risposta text,
  add column if not exists scadenza_consenso timestamptz,
  add column if not exists revocato_il timestamptz,
  add column if not exists rinnovi integer not null default 1,
  add column if not exists registrato_da text,
  add column if not exists updated_at timestamptz not null default now();

alter table public.marketing_contacts
  alter column email drop not null;

update public.marketing_contacts
set scadenza_consenso = consenso_data + interval '24 months'
where scadenza_consenso is null;

alter table public.marketing_contacts
  alter column scadenza_consenso set not null;

alter table public.marketing_contacts
  drop constraint if exists marketing_contacts_email_key;

do $$
begin
  if not exists (
    select 1 from pg_constraint
    where conname = 'marketing_contacts_booking_id_fkey'
      and conrelid = 'public.marketing_contacts'::regclass
  ) then
    alter table public.marketing_contacts
      add constraint marketing_contacts_booking_id_fkey
      foreign key (booking_id) references public.bookings(id) on delete set null;
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'marketing_contacts_channel_check'
      and conrelid = 'public.marketing_contacts'::regclass
  ) then
    alter table public.marketing_contacts
      add constraint marketing_contacts_channel_check
      check (canale is null or canale in ('whatsapp', 'telefono', 'email'));
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'marketing_contacts_renewals_check'
      and conrelid = 'public.marketing_contacts'::regclass
  ) then
    alter table public.marketing_contacts
      add constraint marketing_contacts_renewals_check check (rinnovi > 0);
  end if;

  if not exists (
    select 1 from pg_constraint
    where conname = 'marketing_contacts_expiry_check'
      and conrelid = 'public.marketing_contacts'::regclass
  ) then
    alter table public.marketing_contacts
      add constraint marketing_contacts_expiry_check
      check (scadenza_consenso > consenso_data);
  end if;
end
$$;

create unique index if not exists marketing_contacts_email_unique
  on public.marketing_contacts (lower(email))
  where email is not null and email <> '';

create unique index if not exists marketing_contacts_phone_unique
  on public.marketing_contacts (phone)
  where phone is not null;

create index if not exists marketing_contacts_expiry_idx
  on public.marketing_contacts (scadenza_consenso);

alter table public.marketing_contacts enable row level security;
revoke all on table public.marketing_contacts from anon, authenticated;
revoke all on sequence public.marketing_contacts_id_seq from anon, authenticated;

select cron.schedule(
  'delete-expired-marketing-contacts',
  '15 3 * * *',
  $$delete from public.marketing_contacts where scadenza_consenso <= now()$$
);

commit;
