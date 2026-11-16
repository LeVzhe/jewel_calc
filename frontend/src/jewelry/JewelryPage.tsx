import { useEffect, useState, type PointerEvent } from "react";
import { listJewelry } from "../api";
import { money } from "../format";
import type { Jewelry } from "../types";
import { PAGE_SIZE, Pager, usePageReset } from "../shelf/Pager";
import { useShelfView, ViewSwitch } from "../shelf/ShelfView";
import { JewelryForm } from "./JewelryForm";
import { PhotoCarousel } from "./PhotoCarousel";

function cardBody(item: Jewelry) {
  return (
    <>
      <div className="card-title">
        <h2>{item.name}</h2>
        {item.is_archived ? <span>архив</span> : null}
      </div>
      <p className="price price-hero">{money(item.cost)}</p>
      <p className="sale-line">к продаже {money(item.sale_price)}</p>
      <p className="initial-cost">сначала {money(item.initial_cost)}</p>
    </>
  );
}

function JewelryTile({ item, onOpen }: { item: Jewelry; onOpen: () => void }) {
  const [hover, setHover] = useState(false);

  function track(event: PointerEvent<HTMLElement>, active: boolean) {
    if (event.pointerType === "mouse") setHover(active);
  }

  return (
    <article
      className={item.is_archived ? "card is-archived" : "card"}
      onPointerEnter={(event) => track(event, true)}
      onPointerLeave={(event) => track(event, false)}
    >
      <PhotoCarousel photos={item.photos} playing={hover} onOpen={onOpen} />
      <button type="button" className="card-body" onClick={onOpen}>
        {cardBody(item)}
      </button>
    </article>
  );
}

export function JewelryPage() {
  const [items, setItems] = useState<Jewelry[]>([]);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState("");
  const [query, setQuery] = useState("");
  const [showArchived, setShowArchived] = useState(false);
  const [page, setPage] = usePageReset(`${query}|${showArchived}`);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editor, setEditor] = useState<Jewelry | null | undefined>(undefined);
  const [shelf, setShelf] = useShelfView();

  useEffect(() => {
    const timer = window.setTimeout(() => setQuery(search), 300);
    return () => window.clearTimeout(timer);
  }, [search]);

  function reload() {
    setLoading(true);
    listJewelry(query, showArchived, (page - 1) * PAGE_SIZE, PAGE_SIZE)
      .then((next) => {
        const last = Math.max(1, Math.ceil(next.total / PAGE_SIZE));
        if (page > last) {
          setPage(last);
          return;
        }
        setItems(next.items);
        setTotal(next.total);
        setError(null);
      })
      .catch((cause: unknown) => {
        setError(cause instanceof Error ? cause.message : "Не удалось открыть изделия");
      })
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [query, showArchived, page]);

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>Бижутерия</h1>
          <p>Готовые изделия. Себестоимость считается из состава, цену продажи задают бегунком или вручную.</p>
        </div>
        <button type="button" className="primary" onClick={() => setEditor(null)}>
          Собрать
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
        <label className="check">
          <input
            type="checkbox"
            checked={showArchived}
            onChange={(event) => setShowArchived(event.target.checked)}
          />
          Архив
        </label>
        <ViewSwitch view={shelf} onChange={setShelf} />
      </div>

      {error ? <p className="banner">{error}</p> : null}
      {loading ? <p className="muted">Раскладываю изделия…</p> : null}

      {!loading && items.length === 0 ? (
        <div className="empty">
          <p>Изделий пока нет.</p>
          <button type="button" className="ghost" onClick={() => setEditor(null)}>
            Собрать первое
          </button>
        </div>
      ) : null}

      <ul className={`shelf shelf-${shelf}`}>
        {items.map((item) => {
          const cover = item.photos[0];
          const carousel = shelf !== "list" && item.photos.length > 1;
          return (
            <li key={item.id}>
              {carousel ? (
                <JewelryTile item={item} onOpen={() => setEditor(item)} />
              ) : (
                <button
                  type="button"
                  className={item.is_archived ? "card is-archived" : "card"}
                  onClick={() => setEditor(item)}
                >
                  {cover ? <img src={cover.image_preview} alt="" /> : <span className="card-fallback" />}
                  <div className="card-body">{cardBody(item)}</div>
                </button>
              )}
            </li>
          );
        })}
      </ul>

      <Pager page={page} total={total} onPage={setPage} />

      {editor !== undefined ? (
        <JewelryForm
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
