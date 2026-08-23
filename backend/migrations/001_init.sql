-- ==========================================================================
-- Bhopal CivicAI — initial schema for Supabase Postgres
--
-- Run this in the Supabase SQL Editor (or via `psql`) for a production
-- deployment, then set AUTO_CREATE_TABLES=false so the API never issues DDL.
-- It mirrors the SQLAlchemy models in app/models/ exactly.
--
-- Idempotent: safe to re-run.
-- ==========================================================================

create extension if not exists "pgcrypto";   -- gen_random_uuid()

-- --------------------------------------------------------------------------
-- departments
-- --------------------------------------------------------------------------
create table if not exists public.departments (
    id             uuid primary key default gen_random_uuid(),
    name           varchar(120) not null unique,
    code           varchar(32)  not null unique,
    description    text,
    contact_email  varchar(255),
    contact_phone  varchar(32),
    categories     jsonb        not null default '[]'::jsonb,
    sla_hours      integer      not null default 72,
    is_active      boolean      not null default true,
    created_at     timestamptz  not null default now(),
    updated_at     timestamptz  not null default now()
);

create index if not exists ix_departments_code       on public.departments (code);
create index if not exists ix_departments_created_at on public.departments (created_at);

-- --------------------------------------------------------------------------
-- profiles  (1:1 with auth.users; id IS the Supabase auth user id)
--
-- `role` is server-controlled. Nothing in the public API can set it; only the
-- backend's ADMIN_EMAILS allow-list, an existing admin, or the operator CLI.
-- --------------------------------------------------------------------------
create table if not exists public.profiles (
    id             uuid primary key references auth.users (id) on delete cascade,
    email          varchar(255) not null unique,
    full_name      varchar(160),
    phone          varchar(32),
    address        text,
    ward           varchar(80),
    city           varchar(80)  not null default 'Bhopal',
    avatar_url     text,
    language       varchar(8)   not null default 'en',
    role           varchar(32)  not null default 'citizen'
                   check (role in ('citizen', 'admin')),
    department_id  uuid references public.departments (id) on delete set null,
    is_active      boolean      not null default true,
    created_at     timestamptz  not null default now(),
    updated_at     timestamptz  not null default now()
);

create index if not exists ix_profiles_email         on public.profiles (email);
create index if not exists ix_profiles_role          on public.profiles (role);
create index if not exists ix_profiles_ward          on public.profiles (ward);
create index if not exists ix_profiles_department_id on public.profiles (department_id);
create index if not exists ix_profiles_created_at    on public.profiles (created_at);

-- --------------------------------------------------------------------------
-- complaints
-- --------------------------------------------------------------------------
create table if not exists public.complaints (
    id                     uuid primary key default gen_random_uuid(),
    reference_code         varchar(32)  not null unique,
    citizen_id             uuid         not null references public.profiles (id) on delete cascade,

    title                  varchar(200) not null,
    description            text         not null,
    image_url              text,
    image_urls             jsonb        not null default '[]'::jsonb,

    latitude               double precision not null,
    longitude              double precision not null,
    address                text,
    landmark               varchar(200),
    ward                   varchar(80),

    category               varchar(32)  not null default 'other'
                           check (category in ('road','garbage','streetlight','water','traffic','drainage','other')),
    severity               varchar(32)  not null default 'medium'
                           check (severity in ('low','medium','high','critical')),
    priority_score         integer      not null default 50,
    status                 varchar(32)  not null default 'submitted'
                           check (status in ('submitted','acknowledged','assigned','in_progress','resolved','rejected','duplicate','closed')),

    ai_summary             text,
    ai_suggested_action    text,
    ai_tags                jsonb        not null default '[]'::jsonb,
    ai_confidence          double precision,
    ai_model               varchar(64),
    ai_analysis_status     varchar(32)  not null default 'pending'
                           check (ai_analysis_status in ('pending','completed','fallback','failed','skipped')),
    ai_analyzed_at         timestamptz,

    department_id          uuid references public.departments (id) on delete set null,
    assigned_to_id         uuid references public.profiles (id)    on delete set null,

    duplicate_of_id        uuid references public.complaints (id)  on delete set null,
    similar_complaint_ids  jsonb        not null default '[]'::jsonb,
    confirmation_count     integer      not null default 0,

    resolution_notes       text,
    before_image_url       text,
    after_image_url        text,
    acknowledged_at        timestamptz,
    resolved_at            timestamptz,
    closed_at              timestamptz,

    created_at             timestamptz  not null default now(),
    updated_at             timestamptz  not null default now(),

    constraint ck_complaints_lat      check (latitude  >= -90  and latitude  <= 90),
    constraint ck_complaints_lon      check (longitude >= -180 and longitude <= 180),
    constraint ck_complaints_priority check (priority_score >= 0 and priority_score <= 100)
);

create index if not exists ix_complaints_reference_code    on public.complaints (reference_code);
create index if not exists ix_complaints_citizen_id        on public.complaints (citizen_id);
create index if not exists ix_complaints_status            on public.complaints (status);
create index if not exists ix_complaints_category          on public.complaints (category);
create index if not exists ix_complaints_severity          on public.complaints (severity);
create index if not exists ix_complaints_priority_score    on public.complaints (priority_score);
create index if not exists ix_complaints_ward              on public.complaints (ward);
create index if not exists ix_complaints_department_id     on public.complaints (department_id);
create index if not exists ix_complaints_assigned_to_id    on public.complaints (assigned_to_id);
create index if not exists ix_complaints_duplicate_of_id   on public.complaints (duplicate_of_id);
create index if not exists ix_complaints_created_at        on public.complaints (created_at);
-- Bounding-box prefilter for nearby / duplicate detection.
create index if not exists ix_complaints_lat_lon           on public.complaints (latitude, longitude);
create index if not exists ix_complaints_status_category   on public.complaints (status, category);
create index if not exists ix_complaints_citizen_created   on public.complaints (citizen_id, created_at);

-- --------------------------------------------------------------------------
-- complaint_confirmations  ("me too" — one per citizen per complaint)
-- --------------------------------------------------------------------------
create table if not exists public.complaint_confirmations (
    id               uuid primary key default gen_random_uuid(),
    complaint_id     uuid not null references public.complaints (id) on delete cascade,
    citizen_id       uuid not null references public.profiles (id)   on delete cascade,
    note             text,
    latitude         double precision,
    longitude        double precision,
    distance_meters  double precision,
    created_at       timestamptz not null default now(),
    updated_at       timestamptz not null default now(),
    constraint uq_confirmation_complaint_citizen unique (complaint_id, citizen_id)
);

create index if not exists ix_confirmations_complaint_id on public.complaint_confirmations (complaint_id);
create index if not exists ix_confirmations_citizen_id   on public.complaint_confirmations (citizen_id);
create index if not exists ix_confirmations_created_at   on public.complaint_confirmations (created_at);

-- --------------------------------------------------------------------------
-- complaint_updates  (append-only audit trail / public timeline)
-- --------------------------------------------------------------------------
create table if not exists public.complaint_updates (
    id            uuid primary key default gen_random_uuid(),
    complaint_id  uuid        not null references public.complaints (id) on delete cascade,
    actor_id      uuid references public.profiles (id) on delete set null,
    actor_role    varchar(32) check (actor_role in ('citizen','admin')),
    actor_label   varchar(64) not null default 'system',
    update_type   varchar(32) not null
                  check (update_type in ('created','ai_analysis','status_change','department_assigned',
                                         'priority_change','severity_change','category_change',
                                         'assignee_change','resolution_note','evidence_added',
                                         'confirmation','duplicate_linked','comment')),
    old_value     varchar(255),
    new_value     varchar(255),
    note          text,
    is_public     boolean     not null default true,
    created_at    timestamptz not null default now(),
    updated_at    timestamptz not null default now()
);

create index if not exists ix_updates_complaint_id on public.complaint_updates (complaint_id);
create index if not exists ix_updates_actor_id     on public.complaint_updates (actor_id);
create index if not exists ix_updates_update_type  on public.complaint_updates (update_type);
create index if not exists ix_updates_created_at   on public.complaint_updates (created_at);

-- --------------------------------------------------------------------------
-- updated_at maintenance
-- --------------------------------------------------------------------------
create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.updated_at = now();
    return new;
end;
$$;

drop trigger if exists trg_profiles_updated_at on public.profiles;
create trigger trg_profiles_updated_at before update on public.profiles
    for each row execute function public.set_updated_at();

drop trigger if exists trg_departments_updated_at on public.departments;
create trigger trg_departments_updated_at before update on public.departments
    for each row execute function public.set_updated_at();

drop trigger if exists trg_complaints_updated_at on public.complaints;
create trigger trg_complaints_updated_at before update on public.complaints
    for each row execute function public.set_updated_at();

drop trigger if exists trg_confirmations_updated_at on public.complaint_confirmations;
create trigger trg_confirmations_updated_at before update on public.complaint_confirmations
    for each row execute function public.set_updated_at();

drop trigger if exists trg_updates_updated_at on public.complaint_updates;
create trigger trg_updates_updated_at before update on public.complaint_updates
    for each row execute function public.set_updated_at();

-- --------------------------------------------------------------------------
-- Seed departments (matches app/database/init_db.py)
-- --------------------------------------------------------------------------
insert into public.departments (name, code, description, categories, contact_email, sla_hours)
values
    ('Public Works Department',       'PWD',     'Roads, footpaths, potholes and civil infrastructure.', '["road"]',        'pwd@bhopalcivicai.in',       96),
    ('Solid Waste Management',        'SWM',     'Garbage collection, dumping points and street sweeping.', '["garbage"]',   'swm@bhopalcivicai.in',       24),
    ('Electrical & Street Lighting',  'ELEC',    'Street lights, poles and public electrical faults.',    '["streetlight"]', 'electrical@bhopalcivicai.in', 48),
    ('Water Supply',                  'WATER',   'Pipelines, leakages, supply interruptions and quality.', '["water"]',      'water@bhopalcivicai.in',     24),
    ('Traffic Police & Management',   'TRAFFIC', 'Signals, signage, encroachment and traffic congestion.', '["traffic"]',    'traffic@bhopalcivicai.in',   48),
    ('Drainage & Sewerage',           'DRAIN',   'Storm drains, sewer overflow and waterlogging.',         '["drainage"]',   'drainage@bhopalcivicai.in',  48),
    ('General Grievance Cell',        'GENERAL', 'Fallback department for uncategorised civic issues.',    '["other"]',      'grievance@bhopalcivicai.in', 120)
on conflict (code) do nothing;

-- ==========================================================================
-- Row Level Security
--
-- The FastAPI backend connects with the Postgres/service role, which bypasses
-- RLS — authorisation for the API is enforced in app/auth/dependencies.py.
-- These policies protect the data if the React client (or anything else using
-- the anon key) ever queries Supabase directly.
-- ==========================================================================

alter table public.profiles                enable row level security;
alter table public.departments             enable row level security;
alter table public.complaints              enable row level security;
alter table public.complaint_confirmations enable row level security;
alter table public.complaint_updates       enable row level security;

-- Helper: is the caller an admin?
create or replace function public.is_admin()
returns boolean
language sql
security definer
stable
set search_path = public
as $$
    select exists (
        select 1 from public.profiles
        where id = auth.uid() and role = 'admin' and is_active
    );
$$;

-- profiles ---------------------------------------------------------------
drop policy if exists profiles_select_own    on public.profiles;
drop policy if exists profiles_update_own    on public.profiles;
drop policy if exists profiles_admin_all     on public.profiles;

create policy profiles_select_own on public.profiles
    for select using (id = auth.uid() or public.is_admin());

-- A citizen may edit their own row but NOT their role, and cannot
-- self-activate or attach themselves to a department.
create policy profiles_update_own on public.profiles
    for update using (id = auth.uid())
    with check (
        id = auth.uid()
        and role = (select p.role from public.profiles p where p.id = auth.uid())
        and is_active = (select p.is_active from public.profiles p where p.id = auth.uid())
        and department_id is not distinct from
            (select p.department_id from public.profiles p where p.id = auth.uid())
    );

create policy profiles_admin_all on public.profiles
    for all using (public.is_admin()) with check (public.is_admin());

-- departments ------------------------------------------------------------
drop policy if exists departments_read_all  on public.departments;
drop policy if exists departments_admin_all on public.departments;

create policy departments_read_all on public.departments
    for select using (auth.role() = 'authenticated');

create policy departments_admin_all on public.departments
    for all using (public.is_admin()) with check (public.is_admin());

-- complaints -------------------------------------------------------------
drop policy if exists complaints_select_own    on public.complaints;
drop policy if exists complaints_insert_own    on public.complaints;
drop policy if exists complaints_update_own    on public.complaints;
drop policy if exists complaints_admin_all     on public.complaints;

create policy complaints_select_own on public.complaints
    for select using (citizen_id = auth.uid() or public.is_admin());

create policy complaints_insert_own on public.complaints
    for insert with check (citizen_id = auth.uid());

-- Only while still unacknowledged, and never the workflow fields.
create policy complaints_update_own on public.complaints
    for update using (citizen_id = auth.uid() and status = 'submitted')
    with check (citizen_id = auth.uid() and status = 'submitted');

create policy complaints_admin_all on public.complaints
    for all using (public.is_admin()) with check (public.is_admin());

-- complaint_confirmations ------------------------------------------------
drop policy if exists confirmations_select on public.complaint_confirmations;
drop policy if exists confirmations_insert on public.complaint_confirmations;
drop policy if exists confirmations_admin  on public.complaint_confirmations;

create policy confirmations_select on public.complaint_confirmations
    for select using (citizen_id = auth.uid() or public.is_admin());

create policy confirmations_insert on public.complaint_confirmations
    for insert with check (
        citizen_id = auth.uid()
        and exists (
            select 1 from public.complaints c
            where c.id = complaint_id
              and c.citizen_id <> auth.uid()
              and c.status in ('submitted','acknowledged','assigned','in_progress')
        )
    );

create policy confirmations_admin on public.complaint_confirmations
    for all using (public.is_admin()) with check (public.is_admin());

-- complaint_updates ------------------------------------------------------
-- Citizens read only public entries on their own complaints; the trail is
-- append-only from the client's perspective (no insert/update/delete policy).
drop policy if exists updates_select_public on public.complaint_updates;
drop policy if exists updates_admin_all     on public.complaint_updates;

create policy updates_select_public on public.complaint_updates
    for select using (
        public.is_admin()
        or (
            is_public
            and exists (
                select 1 from public.complaints c
                where c.id = complaint_id and c.citizen_id = auth.uid()
            )
        )
    );

create policy updates_admin_all on public.complaint_updates
    for all using (public.is_admin()) with check (public.is_admin());

-- ==========================================================================
-- OPTIONAL: auto-create a profile row on signup.
--
-- Left disabled on purpose. The backend provisions profiles on the first
-- authenticated request (app/services/profile_service.py), which is where the
-- ADMIN_EMAILS allow-list is applied. If this trigger creates the row first,
-- every user is a citizen until an admin promotes them — enable it only if you
-- want profiles to exist before the user's first API call.
-- ==========================================================================
-- create or replace function public.handle_new_user()
-- returns trigger language plpgsql security definer set search_path = public as $$
-- begin
--     insert into public.profiles (id, email, full_name)
--     values (new.id, new.email, new.raw_user_meta_data->>'full_name')
--     on conflict (id) do nothing;
--     return new;
-- end;
-- $$;
--
-- drop trigger if exists on_auth_user_created on auth.users;
-- create trigger on_auth_user_created
--     after insert on auth.users
--     for each row execute function public.handle_new_user();
