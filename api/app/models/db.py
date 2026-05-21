from datetime import date, datetime, timezone
from typing import Any

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


JsonDict = dict[str, Any]
JsonList = list[Any]


class Base(DeclarativeBase):
    pass


class Store(Base):
    __tablename__ = "stores"

    id: Mapped[str] = mapped_column(String(48), primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    state: Mapped[str] = mapped_column(String(2), nullable=False, index=True)
    city: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str] = mapped_column(String(80), nullable=False)
    latitude: Mapped[float | None] = mapped_column(Float)
    longitude: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class CatalogItem(Base):
    __tablename__ = "catalog_items"

    id: Mapped[str] = mapped_column(String(48), primary_key=True)
    sku: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    brand: Mapped[str] = mapped_column(String(160), index=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String(240), nullable=False)
    upc: Mapped[str | None] = mapped_column(String(64), index=True)
    category: Mapped[str] = mapped_column(String(120), nullable=False)
    supplier_name: Mapped[str] = mapped_column(String(180), index=True, nullable=False)
    co_manufacturer_name: Mapped[str | None] = mapped_column(String(180))
    ingredients_json: Mapped[JsonList] = mapped_column(JSON, default=list, nullable=False)
    allergens_json: Mapped[JsonList] = mapped_column(JSON, default=list, nullable=False)
    supplier_aliases_json: Mapped[JsonList] = mapped_column(JSON, default=list, nullable=False)
    metadata_json: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)


class InventoryLot(Base):
    __tablename__ = "inventory_lots"

    id: Mapped[str] = mapped_column(String(48), primary_key=True)
    catalog_item_id: Mapped[str] = mapped_column(ForeignKey("catalog_items.id"), index=True, nullable=False)
    store_id: Mapped[str] = mapped_column(ForeignKey("stores.id"), index=True, nullable=False)
    lot_code: Mapped[str | None] = mapped_column(String(80), index=True)
    quantity_on_hand: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    catalog_item: Mapped[CatalogItem] = relationship()
    store: Mapped[Store] = relationship()


class ExternalSource(Base):
    __tablename__ = "external_sources"

    id: Mapped[str] = mapped_column(String(48), primary_key=True)
    canonical_url: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    source_domain: Mapped[str] = mapped_column(String(180), index=True, nullable=False)
    source_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), index=True)
    first_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True)
    raw_exa_result_json: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)


class RecallSignal(Base):
    __tablename__ = "recall_signals"

    id: Mapped[str] = mapped_column(String(48), primary_key=True)
    source_id: Mapped[str] = mapped_column(ForeignKey("external_sources.id"), index=True, nullable=False)
    fingerprint: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    company: Mapped[str | None] = mapped_column(String(180))
    hazard_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    hazard_description: Mapped[str] = mapped_column(Text, nullable=False)
    affected_products_json: Mapped[JsonList] = mapped_column(JSON, default=list, nullable=False)
    identifiers_json: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    supplier_chain_json: Mapped[JsonList] = mapped_column(JSON, default=list, nullable=False)
    retailers_json: Mapped[JsonList] = mapped_column(JSON, default=list, nullable=False)
    distribution_json: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    explicit_exclusions_json: Mapped[JsonList] = mapped_column(JSON, default=list, nullable=False)
    event_date: Mapped[date | None] = mapped_column(Date, index=True)
    raw_extraction_json: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    source: Mapped[ExternalSource] = relationship()


class ExposureMatch(Base):
    __tablename__ = "exposure_matches"
    __table_args__ = (UniqueConstraint("recall_signal_id", "catalog_item_id", "match_type"),)

    id: Mapped[str] = mapped_column(String(48), primary_key=True)
    recall_signal_id: Mapped[str] = mapped_column(ForeignKey("recall_signals.id"), index=True, nullable=False)
    catalog_item_id: Mapped[str] = mapped_column(ForeignKey("catalog_items.id"), index=True, nullable=False)
    tier: Mapped[str] = mapped_column(String(40), index=True, nullable=False)
    match_type: Mapped[str] = mapped_column(String(80), nullable=False)
    matched_fields_json: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    missing_fields_json: Mapped[JsonList] = mapped_column(JSON, default=list, nullable=False)
    explanation: Mapped[str] = mapped_column(Text, nullable=False)
    recommended_action: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)

    catalog_item: Mapped[CatalogItem] = relationship()
    signal: Mapped[RecallSignal] = relationship()


class ScanRun(Base):
    __tablename__ = "scan_runs"

    id: Mapped[str] = mapped_column(String(48), primary_key=True)
    scan_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(60), index=True, nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(180), unique=True)
    query_version: Mapped[str] = mapped_column(String(40), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    error_message: Mapped[str | None] = mapped_column(Text)
    sources_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    signals_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    signals_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    matches_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


class JobLock(Base):
    __tablename__ = "job_locks"

    name: Mapped[str] = mapped_column(String(120), primary_key=True)
    owner_id: Mapped[str] = mapped_column(String(80), nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)


class IdempotencyKey(Base):
    __tablename__ = "idempotency_keys"

    key: Mapped[str] = mapped_column(String(180), primary_key=True)
    request_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    response_json: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    status_code: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)


class SupplierProfile(Base):
    __tablename__ = "supplier_profiles"

    normalized_name: Mapped[str] = mapped_column(String(180), primary_key=True)
    display_name: Mapped[str] = mapped_column(String(180), nullable=False)
    details_json: Mapped[JsonDict] = mapped_column(JSON, default=dict, nullable=False)
    sources_json: Mapped[JsonList] = mapped_column(JSON, default=list, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)
