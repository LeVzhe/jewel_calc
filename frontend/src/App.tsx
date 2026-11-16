import { useState } from "react";
import { CatalogPage } from "./catalog/CatalogPage";
import { ReferencesPage } from "./references/ReferencesPage";

type Section = "catalog" | "references";

export function App() {
  const [section, setSection] = useState<Section>("catalog");

  return (
    <div className="shell">
      <header className="topbar">
        <div className="brand">
          <span className="mark" aria-hidden="true" />
          <div>
            <p className="brand-name">Jewel calc</p>
            <p className="brand-note">домашняя мастерская</p>
          </div>
        </div>
        <nav className="nav" aria-label="Разделы">
          <button
            type="button"
            className={section === "catalog" ? "nav-link is-active" : "nav-link"}
            onClick={() => setSection("catalog")}
          >
            Комплектующие
          </button>
          <button
            type="button"
            className={section === "references" ? "nav-link is-active" : "nav-link"}
            onClick={() => setSection("references")}
          >
            Справочники
          </button>
        </nav>
      </header>
      <main>{section === "catalog" ? <CatalogPage /> : <ReferencesPage />}</main>
    </div>
  );
}
