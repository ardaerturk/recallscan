create table if not exists stores (
  id text primary key,
  name text not null,
  state text not null,
  city text not null,
  region text not null,
  created_at timestamptz not null default now()
);

create table if not exists catalog_items (
  id text primary key,
  sku text not null unique,
  brand text not null,
  product_name text not null,
  upc text,
  category text not null,
  supplier_name text not null,
  co_manufacturer_name text,
  ingredients_json jsonb not null default '[]',
  allergens_json jsonb not null default '[]',
  supplier_aliases_json jsonb not null default '[]',
  metadata_json jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create index if not exists idx_catalog_items_upc on catalog_items (upc);
create index if not exists idx_catalog_items_brand on catalog_items (brand);
create index if not exists idx_catalog_items_supplier on catalog_items (supplier_name);

create table if not exists inventory_lots (
  id text primary key,
  catalog_item_id text not null references catalog_items(id),
  store_id text not null references stores(id),
  lot_code text,
  quantity_on_hand integer not null default 0,
  last_seen_at timestamptz not null default now()
);

create index if not exists idx_inventory_catalog_item on inventory_lots (catalog_item_id);
create index if not exists idx_inventory_store on inventory_lots (store_id);
create index if not exists idx_inventory_lot_code on inventory_lots (lot_code);

create table if not exists external_sources (
  id text primary key,
  canonical_url text not null unique,
  source_domain text not null,
  source_type text not null,
  title text not null,
  published_at timestamptz,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  content_hash text,
  raw_exa_result_json jsonb not null default '{}'
);

create table if not exists recall_signals (
  id text primary key,
  source_id text not null references external_sources(id),
  fingerprint text not null unique,
  title text not null,
  company text,
  hazard_type text not null,
  hazard_description text not null,
  affected_products_json jsonb not null default '[]',
  identifiers_json jsonb not null default '{}',
  supplier_chain_json jsonb not null default '[]',
  retailers_json jsonb not null default '[]',
  distribution_json jsonb not null default '{}',
  explicit_exclusions_json jsonb not null default '[]',
  event_date date,
  raw_extraction_json jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table if not exists exposure_matches (
  id text primary key,
  recall_signal_id text not null references recall_signals(id),
  catalog_item_id text not null references catalog_items(id),
  tier text not null,
  match_type text not null,
  matched_fields_json jsonb not null default '{}',
  missing_fields_json jsonb not null default '[]',
  explanation text not null,
  recommended_action text not null,
  created_at timestamptz not null default now(),
  unique(recall_signal_id, catalog_item_id, match_type)
);

create table if not exists scan_runs (
  id text primary key,
  scan_type text not null,
  status text not null,
  idempotency_key text unique,
  query_version text not null,
  started_at timestamptz not null default now(),
  finished_at timestamptz,
  error_message text,
  sources_found integer not null default 0,
  signals_created integer not null default 0,
  signals_updated integer not null default 0,
  matches_created integer not null default 0
);

create table if not exists job_locks (
  name text primary key,
  owner_id text not null,
  expires_at timestamptz not null,
  created_at timestamptz not null default now()
);

create table if not exists idempotency_keys (
  key text primary key,
  request_hash text not null,
  response_json jsonb not null default '{}',
  status_code integer not null,
  created_at timestamptz not null default now(),
  expires_at timestamptz not null
);
