import type { HistoryItem } from "@/lib/types";

const STORAGE_KEY = "mpchat-history";
const MAX_ITEMS = 50;

export function readHistory(): HistoryItem[] {
  if (typeof window === "undefined") {
    return [];
  }

  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    return raw ? (JSON.parse(raw) as HistoryItem[]) : [];
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
