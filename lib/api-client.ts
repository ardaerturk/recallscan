import type {
  CatalogResponse,
  DashboardResponse,
  ManualScanResponse,
  ProductAssetResponse,
  SupplierLookupResponse,
} from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api";
const DEFAULT_LOOKBACK_DAYS = 365;
const supplierLookupCache = new Map<string, Promise<SupplierLookupResponse>>();
const productAssetCache = new Map<string, Promise<ProductAssetResponse>>();

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers ?? {}),
    },
  });
  if (!response.ok) {
    throw new Error(await responseErrorMessage(response));
  }
  return (await response.json()) as T;
}

async function responseErrorMessage(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    const body = (await response.json().catch(() => null)) as { detail?: unknown; message?: unknown } | null;
    const detail = typeof body?.detail === "string" ? body.detail : typeof body?.message === "string" ? body.message : "";
    return detail || `Request failed with ${response.status}`;
  }

  const body = await response.text().catch(() => "");
  if (contentType.includes("text/html") || body.trim().startsWith("<!DOCTYPE html")) {
    return "RecallScan API is unavailable. Check the database connection, then scan again.";
  }

  return body.slice(0, 240) || `Request failed with ${response.status}`;
}

export function getDashboard(days = DEFAULT_LOOKBACK_DAYS) {
  return request<DashboardResponse>(`/recalls/recent?days=${days}`, { cache: "no-store" });
}

export function getCatalog() {
  return request<CatalogResponse>("/catalog", { cache: "no-store" });
}

export function runManualScan(forceFresh = false) {
  return request<ManualScanResponse>("/scans", {
    method: "POST",
    headers: {
      "Idempotency-Key": `manual-scan-${crypto.randomUUID()}`,
    },
    body: JSON.stringify({ scan_type: "recent_recalls", days: DEFAULT_LOOKBACK_DAYS, force_fresh: forceFresh }),
  });
}

export function lookupSupplier(name: string) {
  const key = name.trim().toLowerCase();
  const cached = supplierLookupCache.get(key);
  if (cached) return cached;
  const pending = request<SupplierLookupResponse>(`/suppliers/lookup?name=${encodeURIComponent(name)}`, { cache: "no-store" }).catch(
    (error) => {
      supplierLookupCache.delete(key);
      throw error;
    },
  );
  supplierLookupCache.set(key, pending);
  return pending;
}

export function getProductAsset(catalogItemId: string) {
  const key = catalogItemId.trim();
  const cached = productAssetCache.get(key);
  if (cached) return cached;
  const pending = request<ProductAssetResponse>(`/catalog/${encodeURIComponent(key)}/asset`, { cache: "no-store" }).catch(
    (error) => {
      productAssetCache.delete(key);
      throw error;
    },
  );
  productAssetCache.set(key, pending);
  return pending;
}
