import { useState } from "react";

export type ShelfView = "grid" | "large" | "list";

const STORAGE_KEY = "jewel-calc-shelf-view";

const OPTIONS: { id: ShelfView; label: string }[] = [
  { id: "grid", label: "Плитка" },
  { id: "large", label: "Крупно" },
  { id: "list", label: "Список" },
];

function readView(): ShelfView {
  const saved = window.localStorage.getItem(STORAGE_KEY);
  if (saved === "grid" || saved === "large" || saved === "list") return saved;
  return "grid";
}

export function useShelfView(): [ShelfView, (view: ShelfView) => void] {
  const [view, setView] = useState<ShelfView>(readView);
  function choose(next: ShelfView) {
    setView(next);
    window.localStorage.setItem(STORAGE_KEY, next);
  }
  return [view, choose];
}

export function ViewSwitch({ view, onChange }: { view: ShelfView; onChange: (view: ShelfView) => void }) {
  return (
    <div className="view-switch" role="group" aria-label="Вид полки">
      {OPTIONS.map((option) => (
        <button
          key={option.id}
          type="button"
          className={view === option.id ? "is-on" : undefined}
          aria-label={option.label}
          aria-pressed={view === option.id}
          title={option.label}
          onClick={() => onChange(option.id)}
        >
          <ShelfIcon view={option.id} />
        </button>
      ))}
    </div>
  );
}

function ShelfIcon({ view }: { view: ShelfView }) {
  if (view === "list") {
    return (
      <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
        <rect x="1" y="2" width="4" height="4" rx="1" fill="currentColor" />
        <rect x="7" y="3" width="10" height="2" rx="1" fill="currentColor" />
        <rect x="1" y="8" width="4" height="4" rx="1" fill="currentColor" />
        <rect x="7" y="9" width="10" height="2" rx="1" fill="currentColor" />
        <rect x="1" y="14" width="4" height="2" rx="1" fill="currentColor" />
        <rect x="7" y="14" width="10" height="2" rx="1" fill="currentColor" />
      </svg>
    );
  }
  if (view === "large") {
    return (
      <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
        <rect x="1" y="1" width="16" height="16" rx="3" fill="currentColor" />
      </svg>
    );
  }
  return (
    <svg width="18" height="18" viewBox="0 0 18 18" aria-hidden="true">
      <rect x="1" y="1" width="7" height="7" rx="1.5" fill="currentColor" />
      <rect x="10" y="1" width="7" height="7" rx="1.5" fill="currentColor" />
      <rect x="1" y="10" width="7" height="7" rx="1.5" fill="currentColor" />
      <rect x="10" y="10" width="7" height="7" rx="1.5" fill="currentColor" />
    </svg>
  );
}
