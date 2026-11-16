import { useEffect, useMemo, useState } from "react";
import { listColors, listComponents, listTypes } from "../api";
import { money } from "../format";
import type { Color, Component, ComponentType } from "../types";
import { ComponentForm } from "./ComponentForm";

export function CatalogPage() {
  const [types, setTypes] = useState<ComponentType[]>([]);
  const [colors, setColors] = useState<Color[]>([]);
  const [items, setItems] = useState<Component[]>([]);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [rootId, setRootId] = useState<number | null>(null);
  const [colorId, setColorId] = useState<number | null>(null);
  const [showArchived, setShowArchived] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editor, setEditor] = useState<Component | null | undefined>(undefined);

  useEffect(() => {
    const timer = window.setTimeout(() => setQuery(search), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  function reload() {
    setLoading(true);
    Promise.all([listTypes(true), listColors(true), listComponents(query, showArchived)])
      .then(([nextTypes, nextColors, nextItems]) => {
        setTypes(nextTypes);
        setColors(nextColors);
        setItems(nextItems);
        setError(null);
      })
      .catch((cause: unknown) => {
        setError(cause instanceof Error ? cause.message : "Не удалось открыть каталог");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    reload();
    // reload is recreated each render; the inputs below are the real triggers.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, showArchived]);

  const roots = types.filter((item) => item.parent_id === null && !item.is_archived);
  const visible = useMemo(() => {
    return items.filter((item) => {
      const rootOk = rootId === null || item.type.id === rootId || item.type.parent_id === rootId;
      const colorOk = colorId === null || item.color_id === colorId;
      return rootOk && colorOk;
    });
  }, [items, rootId, colorId]);

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>Комплектующие</h1>
          <p>Замки, нити, коробочки и всё остальное, что лежит в коробке.</p>
        </div>
        <button type="button" className="primary" onClick={() => setEditor(null)}>
          Добавить
        </button>
      </div>

      <div className="toolbar">
        <input
          className="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Найти по названию"
          aria-label="Поиск"
        />
        <div className="chips" role="group" aria-label="Тип">
          <button type="button" className={rootId === null ? "chip is-on" : "chip"} onClick={() => setRootId(null)}>
            Все
          </button>
          {roots.map((root) => (
            <button
              key={root.id}
              type="button"
              className={rootId === root.id ? "chip is-on" : "chip"}
              onClick={() => setRootId(root.id)}
            >
              {root.name}
            </button>
          ))}
        </div>
        <label className="color-filter">
          Цвет
          <select
            value={colorId ?? ""}
            onChange={(event) => setColorId(event.target.value ? Number(event.target.value) : null)}
          >
            <option value="">Любой</option>
            {colors
              .filter((item) => !item.is_archived)
              .map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
          </select>
        </label>
        <label className="check">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(event) => setShowArchived(event.target.checked)}
          />
          Архив
        </label>
      </div>

      {error ? <p className="banner">{error}</p> : null}
      {loading ? <p className="muted">Собираю полку…</p> : null}

      {!loading && visible.length === 0 ? (
        <div className="empty">
          <p>На полке пока пусто.</p>
          <button type="button" className="ghost" onClick={() => setEditor(null)}>
            Положить первое
          </button>
        </div>
      ) : null}

      <ul className="grid">
        {visible.map((item) => (
          <li key={item.id}>
            <button type="button" className={item.is_archived ? "card is-archived" : "card"} onClick={() => setEditor(item)}>
              <img src={item.image_preview || item.image} alt="" />
              <div className="card-body">
                <div className="card-title">
                  <h2>{item.name}</h2>
                  {item.is_archived ? <span>архив</span> : null}
                </div>
                <p className="price">
                  {money(item.cost)} <small>/ {item.unit}</small>
                </p>
                <p className="meta">
                  {item.type.name}
                  {item.color ? ` · ${item.color.name}` : ""}
                  {item.article ? ` · ${item.article}` : ""}
                </p>
                {item.shops.length > 0 ? <p className="shops-line">{item.shops.join(" · ")}</p> : null}
              </div>
            </button>
          </li>
        ))}
      </ul>

      {editor !== undefined ? (
        <ComponentForm
          types={types}
          colors={colors}
          initial={editor}
          onClose={() => setEditor(undefined)}
          onSaved={() => {
            setEditor(undefined);
            reload();
          }}
        />
      ) : null}
    </section>
  );
}
