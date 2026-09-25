-- InstaLILY GTM pipeline schema. This migration creates structure only.

create or replace function public.set_updated_at()
returns trigger
language plpgsql
security invoker
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create table public.events (
  id uuid primary key default gen_random_uuid(),
  event_name text not null,
  event_url text,
  normalized_event_url text,
  dates text,
  start_date date,
  end_date date,
  location text,
  venue text,
  cost text,
  description text,
  industry_vertical text,
  exhibitor_mix text,
  audience_mix text,
  source text,
  overall_score numeric(4, 2),
  reasoning text,
  sales_brief text,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint events_date_range_check check (
    start_date is null or end_date is null or end_date >= start_date
  ),
  constraint events_overall_score_check check (
    overall_score is null or overall_score between 0 and 10
  )
);

create table public.event_score_factors (
  event_id uuid not null references public.events(id) on delete cascade,
  factor_key text not null,
  score numeric(4, 2) not null,
  weight numeric(5, 4),
  rationale text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (event_id, factor_key),
  constraint event_score_factors_score_check check (score between 0 and 10),
  constraint event_score_factors_weight_check check (
    weight is null or weight between 0 and 1
  )
);

create table public.event_attendance (
  event_id uuid primary key references public.events(id) on delete cascade,
  attending boolean not null default false,
  whos_going text[] not null default '{}'::text[],
  notes text,
  updated_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.event_feedback (
  event_id uuid primary key references public.events(id) on delete cascade,
  would_attend_again boolean,
  notes text not null default '',
  updated_by uuid references auth.users(id) on delete set null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.companies (
  id uuid primary key default gen_random_uuid(),
  company_name text not null,
  website_url text,
  normalized_domain text,
  description text,
  overall_score numeric(5, 2),
  qualification_summary text,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint companies_overall_score_check check (
    overall_score is null or overall_score between 0 and 100
  )
);

create table public.event_companies (
  event_id uuid not null references public.events(id) on delete cascade,
  company_id uuid not null references public.companies(id) on delete cascade,
  attendance_type text not null default 'unknown',
  confidence text not null default 'unknown',
  booth_number text,
  source text,
  source_reasoning text,
  source_urls text[] not null default '{}'::text[],
  relevance_indicators text[] not null default '{}'::text[],
  raw_data jsonb not null default '{}'::jsonb,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  is_active boolean not null default true,
  updated_at timestamptz not null default now(),
  primary key (event_id, company_id),
  constraint event_companies_attendance_type_check check (
    attendance_type in ('exhibitor', 'sponsor', 'speaker', 'attendee', 'unknown')
  ),
  constraint event_companies_confidence_check check (
    confidence in ('confirmed', 'likely', 'unknown')
  )
);

create table public.company_score_factors (
  company_id uuid not null references public.companies(id) on delete cascade,
  factor_key text not null,
  score numeric(4, 2) not null,
  weight numeric(5, 4) not null,
  rationale text[] not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (company_id, factor_key),
  constraint company_score_factors_score_check check (score between 0 and 10),
  constraint company_score_factors_weight_check check (weight between 0 and 1),
  constraint company_score_factors_rationale_check check (
    cardinality(rationale) between 2 and 3
  )
);

create table public.target_roles (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies(id) on delete cascade,
  title text not null,
  priority smallint not null,
  rationale text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint target_roles_priority_check check (priority > 0),
  unique (company_id, title)
);

create table public.linkedin_searches (
  id uuid primary key default gen_random_uuid(),
  target_role_id uuid not null references public.target_roles(id) on delete cascade,
  search_url text not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (target_role_id)
);

create table public.contacts (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies(id) on delete cascade,
  target_role_id uuid references public.target_roles(id) on delete set null,
  full_name text not null,
  title text,
  email text,
  linkedin_url text,
  source text,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.outreach_generation (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies(id) on delete cascade,
  target_role_id uuid references public.target_roles(id) on delete set null,
  contact_id uuid references public.contacts(id) on delete set null,
  channel text not null,
  engagement_strategy jsonb not null default '{}'::jsonb,
  personalization_hooks jsonb not null default '[]'::jsonb,
  subject text,
  body text not null,
  status text not null default 'draft',
  model text,
  prompt_version text,
  raw_data jsonb not null default '{}'::jsonb,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  constraint outreach_generation_channel_check check (
    channel in ('email', 'linkedin')
  ),
  constraint outreach_generation_status_check check (
    status in ('draft', 'approved', 'sent', 'archived')
  )
);

create index events_start_date_idx on public.events(start_date);
create index events_overall_score_idx on public.events(overall_score desc);
create index events_normalized_url_idx on public.events(normalized_event_url);
create index companies_name_idx on public.companies(company_name);
create unique index companies_normalized_domain_key
  on public.companies(normalized_domain)
  where normalized_domain is not null and normalized_domain <> '';
create index companies_overall_score_idx on public.companies(overall_score desc);
create index event_companies_company_id_idx on public.event_companies(company_id);
create index event_companies_active_idx on public.event_companies(event_id, is_active);
create index target_roles_company_id_idx on public.target_roles(company_id);
create index contacts_company_id_idx on public.contacts(company_id);
create index contacts_target_role_id_idx on public.contacts(target_role_id);
create index outreach_generation_company_id_idx on public.outreach_generation(company_id);
create index outreach_generation_contact_id_idx on public.outreach_generation(contact_id);

create trigger set_events_updated_at
before update on public.events
for each row execute function public.set_updated_at();

create trigger set_event_score_factors_updated_at
before update on public.event_score_factors
for each row execute function public.set_updated_at();

create trigger set_event_attendance_updated_at
before update on public.event_attendance
for each row execute function public.set_updated_at();

create trigger set_event_feedback_updated_at
before update on public.event_feedback
for each row execute function public.set_updated_at();

create trigger set_companies_updated_at
before update on public.companies
for each row execute function public.set_updated_at();

create trigger set_event_companies_updated_at
before update on public.event_companies
for each row execute function public.set_updated_at();

create trigger set_company_score_factors_updated_at
before update on public.company_score_factors
for each row execute function public.set_updated_at();

create trigger set_target_roles_updated_at
before update on public.target_roles
for each row execute function public.set_updated_at();

create trigger set_linkedin_searches_updated_at
before update on public.linkedin_searches
for each row execute function public.set_updated_at();

create trigger set_contacts_updated_at
before update on public.contacts
for each row execute function public.set_updated_at();

create trigger set_outreach_generation_updated_at
before update on public.outreach_generation
for each row execute function public.set_updated_at();

alter table public.events enable row level security;
alter table public.event_score_factors enable row level security;
alter table public.event_attendance enable row level security;
alter table public.event_feedback enable row level security;
alter table public.companies enable row level security;
alter table public.event_companies enable row level security;
alter table public.company_score_factors enable row level security;
alter table public.target_roles enable row level security;
alter table public.linkedin_searches enable row level security;
alter table public.contacts enable row level security;
alter table public.outreach_generation enable row level security;

revoke all on table
  public.events,
  public.event_score_factors,
  public.event_attendance,
  public.event_feedback,
  public.companies,
  public.event_companies,
  public.company_score_factors,
  public.target_roles,
  public.linkedin_searches,
  public.contacts,
  public.outreach_generation
from anon;

grant select, insert, update, delete on table
  public.events,
  public.event_score_factors,
  public.event_attendance,
  public.event_feedback,
  public.companies,
  public.event_companies,
  public.company_score_factors,
  public.target_roles,
  public.linkedin_searches,
  public.contacts,
  public.outreach_generation
to authenticated, service_role;

create policy "Authenticated users can manage events"
on public.events for all to authenticated using (true) with check (true);

create policy "Authenticated users can manage event score factors"
on public.event_score_factors for all to authenticated using (true) with check (true);

create policy "Authenticated users can manage event attendance"
on public.event_attendance for all to authenticated using (true) with check (true);

create policy "Authenticated users can manage event feedback"
on public.event_feedback for all to authenticated using (true) with check (true);

create policy "Authenticated users can manage companies"
on public.companies for all to authenticated using (true) with check (true);

create policy "Authenticated users can manage event companies"
on public.event_companies for all to authenticated using (true) with check (true);

create policy "Authenticated users can manage company score factors"
on public.company_score_factors for all to authenticated using (true) with check (true);

create policy "Authenticated users can manage target roles"
on public.target_roles for all to authenticated using (true) with check (true);

create policy "Authenticated users can manage LinkedIn searches"
on public.linkedin_searches for all to authenticated using (true) with check (true);

create policy "Authenticated users can manage contacts"
on public.contacts for all to authenticated using (true) with check (true);

create policy "Authenticated users can manage outreach generation"
on public.outreach_generation for all to authenticated using (true) with check (true);
