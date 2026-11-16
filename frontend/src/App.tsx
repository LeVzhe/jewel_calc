import { useEffect, useState } from "react";
import { getMeta, type AppMeta } from "./api";
import { CatalogPage } from "./catalog/CatalogPage";
import { JewelryPage } from "./jewelry/JewelryPage";
import { ReferencesPage } from "./references/ReferencesPage";

type Section = "jewelry" | "catalog" | "references";

const FALLBACK_META: AppMeta = {
  name: "Jewel calc",
  version: "1.0.0",
  year: new Date().getFullYear(),
  author: "LeV",
};

export function App() {
  const [section, setSection] = useState<Section>("jewelry");
  const [meta, setMeta] = useState<AppMeta>(FALLBACK_META);

  useEffect(() => {
    getMeta()
      .then(setMeta)
      .catch(() => setMeta(FALLBACK_META));
  }, []);

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
            className={section === "jewelry" ? "nav-link is-active" : "nav-link"}
            onClick={() => setSection("jewelry")}
          >
            Бижутерия
          </button>
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
      <main>
        {section === "jewelry" ? <JewelryPage /> : null}
        {section === "catalog" ? <CatalogPage /> : null}
        {section === "references" ? <ReferencesPage /> : null}
      </main>
      <footer className="footer">
        <ul>
          <li>{meta.name}</li>
          <li>версия {meta.version}</li>
          <li>{meta.year}</li>
          <li>By {meta.author}</li>
        </ul>
      </footer>
    </div>
  );
}
