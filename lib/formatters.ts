import type { TriageTier } from "@/lib/types";

export const tierLabels: Record<TriageTier, string> = {
  confirmed_match: "Pull from shelves",
  supplier_review: "Contact supplier",
  watch_only: "Monitor",
  no_exposure: "Clear",
};

export const tierTone: Record<TriageTier, string> = {
  confirmed_match: "border-red-500/50 bg-red-500/10 text-red-200",
  supplier_review: "border-amber-500/50 bg-amber-500/10 text-amber-200",
  watch_only: "border-sky-500/50 bg-sky-500/10 text-sky-200",
  no_exposure: "border-emerald-500/50 bg-emerald-500/10 text-emerald-200",
};

export function formatDate(value: string | null | undefined) {
  if (!value) return "Unknown";
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", year: "numeric" }).format(
    new Date(value),
  );
}

export function formatTime(value: string | null | undefined) {
  if (!value) return "Not scanned";
  return new Intl.DateTimeFormat("en", { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }).format(
    new Date(value),
  );
}

export function compactNumber(value: number) {
  return new Intl.NumberFormat("en", { notation: value > 999 ? "compact" : "standard" }).format(value);
}

export function titleCase(value: string) {
  return value
    .replaceAll("_", " ")
    .split(" ")
    .filter(Boolean)
    .map((word) => word.slice(0, 1).toUpperCase() + word.slice(1))
    .join(" ");
}

export function listValue(value: unknown): string {
  if (Array.isArray(value)) {
    const values = value.filter(Boolean);
    return values.length ? values.join(", ") : "None";
  }
  if (value == null) return "None";
  const text = String(value).trim();
  return text || "None";
}
