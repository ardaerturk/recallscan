create table if not exists supplier_profiles (
  normalized_name text primary key,
  display_name text not null,
  details_json jsonb not null default '{}',
  sources_json jsonb not null default '[]',
  fetched_at timestamptz not null default now(),
  expires_at timestamptz not null,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_supplier_profiles_expires_at on supplier_profiles (expires_at);
