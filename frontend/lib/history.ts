import type { HistoryItem } from "@/lib/types";

const STORAGE_KEY = "mpchat-history";
const MAX_ITEMS = 50;

function isValidHistoryItem(item: unknown): item is HistoryItem {
  if (!item || typeof item !== "object") return false;
  const obj = item as Record<string, unknown>;
  return (
    typeof obj.id === "string" &&
    typeof obj.createdAt === "string" &&
    typeof obj.scenario === "string" &&
    obj.result != null &&
    typeof obj.result === "object" &&
    typeof (obj.result as Record<string, unknown>).title === "string"
  );
}

export function readHistory(): HistoryItem[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) return [];
    return parsed.filter(isValidHistoryItem);
  } catch {
    return [];
  }
}

export function writeHistory(items: HistoryItem[]) {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.setItem(STORAGE_KEY, JSON.stringify(items.slice(0, MAX_ITEMS)));
}

export function pushHistory(item: HistoryItem) {
  const next = [item, ...readHistory()].slice(0, MAX_ITEMS);
  writeHistory(next);
}

export function clearHistory() {
  if (typeof window === "undefined") {
    return;
  }
  window.localStorage.removeItem(STORAGE_KEY);
}
