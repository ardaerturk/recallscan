export type CatalogItem = {
  id: string;
  sku: string;
  brand: string;
  product_name: string;
  upc: string | null;
  category: string;
  supplier_name: string;
  co_manufacturer_name: string | null;
  ingredients: string[];
  allergens: string[];
  supplier_aliases: string[];
  metadata: Record<string, unknown>;
};

export type InventoryLot = {
  id: string;
  catalog_item_id: string;
  store_id: string;
  store_name: string;
  city: string;
  state: string;
  latitude: number | null;
  longitude: number | null;
  lot_code: string | null;
  quantity_on_hand: number;
  last_seen_at: string;
};

export type CatalogSummary = {
  sku_count: number;
  supplier_count: number;
  store_count: number;
  inventory_units: number;
};

export type Source = {
  id: string;
  canonical_url: string;
  source_domain: string;
  source_type: string;
  title: string;
  image_url: string | null;
  favicon_url: string | null;
  image_links: string[];
  published_at: string | null;
  first_seen_at: string;
  last_seen_at: string;
  raw_exa_result: Record<string, unknown>;
};

export type ExposureMatch = {
  id: string;
  catalog_item: CatalogItem;
  tier: TriageTier;
  match_type: string;
  matched_fields: Record<string, unknown>;
  missing_fields: string[];
  explanation: string;
  recommended_action: string;
  impacted_inventory: InventoryLot[];
};

export type RecallSignal = {
  id: string;
  title: string;
  company: string | null;
  hazard_type: string;
  hazard_description: string;
  affected_products: Record<string, unknown>[];
  identifiers: Record<string, unknown>;
  supplier_chain: Record<string, unknown>[];
  retailers: string[];
  distribution: Record<string, unknown>;
  explicit_exclusions: Record<string, unknown>[];
  event_date: string | null;
  source: Source;
  matches: ExposureMatch[];
  evidence: string[];
  action_memo: string;
};

export type ScanRun = {
  id: string;
  scan_type: string;
  status: string;
  started_at: string;
  finished_at: string | null;
  error_message: string | null;
  sources_found: number;
  signals_created: number;
  signals_updated: number;
  matches_created: number;
};

export type DashboardResponse = {
  catalog_summary: CatalogSummary;
  signals: RecallSignal[];
  scan_history: ScanRun[];
  meta: Record<string, unknown>;
};

export type CatalogResponse = {
  items: CatalogItem[];
};

export type ProductAssetResponse = {
  catalog_item_id: string;
  product_image_url: string | null;
  product_image_source_url: string | null;
  product_image_source_domain: string | null;
  status: string;
};

export type ManualScanResponse = {
  scan: ScanRun;
  signals: RecallSignal[];
  meta: Record<string, unknown>;
};

export type SupplierSource = {
  title: string | null;
  url: string;
  domain: string;
  image_url: string | null;
  favicon_url: string | null;
  highlights: unknown[];
};

export type SupplierLookupResponse = {
  query: string;
  details: Record<string, unknown>;
  sources: SupplierSource[];
  meta: Record<string, unknown>;
};

export type TriageTier = "confirmed_match" | "supplier_review" | "watch_only" | "no_exposure";
