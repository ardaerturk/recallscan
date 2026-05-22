"use client";

import {
  ExternalLink,
  Loader2,
  PackageSearch,
  Phone,
  RefreshCw,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";

import { getDashboard, getProductAsset, lookupSupplier, runManualScan } from "@/lib/api-client";
import { compactNumber, formatDate, formatTime, listValue, tierLabels, tierTone, titleCase } from "@/lib/formatters";
import type {
  CatalogItem,
  DashboardResponse,
  ExposureMatch,
  RecallSignal,
  SupplierLookupResponse,
  TriageTier,
} from "@/lib/types";

const LOOKBACK_DAYS = 365;

type DrawerTab = "overview" | "locate" | "supplier" | "source";
type QueueView = "action" | "watch";
type AlertItem = {
  id: string;
  signal: RecallSignal;
  match: ExposureMatch;
};

export function Dashboard() {
  const [dashboard, setDashboard] = useState<DashboardResponse | null>(null);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [tab, setTab] = useState<DrawerTab>("overview");
  const [queueView, setQueueView] = useState<QueueView>("action");
  const [loading, setLoading] = useState(true);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setError(null);
    const dash = await getDashboard(LOOKBACK_DAYS);
    setDashboard(dash);
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect -- initial API hydration happens after mount.
    load()
      .catch((reason: Error) => setError(reason.message))
      .finally(() => setLoading(false));
    const timer = window.setInterval(() => {
      load().catch(() => undefined);
    }, 30_000);
    return () => window.clearInterval(timer);
  }, [load]);

  const liveSignals = useMemo(() => dashboard?.signals ?? [], [dashboard]);
  const actionItems = useMemo(() => buildQueueItems(liveSignals, "action"), [liveSignals]);
  const actionSkus = useMemo(() => new Set(actionItems.map((item) => item.match.catalog_item.sku)), [actionItems]);
  const watchItems = useMemo(() => buildQueueItems(liveSignals, "watch", actionSkus), [actionSkus, liveSignals]);
  const reviewCount = actionItems.length;
  const lastScan = useMemo(() => latestCompletedScan(dashboard), [dashboard]);

  const visibleItems = queueView === "action" ? actionItems : watchItems;
  const allItems = useMemo(() => [...actionItems, ...watchItems], [actionItems, watchItems]);
  const selected = useMemo(
    () =>
      findAlertItem(visibleItems, selectedId) ??
      firstAlertItem(visibleItems) ??
      findAlertItem(allItems, selectedId) ??
      firstAlertItem(allItems) ??
      null,
    [allItems, selectedId, visibleItems],
  );
  async function handleScan(forceFresh = false) {
    setScanning(true);
    setError(null);
    try {
      await runManualScan(forceFresh);
      await load();
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Scan failed");
    } finally {
      setScanning(false);
    }
  }

  if (loading) {
    return (
      <main className="flex min-h-svh items-center justify-center bg-[#090909] text-zinc-100">
        <div className="flex items-center gap-3 text-sm text-zinc-400">
          <Loader2 className="size-4 animate-spin" />
          Loading RecallScan
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-svh bg-[#090909] text-zinc-100 lg:h-svh lg:overflow-hidden">
      <div className="mx-auto flex min-h-svh w-full max-w-[1280px] flex-col gap-6 px-4 py-5 sm:px-6 lg:h-full lg:min-h-0 lg:px-8">
        <header className="flex flex-col gap-5 border-b border-white/10 pb-5 lg:flex-row lg:items-start lg:justify-between">
          <div className="max-w-2xl">
            <div className="flex items-center gap-3">
              <div className="flex size-9 items-center justify-center rounded-md bg-white text-black">
                <PackageSearch className="size-4" />
              </div>
              <div>
                <h1 className="text-2xl font-semibold tracking-normal text-white">RecallScan</h1>
                <p className="text-sm text-zinc-500">Recall monitoring for your stores.</p>
              </div>
            </div>
            <h2 className="mt-6 max-w-xl text-3xl font-semibold tracking-normal text-white sm:text-4xl">
              {error ? "Unable to load recall data." : reviewCount > 0 ? reviewHeadline(reviewCount) : "All clear. Nothing needs attention."}
            </h2>
          </div>

          <div className="flex flex-wrap items-center gap-3 lg:pt-1">
            {lastScan ? <p className="text-xs text-zinc-600">Last scanned {formatTime(lastScan)}</p> : null}
            <button
              onClick={() => void handleScan(false)}
              disabled={scanning}
              className="inline-flex h-10 items-center gap-2 rounded-md bg-white px-3 text-sm font-medium text-black transition hover:bg-zinc-200 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {scanning ? <Loader2 className="size-4 animate-spin" /> : <RefreshCw className="size-4" />}
              Scan
            </button>
          </div>
        </header>

        {error ? (
          <div className="rounded-md border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
            {error}
          </div>
        ) : null}

        <section className="grid gap-6 lg:min-h-0 lg:flex-1 lg:grid-cols-[360px_minmax(0,1fr)]">
          <SignalQueue
            view={queueView}
            setView={setQueueView}
            items={visibleItems}
            selectedId={selected?.id ?? null}
            counts={{
              action: actionItems.length,
              watch: watchItems.length,
            }}
            onSelect={(item) => {
              setSelectedId(item.id);
              setTab("overview");
            }}
          />

          <EvidenceDrawer alert={selected} tab={tab} setTab={setTab} />
        </section>
      </div>
    </main>
  );
}

function SignalQueue({
  view,
  setView,
  items,
  selectedId,
  counts,
  onSelect,
}: {
  view: QueueView;
  setView: (view: QueueView) => void;
  items: AlertItem[];
  selectedId: string | null;
  counts: Record<QueueView, number>;
  onSelect: (item: AlertItem) => void;
}) {
  const tabs: { key: QueueView; label: string }[] = [
    { key: "action", label: "Action needed" },
    { key: "watch", label: "Monitoring" },
  ];

  return (
    <section className="flex min-h-0 flex-col rounded-lg border border-white/10 bg-[#101010]">
      <div className="border-b border-white/10 px-4 py-3">
        <div className="grid grid-cols-2 gap-1 rounded-md bg-black/30 p-1">
          {tabs.map((item) => (
            <button
              key={item.key}
              onClick={() => setView(item.key)}
              className={`flex items-center justify-center gap-2 rounded px-2 py-2 text-center transition ${
                view === item.key ? "bg-white text-black" : "text-zinc-400 hover:text-white"
              }`}
            >
              <span className="text-sm font-medium">{item.label}</span>
              <span className={`text-xs ${view === item.key ? "text-black/50" : "text-zinc-600"}`}>{counts[item.key]}</span>
            </button>
          ))}
        </div>
      </div>

      <div className="min-h-0 overflow-y-auto">
        {items.length ? (
          items.map((item) => (
            <ProductQueueRow
              key={item.id}
              item={item}
              selected={item.id === selectedId}
              onSelect={() => onSelect(item)}
            />
          ))
        ) : (
          <QueueEmpty view={view} />
        )}
      </div>
    </section>
  );
}

function ProductQueueRow({ item, selected, onSelect }: { item: AlertItem; selected: boolean; onSelect: () => void }) {
  const { signal, match } = item;
  return (
    <button
      onClick={onSelect}
      className={`w-full border-b border-white/5 px-4 py-4 text-left transition last:border-0 ${
        selected ? "bg-white/[0.07]" : "hover:bg-white/[0.035]"
      }`}
    >
      <div className="flex items-center justify-between gap-3">
        <span className={`rounded-md border px-2 py-1 text-xs ${tierTone[match.tier]}`}>
          {tierLabels[match.tier]}
        </span>
        <span className="shrink-0 text-xs text-zinc-600">{formatDate(signal.event_date)}</span>
      </div>
      <h3 className="mt-2 line-clamp-2 text-sm font-medium leading-5 text-zinc-100">
        {catalogItemName(match.catalog_item)}
      </h3>
      <p className="mt-1 truncate text-xs text-zinc-600">SKU {match.catalog_item.sku}</p>
    </button>
  );
}

function QueueEmpty({ view }: { view: QueueView }) {
  const copy: Record<QueueView, { title: string; body: string }> = {
    action: {
      title: "All clear",
      body: `No recall notices from the last ${LOOKBACK_DAYS} days matched your products.`,
    },
    watch: {
      title: "Nothing to monitor",
      body: "Possible matches will appear here as new notices come in.",
    },
  };
  return (
    <div className="px-4 py-10 text-sm">
      <p className="font-medium text-zinc-200">{copy[view].title}</p>
      <p className="mt-2 leading-6 text-zinc-500">{copy[view].body}</p>
    </div>
  );
}

function EvidenceDrawer({
  alert,
  tab,
  setTab,
}: {
  alert: AlertItem | null;
  tab: DrawerTab;
  setTab: (tab: DrawerTab) => void;
}) {
  const catalogItemId = alert?.match.catalog_item.id ?? "";
  const [assetImage, setAssetImage] = useState<{ catalogItemId: string; url: string } | null>(null);
  const [failedImages, setFailedImages] = useState<Set<string>>(() => new Set());

  useEffect(() => {
    if (!catalogItemId) return;

    let cancelled = false;
    getProductAsset(catalogItemId)
      .then((asset) => {
        if (!cancelled && asset.product_image_url && isProductImageCandidate(asset.product_image_url)) {
          setAssetImage({ catalogItemId, url: asset.product_image_url });
        }
      })
      .catch(() => undefined);
    return () => {
      cancelled = true;
    };
  }, [catalogItemId]);

  if (!alert) {
    return (
      <section className="flex min-h-[620px] items-center justify-center rounded-lg border border-white/10 bg-[#101010] p-6 text-sm text-zinc-500">
        Select a product to see details.
      </section>
    );
  }

  const { signal, match } = alert;
  const asyncProductImage = assetImage?.catalogItemId === catalogItemId ? assetImage.url : "";
  const productImage = asyncProductImage || productImageForAlert(alert);
  const productImageKey = `${catalogItemId}:${productImage}`;
  const showProductImage = productImage && !failedImages.has(productImageKey);
  const tabs: { key: DrawerTab; label: string }[] = [
    { key: "overview", label: "Overview" },
    { key: "locate", label: "Locate" },
    { key: "supplier", label: "Supplier" },
    { key: "source", label: "Source" },
  ];

  return (
    <section className="flex min-h-[620px] flex-col overflow-hidden rounded-lg border border-white/10 bg-[#101010] lg:min-h-0">
      <div className="border-b border-white/10 px-5 py-5">
        <div className="flex items-start justify-between gap-4">
          <div className="flex min-w-0 gap-4">
            <div className="hidden size-16 shrink-0 overflow-hidden rounded-lg border border-white/10 bg-white/[0.03] sm:block">
              {showProductImage ? (
                // eslint-disable-next-line @next/next/no-img-element -- product images are catalog metadata and unknown at build time.
                <img
                  src={productImage}
                  alt=""
                  className="size-full object-cover"
                  onError={() => {
                    setFailedImages((current) => new Set(current).add(productImageKey));
                  }}
                />
              ) : (
                <div className="flex size-full items-center justify-center text-zinc-600">
                  <PackageSearch className="size-5" />
                </div>
              )}
            </div>
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-2">
                <span className={`rounded-md border px-2 py-1 text-xs ${tierTone[match.tier]}`}>
                  {tierLabels[match.tier]}
                </span>
              </div>
              <h2 className="mt-4 max-w-3xl text-2xl font-semibold tracking-normal text-white">{catalogItemName(match.catalog_item)}</h2>
            </div>
          </div>
          {isExternalUrl(signal.source.canonical_url) ? (
            <a
              href={signal.source.canonical_url}
              target="_blank"
              rel="noreferrer"
              className="shrink-0 rounded-md border border-white/10 p-2 text-zinc-400 transition hover:text-white"
              aria-label="Open source"
            >
              <ExternalLink className="size-4" />
            </a>
          ) : null}
        </div>

        <div className="mt-5 grid gap-3 sm:grid-cols-4">
          <SignalFact label="Issue" value={titleCase(signal.hazard_type)} />
          <SignalFact label="SKU" value={match.catalog_item.sku} />
          <SignalFact label="Units at risk" value={compactNumber(matchImpactedUnits(match))} />
          <SignalFact label="Source" value={signal.source.source_domain} />
        </div>

        <div className="mt-5 flex flex-wrap gap-2">
          {tabs.map((item) => (
            <button
              key={item.key}
              onClick={() => setTab(item.key)}
              className={`rounded-md px-3 py-1.5 text-xs transition ${
                tab === item.key ? "bg-white text-black" : "border border-white/10 text-zinc-400 hover:text-white"
              }`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      <div className="min-h-0 overflow-y-auto p-5">
        {tab === "overview" ? <OverviewTab alert={alert} /> : null}
        {tab === "locate" ? <LocateTab alert={alert} /> : null}
        {tab === "supplier" ? <SupplierTab alert={alert} /> : null}
        {tab === "source" ? <SourceTab alert={alert} /> : null}
      </div>
    </section>
  );
}

function SignalFact({ label, value }: { label: string; value: string }) {
  return (
    <div className="border-l border-white/10 pl-3">
      <p className="text-xs text-zinc-500">{label}</p>
      <p className="mt-1 truncate text-sm text-zinc-100">{value || "Unknown"}</p>
    </div>
  );
}

function OverviewTab({ alert }: { alert: AlertItem }) {
  const facts = overviewFacts(alert);
  const steps = trackSteps(alert);
  const evidence = bestEvidence(alert);
  return (
    <div className="space-y-7">
      {facts.length ? (
        <dl className="grid gap-x-6 gap-y-3 sm:grid-cols-2">
          {facts.map(([label, value]) => (
            <div key={label} className="grid grid-cols-[92px_1fr] gap-3 text-sm">
              <dt className="text-zinc-500">{label}</dt>
              <dd className="break-words text-zinc-200">{value}</dd>
            </div>
          ))}
        </dl>
      ) : null}

      {steps.length ? (
        <section>
          <h3 className="text-sm font-medium text-white">Exposure path</h3>
          <ol className="mt-4 space-y-3">
            {steps.map((step, index) => (
              <TrackStep key={`${step.label}-${index}`} step={step} isLast={index === steps.length - 1} />
            ))}
          </ol>
        </section>
      ) : null}

      <section>
        <h3 className="text-sm font-medium text-white">Source note</h3>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-300">{supervisorSourceNote(alert)}</p>
        {evidence ? (
          <p className="mt-3 border-l border-white/10 pl-4 text-sm leading-6 text-zinc-500">
            {truncateText(evidenceExcerpt(alert, evidence), 180)}
          </p>
        ) : null}
      </section>
    </div>
  );
}

function TrackStep({ step, isLast }: { step: TrackStepData; isLast: boolean }) {
  return (
    <li className="grid grid-cols-[22px_1fr] gap-3">
      <div className="flex flex-col items-center">
        <span className={`mt-1 size-2.5 rounded-full ${step.tone}`} />
        {!isLast ? <span className="mt-2 h-full min-h-8 w-px bg-white/10" /> : null}
      </div>
      <div className="pb-2">
        <p className="text-xs text-zinc-500">{step.label}</p>
        <p className="mt-1 text-sm font-medium text-zinc-100">{step.value}</p>
        {step.detail ? <p className="mt-1 text-sm leading-5 text-zinc-500">{step.detail}</p> : null}
      </div>
    </li>
  );
}

function LocateTab({ alert }: { alert: AlertItem }) {
  const { match } = alert;
  if (!match.impacted_inventory.length) {
    return (
      <div className="max-w-xl text-sm leading-6 text-zinc-500">
        No store inventory is currently tied to this product.
      </div>
    );
  }

  return (
    <div className="grid gap-3 lg:grid-cols-2">
      {match.impacted_inventory.map((lot) => (
        <StoreLocation key={lot.id} lot={lot} />
      ))}
    </div>
  );
}

function StoreLocation({ lot }: { lot: ExposureMatch["impacted_inventory"][number] }) {
  return (
    <section className="overflow-hidden rounded-md border border-white/10 bg-white/[0.025]">
      {lot.latitude != null && lot.longitude != null ? (
        <iframe
          title={`${lot.store_name} map`}
          src={openStreetMapEmbedUrl(lot.latitude, lot.longitude)}
          className="h-44 w-full border-0 grayscale invert"
          loading="lazy"
        />
      ) : (
        <div className="flex h-44 items-center justify-center bg-black/30 text-sm text-zinc-600">Map unavailable</div>
      )}
      <div className="p-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <h3 className="truncate text-sm font-medium text-white">{lot.store_name}</h3>
            <p className="mt-1 text-xs text-zinc-500">
              {lot.city}, {lot.state}{lot.lot_code ? ` · Lot ${lot.lot_code}` : ""}
            </p>
          </div>
          <span className="shrink-0 text-sm text-zinc-200">{lot.quantity_on_hand} units</span>
        </div>
        <button
          type="button"
          className="mt-4 inline-flex h-8 items-center gap-2 rounded-md border border-white/10 px-3 text-xs text-zinc-300 transition hover:bg-white/[0.05] hover:text-white"
        >
          <Phone className="size-3" />
          Call store
        </button>
      </div>
    </section>
  );
}

function openStreetMapEmbedUrl(latitude: number, longitude: number) {
  const delta = 0.01;
  const params = new URLSearchParams({
    bbox: [
      (longitude - delta).toFixed(5),
      (latitude - delta).toFixed(5),
      (longitude + delta).toFixed(5),
      (latitude + delta).toFixed(5),
    ].join(","),
    layer: "mapnik",
    marker: `${latitude.toFixed(5)},${longitude.toFixed(5)}`,
  });
  return `https://www.openstreetmap.org/export/embed.html?${params.toString()}`;
}

function SupplierTab({ alert }: { alert: AlertItem }) {
  const suppliers = supplierCompanies(alert);
  const primarySupplier = suppliers[0]?.name ?? "";
  const [lookup, setLookup] = useState<SupplierLookupResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!primarySupplier) return;
    let cancelled = false;
    async function runLookup() {
      setLoading(true);
      setError(null);
      try {
        const result = await lookupSupplier(primarySupplier);
        if (!cancelled) setLookup(result);
      } catch (reason) {
        if (!cancelled) setError(reason instanceof Error ? reason.message : "Supplier lookup failed");
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void runLookup();
    return () => {
      cancelled = true;
    };
  }, [primarySupplier]);

  if (!suppliers.length) {
    return <p className="text-sm text-zinc-500">No supplier was identified in the recall notice or catalog match.</p>;
  }

  const activeLookup = lookup?.query === primarySupplier ? lookup : null;
  const details = activeLookup?.details ?? {};
  const supplierLogo = supplierLogoForDetails(details);
  return (
    <div className="space-y-7">
      <section>
        <h3 className="text-sm font-medium text-white">Suppliers</h3>
        <div className="mt-3 divide-y divide-white/10">
          {suppliers.map((supplier) => (
            <div key={`${supplier.name}-${supplier.role}`} className="py-3 first:pt-0 last:pb-0">
              <p className="text-sm font-medium text-zinc-100">{supplier.name}</p>
              <p className="mt-1 text-xs text-zinc-500">{supplier.role || "Catalog supplier"}</p>
            </div>
          ))}
        </div>
      </section>

      <section>
        <h3 className="text-sm font-medium text-white">Contact</h3>
        {loading ? (
          <div className="mt-3 flex items-center gap-2 text-sm text-zinc-500">
            <Loader2 className="size-4 animate-spin" />
            Looking up supplier details with Exa
          </div>
        ) : error ? (
          <p className="mt-3 text-sm text-zinc-500">Supplier lookup failed.</p>
        ) : (
          <div className="mt-3 flex gap-4">
            {supplierLogo ? (
              <div className="flex size-12 shrink-0 items-center justify-center overflow-hidden rounded-md border border-white/10 bg-white">
                {/* eslint-disable-next-line @next/next/no-img-element -- logo metadata comes from Exa search results. */}
                <img src={supplierLogo} alt="" className="max-h-9 max-w-9 object-contain" />
              </div>
            ) : null}
            <dl className="grid flex-1 gap-x-6 gap-y-3 sm:grid-cols-2">
              <SupplierDetail label="Company" value={detailString(details.company_name) || primarySupplier} />
              <SupplierDetail label="Phone" value={detailString(details.phone)} />
              <SupplierDetail label="Email" value={detailString(details.email)} />
              <SupplierDetail label="Address" value={detailString(details.address)} />
              <SupplierDetail label="Quality" value={detailString(details.recall_or_quality_contact)} />
              <SupplierDetail label="Website" value={detailString(details.website)} link />
            </dl>
          </div>
        )}
      </section>

      {detailString(details.notes) ? (
        <section>
          <h3 className="text-sm font-medium text-white">Note</h3>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-500">{detailString(details.notes)}</p>
        </section>
      ) : null}

      {activeLookup?.sources.length ? (
        <section>
          <h3 className="text-sm font-medium text-white">Sources</h3>
          <div className="mt-3 space-y-2">
            {activeLookup.sources.slice(0, 3).map((source) => (
              <a
                key={source.url}
                href={source.url}
                target="_blank"
                rel="noreferrer"
                className="block rounded-md border border-white/10 px-3 py-2 text-sm text-zinc-300 transition hover:bg-white/[0.04] hover:text-white"
              >
                <span className="flex min-w-0 items-center gap-2">
                  <span className="block truncate">{source.title || source.domain}</span>
                </span>
                <span className="mt-1 block text-xs text-zinc-600">{source.domain}</span>
              </a>
            ))}
          </div>
        </section>
      ) : null}
    </div>
  );
}

function SupplierDetail({ label, value, link = false }: { label: string; value: string; link?: boolean }) {
  const href = link && value && isExternalUrl(value) ? value : null;
  return (
    <div className="grid grid-cols-[76px_1fr] gap-3 text-sm">
      <dt className="text-zinc-500">{label}</dt>
      <dd className="break-words text-zinc-200">
        {href ? (
          <a href={href} target="_blank" rel="noreferrer" className="text-zinc-100 underline decoration-white/20 underline-offset-4">
            {value}
          </a>
        ) : (
          value || "Unknown"
        )}
      </dd>
    </div>
  );
}

function SourceTab({ alert }: { alert: AlertItem }) {
  const { signal } = alert;
  const evidence = bestEvidence(alert);
  return (
    <div className="max-w-3xl space-y-6">
      <section>
        <h3 className="text-sm font-medium text-white">Source highlight</h3>
        <p className="mt-3 max-w-2xl text-sm leading-6 text-zinc-300">{sourceHighlight(alert)}</p>
        {evidence ? (
          <p className="mt-3 border-l border-white/10 pl-4 text-sm leading-6 text-zinc-500">
            {truncateText(evidenceExcerpt(alert, evidence), 260)}
          </p>
        ) : null}
      </section>

      <dl className="grid gap-3 text-sm sm:grid-cols-3">
        <SourceRow label="Source" value={signal.source.source_domain} />
        <SourceRow label="Published" value={formatDate(signal.source.published_at)} />
        <SourceRow label="Type" value={titleCase(signal.source.source_type)} />
      </dl>

      {isExternalUrl(signal.source.canonical_url) ? (
        <a
          href={signal.source.canonical_url}
          target="_blank"
          rel="noreferrer"
          className="inline-flex h-9 items-center rounded-md border border-white/10 px-3 text-sm text-zinc-200 transition hover:bg-white/[0.05] hover:text-white"
        >
          Open source
        </a>
      ) : null}

      {signal.explicit_exclusions.length ? (
        <section className="rounded-md border border-emerald-500/20 bg-emerald-500/10 p-4">
          <p className="text-xs uppercase tracking-normal text-emerald-200">Excluded from this recall</p>
          <ul className="mt-2 space-y-2 text-sm text-emerald-100">
            {signal.explicit_exclusions.map((item, index) => (
              <li key={index}>{String(item.text ?? JSON.stringify(item))}</li>
            ))}
          </ul>
        </section>
      ) : null}
    </div>
  );
}

function SourceRow({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-zinc-500">{label}</dt>
      <dd className="mt-1 break-words text-zinc-200">{value}</dd>
    </div>
  );
}

type TrackStepData = {
  label: string;
  value: string;
  detail?: string;
  tone: string;
};

function buildQueueItems(signals: RecallSignal[], view: QueueView, excludedSkus = new Set<string>()) {
  const bySku = new Map<string, AlertItem>();
  for (const signal of signals) {
    for (const match of signal.matches) {
      const inView =
        view === "action" ? match.tier === "confirmed_match" || match.tier === "supplier_review" : match.tier === "watch_only";
      if (!inView || excludedSkus.has(match.catalog_item.sku)) continue;

      const item = { id: alertItemId(signal, match), signal, match };
      const current = bySku.get(match.catalog_item.sku);
      if (!current || compareAlertItems(item, current) < 0) {
        bySku.set(match.catalog_item.sku, item);
      }
    }
  }
  return Array.from(bySku.values()).sort(compareAlertItems);
}

function compareAlertItems(left: AlertItem, right: AlertItem) {
  const tierDelta = TIER_RANK[left.match.tier] - TIER_RANK[right.match.tier];
  if (tierDelta) return tierDelta;
  const sourceDelta = sourcePriority(left.signal) - sourcePriority(right.signal);
  if (sourceDelta) return sourceDelta;
  const dateDelta = dateValue(right.signal.event_date) - dateValue(left.signal.event_date);
  if (dateDelta) return dateDelta;
  return catalogItemName(left.match.catalog_item).localeCompare(catalogItemName(right.match.catalog_item));
}

function sourcePriority(signal: RecallSignal) {
  const { source_type: sourceType, source_domain: domain } = signal.source;
  if (sourceType === "official_recall") return 0;
  if (sourceType === "public_health_alert") return 1;
  if (sourceType === "direct_recall_notice" && isPressReleaseDomain(domain)) return 2;
  if (sourceType === "direct_recall_notice") return 3;
  if (sourceType === "outbreak_update") return 5;
  if (/(^|\.)fda\.gov$/i.test(domain)) return 0;
  if (/(^|\.)fsis\.usda\.gov$/i.test(domain)) return 1;
  if (/(^|\.)cdc\.gov$/i.test(domain)) return 6;
  if (/(^|\.)foodsafety\.gov$/i.test(domain)) return 3;
  return 4;
}

function latestCompletedScan(dashboard: DashboardResponse | null) {
  const scan = dashboard?.scan_history.find((item) => item.status === "completed") ?? dashboard?.scan_history[0];
  return scan?.finished_at ?? scan?.started_at ?? null;
}

function isPressReleaseDomain(domain: string) {
  return /(^|\.)((prnewswire|einpresswire)\.com|finance\.yahoo\.com)$/i.test(domain);
}

function dateValue(value: string | null) {
  return value ? Date.parse(value) || 0 : 0;
}

function compactKey(value: string) {
  return value.toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function alertItemId(signal: RecallSignal, match?: ExposureMatch) {
  return match ? `${signal.id}:${match.id}` : signal.id;
}

function findAlertItem(items: AlertItem[], selectedId: string | null) {
  if (!selectedId) return null;
  return items.find((candidate) => candidate.id === selectedId) ?? null;
}

function firstAlertItem(items: AlertItem[]) {
  return items[0] ?? null;
}

function reviewHeadline(count: number) {
  return `${count} product${count === 1 ? " needs" : "s need"} your attention.`;
}

function displaySignalTitle(signal: RecallSignal) {
  const confirmed = primaryConfirmedProductName(signal);
  if (confirmed) return confirmed;

  const titleProduct = productFromRecallTitle(signal.title);
  if (titleProduct && isUsefulProductName(titleProduct)) return titleProduct;

  const affected = affectedProductName(signal);
  if (affected && isUsefulProductName(affected) && !looksLikeHeadline(affected)) return affected;

  const matched = matchedProductName(signal);
  if (matched) return matched;

  return cleanNewsTitle(affected || signal.title);
}

function productFromRecallTitle(title: string) {
  let value = title.split("|")[0]?.trim() ?? "";
  value = value.replace(/^(fds issue|fda warns?|usda|cdc)\s+/i, "").trim();
  const recallsPattern = value.match(/^(.+?)\s+recalls?\s+(.+?)(?:\s+over\b|\s+due\b|\s+because\b|,|:|\s+[–—-]\s+|$)/i);
  if (recallsPattern && !startsWithNewsVerb(recallsPattern[2])) {
    const candidate = cleanProductCandidate(`${recallsPattern[1]} ${recallsPattern[2]}`);
    if (candidate.split(/\s+/).length >= 2) return candidate;
  }
  const recallIndex = value.search(/\brecall(?:s|ed|ing)?\b/i);
  if (recallIndex <= 0) return null;
  value = value.slice(0, recallIndex).replace(/[:\-–—]+$/g, "").trim();
  value = cleanProductCandidate(value);
  return value.split(/\s+/).length >= 2 ? value : null;
}

function affectedProductName(signal: RecallSignal) {
  const product = signal.affected_products.find((item) => stringValue(item.product_name) || stringValue(item.name));
  if (!product) return null;
  return cleanProductCandidate(
    [stringValue(product.brand), stringValue(product.product_name ?? product.name)].filter(Boolean).join(" "),
  );
}

function primaryConfirmedProductName(signal: RecallSignal) {
  const match = signal.matches.find((item) => item.tier === "confirmed_match");
  return match ? catalogItemName(match.catalog_item) : null;
}

function matchedProductName(signal: RecallSignal) {
  const item = signal.matches[0]?.catalog_item;
  return item ? stripSize(`${item.brand} ${item.product_name}`) : null;
}

function cleanNewsTitle(title: string) {
  const value = title.split("|")[0]?.trim() || title;
  const afterPattern = value.match(/\bafter\s+(?:the\s+)?(.+?)\s+linked\s+to\b/i);
  if (afterPattern) return cleanProductCandidate(titleCase(afterPattern[1]));
  return cleanProductCandidate(value.split(":")[0]?.trim() || value);
}

function cleanProductCandidate(value: string) {
  let stripped = stripSize(value)
    .split("|")[0]
    .replace(/^(fds issue|fda warns?|usda|cdc)\s+/i, "")
    .replace(/^\s*the\s+/i, "")
    .trim();

  const afterPattern = stripped.match(/^what to check after\s+(?:the\s+)?(.+)$/i);
  if (afterPattern) return cleanProductCandidate(afterPattern[1]);
  const riskFromPattern = stripped.match(/\brisk from\s+(.+?)(?:[:\-–—]|$)/i);
  if (riskFromPattern) return cleanProductCandidate(riskFromPattern[1]);
  stripped = stripped.replace(/\s+(?:linked\s+to|tied\s+to)\b.*$/i, "");

  return stripped
    .replace(
      /\s+(?:sparks?|fears?|warning|warns?|after|across|about|over|due\s+to|because)\b.*$/i,
      "",
    )
    .replace(/\s+(?:cascade|fallout)\b.*$/i, "")
    .trim();
}

function isGenericProductTitle(value: string) {
  return /^(major product|product safety signal|recall notice)$/i.test(value.trim());
}

function isUsefulProductName(value: string) {
  const words = value.split(/\s+/).filter(Boolean);
  if (isGenericProductTitle(value)) return false;
  if (words.length < 2) return false;
  return true;
}

function startsWithNewsVerb(value: string) {
  return /^(and|sparks?|fears?|warning|warns?|after|across|about|linked\s+to|tied\s+to|over|due\s+to|because|cascade|fallout)\b/i.test(
    value.trim(),
  );
}

function stripSize(value: string) {
  return value
    .replace(/\b\d+(?:\.\d+)?\s?(?:oz|ounce|ounces|lb|lbs|g|kg|ml|ct|count|pack|bags?)\b/gi, "")
    .replace(/\s{2,}/g, " ")
    .trim();
}

function overviewFacts(alert: AlertItem) {
  const { signal, match } = alert;
  const impactedStores = matchImpactedStoreNames(match);
  const units = matchImpactedUnits(match);
  const facts = [
    ["Product", catalogItemName(match.catalog_item)],
    ["Issue", titleCase(signal.hazard_type)],
    ["Supplier", supplierSummary(alert)],
    ["Store impact", units ? `${compactNumber(units)} units across ${impactedStores.length} store${impactedStores.length === 1 ? "" : "s"}` : ""],
    ["SKU", match.catalog_item.sku],
    ["UPC", match.catalog_item.upc ?? ""],
    ["Lots", listValue(signal.identifiers.lot_codes)],
    ["States", listValue(signal.distribution.states)],
  ];
  return facts.filter(([, value]) => value && value !== "None");
}

function supervisorSourceNote(alert: AlertItem) {
  const { signal, match } = alert;
  const product = catalogItemName(match.catalog_item);
  const hazard = titleCase(signal.hazard_type);
  const lots = listValue(signal.identifiers.lot_codes);

  if (match.tier === "confirmed_match") {
    const scope = lots !== "None" ? `lot ${lots}` : "";
    return `${product} is named in a ${hazard.toLowerCase()} recall. ${
      scope ? `Check ${scope} in affected stores.` : "Pull the affected store inventory from Locate."
    }`;
  }

  if (match.tier === "supplier_review") {
    return `${product} may be connected through a supplier, manufacturer, or upstream ingredient. Confirm lot and facility exposure before pulling product.`;
  }

  if (match.tier === "watch_only") {
    return `${product} is related by ingredient, category, or geography. No matching UPC, lot, or supplier path is confirmed yet.`;
  }

  return `${product} appears to be excluded from this recall. Keep the source on file for audit history.`;
}

function sourceHighlight(alert: AlertItem) {
  const { signal, match } = alert;
  const product = catalogItemName(match.catalog_item);
  const hazard = titleCase(signal.hazard_type).toLowerCase();

  if (match.tier === "confirmed_match") {
    return `${product} is named in a ${hazard} recall.`;
  }

  if (match.tier === "supplier_review") {
    return `${product} may be connected through a supplier, manufacturer, or upstream ingredient. Supplier lot and facility confirmation are still needed.`;
  }

  if (match.tier === "watch_only") {
    return `This notice is related to ${product}, but it does not confirm a matching product, UPC, lot, or supplier path.`;
  }

  return `${product} appears to be excluded from the affected product list.`;
}

function bestEvidence(alert: AlertItem) {
  const keywords = evidenceKeywords(alert);
  let best = "";
  let bestScore = 0;
  for (const item of alert.signal.evidence) {
    const text = String(item);
    const compacted = text.toLowerCase();
    const score = keywords.reduce((total, keyword) => total + (compacted.includes(keyword) ? 1 : 0), 0);
    if (score > bestScore) {
      best = text;
      bestScore = score;
    }
  }
  return bestScore >= 2 ? best : "";
}

function evidenceExcerpt(alert: AlertItem, evidence: string) {
  const lower = evidence.toLowerCase();
  const index = evidenceKeywords(alert)
    .map((keyword) => lower.indexOf(keyword))
    .filter((position) => position >= 0)
    .sort((left, right) => left - right)[0];
  if (index == null) return evidence;
  const start = Math.max(0, index - 70);
  const end = Math.min(evidence.length, index + 320);
  return `${start > 0 ? "…" : ""}${evidence.slice(start, end).trim()}${end < evidence.length ? "…" : ""}`;
}

function evidenceKeywords(alert: AlertItem) {
  const { signal, match } = alert;
  const values = [
    catalogItemName(match.catalog_item),
    match.catalog_item.brand,
    match.catalog_item.product_name,
    titleCase(signal.hazard_type),
    supplierSummary(alert),
  ];
  return Array.from(
    new Set(
      values
        .flatMap((value) => value.toLowerCase().split(/[^a-z0-9]+/g))
        .filter(
          (value) =>
            value.length >= 4 &&
            ![
              "company",
              "food",
              "foods",
              "information",
              "market",
              "product",
              "products",
              "recall",
              "source",
            ].includes(value),
        ),
    ),
  );
}

function supplierSummary(alert: AlertItem) {
  const suppliers = supplierCompanies(alert);
  if (suppliers.length) {
    const names = suppliers.map((node) => node.name);
    return names.length <= 3 ? names.join(" -> ") : `${names.slice(0, 3).join(" -> ")} +${names.length - 3} more`;
  }
  return "Unknown";
}

function trackSteps(alert: AlertItem): TrackStepData[] {
  const { signal, match } = alert;
  const steps: TrackStepData[] = [];
  const ingredients = matchedIngredients(match);
  const suppliers = supplierCompanies(alert);
  const impactedStores = matchImpactedStoreNames(match);
  const units = matchImpactedUnits(match);

  if (ingredients.length && match.tier !== "confirmed_match") {
    steps.push({
      label: "Shared ingredient",
      value: compactList(ingredients, 2),
      detail: titleCase(signal.hazard_type),
      tone: "bg-red-300",
    });
  }

  steps.push({
    label: "Recall signal",
    value: displaySignalTitle(signal),
    detail: signal.source.source_domain,
    tone: "bg-white",
  });

  suppliers.forEach((node, index) => {
    steps.push({
      label: node.role || (index === 0 ? "Supplier" : "Supply chain"),
      value: node.name,
      tone: index === 0 ? "bg-amber-300" : "bg-zinc-400",
    });
  });

  steps.push({
    label: "Catalog product",
    value: catalogItemName(match.catalog_item),
    detail: match.explanation,
    tone: "bg-sky-300",
  });

  if (impactedStores.length) {
    steps.push({
      label: "Store impact",
      value: `${compactNumber(units)} units across ${impactedStores.length} store${impactedStores.length === 1 ? "" : "s"}`,
      detail: compactList(impactedStores, 3),
      tone: "bg-emerald-300",
    });
  }

  return steps;
}

function supplyChainNodes(signal: RecallSignal) {
  const fromSignal = signal.supplier_chain
    .map((node) => ({
      name: normalizeChainName(stringValue(node.name ?? node.supplier ?? node.company)),
      role: normalizeRole(node.role),
    }))
    .filter((node) => node.name && isValidChainName(node.name));
  return dedupeNodes(fromSignal);
}

function supplierCompanies(alert: AlertItem) {
  const item = alert.match.catalog_item;
  const aliases = supplierAliases(item);
  const fromChain = supplyChainNodes(alert.signal).filter((node) => chainMatchesCatalogSupplier(node.name, aliases));
  const fromCatalog = [
    { name: normalizeChainName(item.supplier_name), role: "Catalog supplier" },
    { name: normalizeChainName(item.co_manufacturer_name ?? ""), role: "Co-manufacturer" },
  ];
  return dedupeNodes([...fromChain, ...fromCatalog].filter((node) => node.name && isValidChainName(node.name)));
}

function supplierAliases(item: CatalogItem) {
  return [
    item.supplier_name,
    item.co_manufacturer_name ?? "",
    ...item.supplier_aliases,
  ].map((value) => compactKey(normalizeChainName(value))).filter(Boolean);
}

function chainMatchesCatalogSupplier(chainName: string, aliases: string[]) {
  const normalized = compactKey(chainName);
  return aliases.some((alias) => alias && (normalized.includes(alias) || alias.includes(normalized)));
}

function matchedIngredients(match: ExposureMatch) {
  const value = match.matched_fields.ingredient_overlap;
  return Array.isArray(value) ? Array.from(new Set(value.map((item) => titleCase(String(item))).filter(Boolean))) : [];
}

function matchImpactedStoreNames(match: ExposureMatch) {
  return Array.from(new Set(match.impacted_inventory.map((lot) => lot.store_name)));
}

function matchImpactedUnits(match: ExposureMatch) {
  return match.impacted_inventory.reduce((total, lot) => total + lot.quantity_on_hand, 0);
}

function compactList(values: string[], limit: number) {
  const unique = Array.from(new Set(values.filter(Boolean)));
  if (unique.length <= limit) return unique.join(", ");
  return `${unique.slice(0, limit).join(", ")} +${unique.length - limit} more`;
}

function dedupeNodes(nodes: { name: string; role: string }[]) {
  const seen = new Set<string>();
  return nodes.filter((node) => {
    const key = node.name
      .toLowerCase()
      .replaceAll(".", "")
      .replace(/\b(llc|inc|incorporated|corp|corporation|co|company)\b/g, "")
      .replace(/\s+/g, " ")
      .trim();
    if (!key || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function catalogItemName(item: CatalogItem) {
  return stripSize(`${item.brand} ${item.product_name}`);
}

function normalizeChainName(value: string) {
  return value
    .replace(/\s+/g, " ")
    .replace(/^(the|a|an)\s+/i, "")
    .replace(/\s+(?:which|that|however|although)\b.*$/i, "")
    .replace(/[.;,:'"“”()[\]]+$/g, "")
    .trim();
}

function normalizeRole(value: unknown) {
  const role = stringValue(value);
  if (!role || /^(null|none|unknown|n\/a)$/i.test(role)) return "";
  return titleCase(role);
}

function isValidChainName(value: string) {
  const words = value.split(/\s+/);
  if (["and", "or", "nor", "the", "of", "for", "from", "by", "to", "in", "on", "with", "use"].includes(value.toLowerCase())) return false;
  if (value.length < 3 || value.length > 80) return false;
  if (/^(of|for|from|by|to|in|on|with)\s+/i.test(value)) return false;
  if (/[;:]/.test(value)) return false;
  if (/\b(the recalls|announced by|health officials|recall notice|according to|however|consumer|use)\b/i.test(value)) return false;
  if (words.length > 9 && !/\b(inc|llc|ltd|corp|corporation|company|co|usa|foods|dairies)\b/i.test(value)) return false;
  return true;
}

const TIER_RANK: Record<TriageTier, number> = {
  confirmed_match: 0,
  supplier_review: 1,
  watch_only: 2,
  no_exposure: 3,
};

function detailString(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function productImageForAlert(alert: AlertItem) {
  const metadata = alert.match.catalog_item.metadata;
  return firstExternalUrl(
    metadata.product_image_url,
    metadata.image_url,
    metadata.thumbnail_url,
    metadata.photo_url,
  );
}

function firstExternalUrl(...values: unknown[]) {
  for (const value of values) {
    const text = detailString(value);
    if (text && isProductImageCandidate(text)) return text;
  }
  return "";
}

function isProductImageCandidate(url: string) {
  if (!isExternalUrl(url)) return false;
  if (isRecallAuthorityDomain(url)) return false;
  const path = url.toLowerCase().split("?")[0] ?? "";
  if (/\b(favicon|apple-touch-icon|logo|icon|sprite|placeholder|default|seal)\b/.test(path)) return false;
  return /\.(avif|gif|jpe?g|png|webp)$/.test(path);
}

function supplierLogoForDetails(details: Record<string, unknown>) {
  const url = detailString(details.logo_url);
  if (!url || !isExternalUrl(url) || isRecallAuthorityDomain(url)) return "";
  return url;
}

function isRecallAuthorityDomain(url: string) {
  try {
    const host = new URL(url).hostname.replace(/^www\./, "").toLowerCase();
    return ["fda.gov", "cdc.gov", "fsis.usda.gov", "foodsafety.gov"].some(
      (domain) => host === domain || host.endsWith(`.${domain}`),
    );
  } catch {
    return false;
  }
}

function truncateText(value: string, maxLength: number) {
  const compacted = value.replace(/\s+/g, " ").trim();
  return compacted.length > maxLength ? `${compacted.slice(0, maxLength - 1).trim()}…` : compacted;
}

function stringValue(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function looksLikeHeadline(value: string) {
  return /\b(recall|warning|alert|outbreak|what to check|sparks|linked to|brand-by-brand|after)\b/i.test(value);
}

function isExternalUrl(value: string) {
  return value.startsWith("http://") || value.startsWith("https://");
}
