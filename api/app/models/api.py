from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class CatalogItemOut(BaseModel):
    id: str
    sku: str
    brand: str
    product_name: str
    upc: str | None
    category: str
    supplier_name: str
    co_manufacturer_name: str | None
    ingredients: list[str]
    allergens: list[str]
    supplier_aliases: list[str]
    metadata: dict[str, Any]


class InventoryLotOut(BaseModel):
    id: str
    catalog_item_id: str
    store_id: str
    store_name: str
    city: str
    state: str
    latitude: float | None = None
    longitude: float | None = None
    lot_code: str | None
    quantity_on_hand: int
    last_seen_at: datetime


class CatalogSummaryOut(BaseModel):
    sku_count: int
    supplier_count: int
    store_count: int
    inventory_units: int


class ProductAssetOut(BaseModel):
    catalog_item_id: str
    product_image_url: str | None = None
    product_image_source_url: str | None = None
    product_image_source_domain: str | None = None
    status: str = "not_found"


class SourceOut(BaseModel):
    id: str
    canonical_url: str
    source_domain: str
    source_type: str
    title: str
    image_url: str | None = None
    favicon_url: str | None = None
    image_links: list[str] = Field(default_factory=list)
    published_at: datetime | None
    first_seen_at: datetime
    last_seen_at: datetime
    raw_exa_result: dict[str, Any] = Field(default_factory=dict)


class ExposureMatchOut(BaseModel):
    id: str
    catalog_item: CatalogItemOut
    tier: str
    match_type: str
    matched_fields: dict[str, Any]
    missing_fields: list[str]
    explanation: str
    recommended_action: str
    impacted_inventory: list[InventoryLotOut] = Field(default_factory=list)


class RecallSignalOut(BaseModel):
    id: str
    title: str
    company: str | None
    hazard_type: str
    hazard_description: str
    affected_products: list[dict[str, Any]]
    identifiers: dict[str, Any]
    supplier_chain: list[dict[str, Any]]
    retailers: list[str]
    distribution: dict[str, Any]
    explicit_exclusions: list[dict[str, Any]]
    event_date: date | None
    source: SourceOut
    matches: list[ExposureMatchOut]
    evidence: list[str]
    action_memo: str


class ScanRunOut(BaseModel):
    id: str
    scan_type: str
    status: str
    started_at: datetime
    finished_at: datetime | None
    error_message: str | None
    sources_found: int
    signals_created: int
    signals_updated: int
    matches_created: int


class DashboardResponse(BaseModel):
    catalog_summary: CatalogSummaryOut
    signals: list[RecallSignalOut]
    scan_history: list[ScanRunOut]
    meta: dict[str, Any]


class SupplierSourceOut(BaseModel):
    title: str | None = None
    url: str
    domain: str
    image_url: str | None = None
    favicon_url: str | None = None
    highlights: list[Any] = Field(default_factory=list)


class SupplierLookupResponse(BaseModel):
    query: str
    details: dict[str, Any] = Field(default_factory=dict)
    sources: list[SupplierSourceOut] = Field(default_factory=list)
    meta: dict[str, Any] = Field(default_factory=dict)


class ManualScanRequest(BaseModel):
    scan_type: Literal["recent_recalls"] = "recent_recalls"
    days: int = Field(default=365, ge=1, le=400)
    force_fresh: bool = False


class ManualScanResponse(BaseModel):
    scan: ScanRunOut
    signals: list[RecallSignalOut]
    meta: dict[str, Any]
