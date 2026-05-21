from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


TriageTier = Literal["confirmed_match", "supplier_review", "watch_only", "no_exposure"]


class CatalogItemDomain(BaseModel):
    id: str
    sku: str
    brand: str
    product_name: str
    upc: str | None = None
    category: str
    supplier_name: str
    co_manufacturer_name: str | None = None
    ingredients: list[str] = Field(default_factory=list)
    allergens: list[str] = Field(default_factory=list)
    supplier_aliases: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class InventoryLotDomain(BaseModel):
    id: str
    catalog_item_id: str
    store_id: str
    store_name: str
    city: str
    state: str
    lot_code: str | None = None
    quantity_on_hand: int
    last_seen_at: datetime


class NormalizedRecallSignal(BaseModel):
    title: str
    company: str | None = None
    hazard_type: str
    hazard_description: str
    affected_products: list[dict[str, Any]] = Field(default_factory=list)
    identifiers: dict[str, Any] = Field(default_factory=dict)
    supplier_chain: list[dict[str, Any]] = Field(default_factory=list)
    retailers: list[str] = Field(default_factory=list)
    distribution: dict[str, Any] = Field(default_factory=dict)
    explicit_exclusions: list[dict[str, Any]] = Field(default_factory=list)
    event_date: date | None = None
    raw_extraction: dict[str, Any] = Field(default_factory=dict)
    fingerprint: str


class MatchDecision(BaseModel):
    catalog_item_id: str
    tier: TriageTier
    match_type: str
    matched_fields: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    explanation: str
    recommended_action: str
