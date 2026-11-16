import { useEffect, useMemo, useRef, useState, type FormEvent } from "react";
import {
  archiveJewelry,
  createJewelry,
  listComponents,
  unarchiveJewelry,
  updateJewelry,
} from "../api";
import { localKey, readImageFile } from "../files";
import { markupFromSale, money, roundMoney, salePrice, skipMessage } from "../format";
import type { Component, Jewelry } from "../types";

type Props = {
  initial: Jewelry | null;
  onClose: () => void;
  onSaved: () => void;
};

type DraftPhoto = {
  key: string;
  id?: number;
  previewUrl: string;
  fullUrl?: string;
  imageBase64?: string;
};

type DraftPart = {
  componentId: number;
  quantity: string;
  unitCost: number;
  component: Component | Jewelry["parts"][number]["component"];
};

const DEFAULT_MARKUP = 30;
const MAX_PHOTOS = 8;

function parseQuantity(value: string): number | null {
  const parsed = Number(value.replace(",", ".").trim());
  if (!Number.isFinite(parsed) || parsed <= 0) return null;
  const rounded = Math.round(parsed * 1000) / 1000;
  return rounded > 0 ? rounded : null;
}

function formatPriceInput(value: number): string {
  return value.toFixed(2).replace(".", ",");
}

function parsePriceInput(value: string): number | null {
  const parsed = Number(value.replace(/\s/g, "").replace(",", ".").trim());
  if (!Number.isFinite(parsed) || parsed < 0) return null;
  return roundMoney(parsed);
}

function componentPreview(component: DraftPart["component"]): string {
  return component.image_preview;
}

function componentLabel(component: DraftPart["component"]): string {
  if ("type" in component) return component.type.name;
  return component.type_name;
}

function componentColor(component: DraftPart["component"]): string | null {
  if ("type" in component) return component.color?.name ?? null;
  return component.color_name;
}

export function JewelryForm({ initial, onClose, onSaved }: Props) {
  const [name, setName] = useState(initial?.name ?? "");
  const [photos, setPhotos] = useState<DraftPhoto[]>(
    () =>
      initial?.photos.map((photo) => ({
        key: `saved-${photo.id}`,
        id: photo.id,
        previewUrl: photo.image_preview,
        fullUrl: photo.image,
      })) ?? [],
  );
  const [parts, setParts] = useState<DraftPart[]>(
    () =>
      initial?.parts.map((part) => ({
        componentId: part.component_id,
        quantity: String(part.quantity).replace(".", ","),
        unitCost: part.unit_cost,
        component: part.component,
      })) ?? [],
  );
  const [markup, setMarkup] = useState(() =>
    initial ? markupFromSale(initial.cost, initial.sale_price) : DEFAULT_MARKUP,
  );
  const [priceText, setPriceText] = useState(() =>
    formatPriceInput(initial?.sale_price ?? salePrice(0, DEFAULT_MARKUP)),
  );
  const [priceLocked, setPriceLocked] = useState(initial !== null);
  const [catalog, setCatalog] = useState<Component[]>([]);
  const [pickerOpen, setPickerOpen] = useState(false);
  const [pickerQuery, setPickerQuery] = useState("");
  const pickerRef = useRef<HTMLDivElement>(null);
  const [opened, setOpened] = useState<DraftPhoto | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    listComponents("", false)
      .then((page) => setCatalog(page.items))
      .catch(() => setCatalog([]));
  }, []);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key !== "Escape") return;
      if (opened) {
        setOpened(null);
        return;
      }
      if (pickerOpen) {
        setPickerOpen(false);
        return;
      }
      onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose, opened, pickerOpen]);

  useEffect(() => {
    if (!pickerOpen) return;
    function onPointer(event: PointerEvent) {
      if (!pickerRef.current?.contains(event.target as Node)) setPickerOpen(false);
    }
    window.addEventListener("pointerdown", onPointer);
    return () => window.removeEventListener("pointerdown", onPointer);
  }, [pickerOpen]);

  const chosen = useMemo(() => new Set(parts.map((part) => part.componentId)), [parts]);
  const pickerItems = useMemo(() => {
    const tokens = pickerQuery
      .trim()
      .toLocaleLowerCase("ru")
      .split(/\s+/)
      .filter(Boolean);
    return catalog.filter((item) => {
      if (item.is_archived || chosen.has(item.id)) return false;
      if (tokens.length === 0) return true;
      const haystack = [item.name, item.type.name, item.color?.name ?? ""].join(" ").toLocaleLowerCase("ru");
      return tokens.every((token) => haystack.includes(token));
    });
  }, [catalog, chosen, pickerQuery]);

  const totals = useMemo(() => {
    let cost = 0;
    let initialCost = 0;
    for (const part of parts) {
      const quantity = parseQuantity(part.quantity);
      if (quantity === null) continue;
      cost += roundMoney(quantity * part.component.cost);
      initialCost += roundMoney(quantity * part.unitCost);
    }
    return { cost: roundMoney(cost), initialCost: roundMoney(initialCost) };
  }, [parts]);

  useEffect(() => {
    if (priceLocked) {
      const parsed = parsePriceInput(priceText);
      if (parsed !== null) setMarkup(markupFromSale(totals.cost, parsed));
      return;
    }
    setPriceText(formatPriceInput(salePrice(totals.cost, markup)));
  }, [priceLocked, priceText, totals.cost, markup]);

  async function addFiles(list: FileList | null) {
    if (!list || list.length === 0) return;
    const room = MAX_PHOTOS - photos.length;
    if (room <= 0) {
      setError("Не больше восьми фото.");
      return;
    }
    const incoming = Array.from(list).slice(0, room);
    try {
      const next: DraftPhoto[] = [];
      for (const file of incoming) {
        const imageBase64 = await readImageFile(file);
        next.push({
          key: `new-${localKey()}`,
          previewUrl: imageBase64,
          imageBase64,
        });
      }
      setPhotos((current) => [...current, ...next]);
      setError(incoming.length < list.length ? "Лишние фото не взяла: максимум восемь." : null);
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось прочитать фото");
    }
  }

  function addPart(component: Component) {
    setParts((current) => [
      ...current,
      {
        componentId: component.id,
        quantity: "1",
        unitCost: component.cost,
        component,
      },
    ]);
    setPickerQuery("");
    setPickerOpen(false);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) {
      setError("Нужно название.");
      return;
    }
    if (photos.length === 0) {
      setError("Добавьте хотя бы одно фото.");
      return;
    }
    if (parts.length === 0) {
      setError("Добавьте хотя бы одну деталь.");
      return;
    }
    const payloadParts = [];
    for (const part of parts) {
      const quantity = parseQuantity(part.quantity);
      if (quantity === null) {
        setError("Количество — число больше нуля.");
        return;
      }
      payloadParts.push({ component_id: part.componentId, quantity });
    }
    const finalPrice = parsePriceInput(priceText);
    if (finalPrice === null) {
      setError("Цена продажи — число от нуля.");
      return;
    }
    const photoPayload = photos.map((photo) =>
      photo.id !== undefined ? { id: photo.id } : { image_base64: photo.imageBase64 ?? "" },
    );
    if (photoPayload.some((photo) => "image_base64" in photo && photo.image_base64 === "")) {
      setError("Одно из новых фото не прочиталось.");
      return;
    }

    setBusy(true);
    setError(null);
    try {
      if (initial) {
        await updateJewelry(initial.id, {
          name: name.trim(),
          parts: payloadParts,
          photos: photoPayload,
          sale_price: finalPrice,
        });
      } else {
        await createJewelry({
          name: name.trim(),
          parts: payloadParts,
          photos: photos.map((photo) => photo.imageBase64 ?? ""),
          sale_price: finalPrice,
        });
      }
      onSaved();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось сохранить");
      setBusy(false);
    }
  }

  async function moveArchive(archived: boolean) {
    if (!initial) return;
    setBusy(true);
    setError(null);
    try {
      const result = archived ? await archiveJewelry([initial.id]) : await unarchiveJewelry([initial.id]);
      const note = skipMessage(result);
      if (note && result.ids.length === 0) {
        setError(note);
        setBusy(false);
        return;
      }
      onSaved();
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : "Не удалось изменить архив");
      setBusy(false);
    }
  }

  return (
    <div className="drawer-root">
      <button type="button" className="backdrop" aria-label="Закрыть" onClick={onClose} />
      <form className="drawer wide" onSubmit={onSubmit}>
        <div className="drawer-head">
          <h2>{initial ? "Изделие" : "Новое изделие"}</h2>
          <button type="button" className="text-button" onClick={onClose}>
            Закрыть
          </button>
        </div>

        <div className="photo-strip" aria-label="Фото изделия">
          {photos.map((photo, index) => (
            <div className="photo-tile" key={photo.key}>
              <button type="button" className="photo-open" onClick={() => setOpened(photo)}>
                <img src={photo.previewUrl} alt="" />
              </button>
              <span className="photo-role">{index === 0 ? "обложка" : "кадр"}</span>
              <button
                type="button"
                className="text-button"
                onClick={() => setPhotos((current) => current.filter((item) => item.key !== photo.key))}
              >
                убрать
              </button>
            </div>
          ))}
        </div>
        <div className="photo-actions">
          <label className="ghost">
            Снять
            <input
              type="file"
              accept="image/*"
              capture="environment"
              onChange={(event) => {
                void addFiles(event.target.files);
                event.target.value = "";
              }}
            />
          </label>
          <label className="ghost">
            Файл
            <input
              type="file"
              accept="image/*"
              multiple
              onChange={(event) => {
                void addFiles(event.target.files);
                event.target.value = "";
              }}
            />
          </label>
        </div>

        <label>
          Название
          <input value={name} onChange={(event) => setName(event.target.value)} maxLength={255} required />
        </label>

        <div className="parts">
          <h3>Состав</h3>
          <div className="picker" ref={pickerRef}>
            <input
              value={pickerQuery}
              onFocus={() => setPickerOpen(true)}
              onChange={(event) => {
                setPickerQuery(event.target.value);
                setPickerOpen(true);
              }}
              placeholder="Добавить из каталога"
              aria-label="Поиск детали"
              aria-expanded={pickerOpen}
            />
            {pickerOpen ? (
              <ul className="picker-menu" role="listbox">
                {pickerItems.length === 0 ? <li className="muted">Ничего не найдено.</li> : null}
                {pickerItems.map((item) => (
                  <li key={item.id}>
                    <button type="button" className="picker-item" onClick={() => addPart(item)}>
                      <img src={item.image_preview} alt="" />
                      <span>
                        <strong>{item.name}</strong>
                        <small>
                          {item.type.name}
                          {item.color ? ` · ${item.color.name}` : ""} · {money(item.cost)} / {item.unit}
                        </small>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
          {parts.length === 0 ? <p className="muted">В изделии пока нет деталей.</p> : null}
          {parts.map((part) => {
            const quantity = parseQuantity(part.quantity);
            const line = quantity === null ? null : roundMoney(quantity * part.component.cost);
            return (
              <div className="part-row" key={part.componentId}>
                <img src={componentPreview(part.component)} alt="" />
                <div>
                  <strong>{part.component.name}</strong>
                  {part.component.is_archived ? <span className="archived-mark"> в архиве</span> : null}
                  <p className="meta">
                    {componentLabel(part.component)}
                    {componentColor(part.component) ? ` · ${componentColor(part.component)}` : ""}
                  </p>
                  <p className="meta">{line === null ? "укажите количество" : money(line)}</p>
                </div>
                <div className="part-side">
                  <input
                    className="part-qty"
                    inputMode="decimal"
                    aria-label={`Количество: ${part.component.name}`}
                    value={part.quantity}
                    onChange={(event) =>
                      setParts((current) =>
                        current.map((item) =>
                          item.componentId === part.componentId ? { ...item, quantity: event.target.value } : item,
                        ),
                      )
                    }
                  />
                  <span className="meta">{part.component.unit}</span>
                  <button
                    type="button"
                    className="text-button"
                    onClick={() => setParts((current) => current.filter((item) => item.componentId !== part.componentId))}
                  >
                    убрать
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        <div className="totals">
          <p className="price price-hero">{money(totals.cost)}</p>
          <label className="markup">
            Наценка {markup}%
            <input
              type="range"
              min={0}
              max={300}
              step={1}
              value={markup}
              onChange={(event) => {
                setPriceLocked(false);
                setMarkup(Number(event.target.value));
              }}
            />
          </label>
          <label className="sale-edit">
            К продаже, ₽
            <input
              inputMode="decimal"
              value={priceText}
              onChange={(event) => {
                const next = event.target.value;
                setPriceText(next);
                setPriceLocked(true);
                const parsed = parsePriceInput(next);
                if (parsed !== null) setMarkup(markupFromSale(totals.cost, parsed));
              }}
              onBlur={() => {
                const parsed = parsePriceInput(priceText);
                if (parsed !== null) setPriceText(formatPriceInput(parsed));
              }}
            />
          </label>
          <p className="markup-note">Бегунок и поле задают одну цену. Она запишется при сохранении. Новое изделие начинается с +30%.</p>
          <p className="initial-cost">сначала {money(totals.initialCost)}</p>
        </div>

        {error ? <p className="form-error">{error}</p> : null}

        <div className="drawer-actions">
          <button type="submit" className="primary" disabled={busy}>
            {busy ? "Сохраняю…" : "Сохранить"}
          </button>
          {initial ? (
            <button
              type="button"
              className="ghost"
              disabled={busy}
              onClick={() => void moveArchive(!initial.is_archived)}
            >
              {initial.is_archived ? "Вернуть из архива" : "В архив"}
            </button>
          ) : null}
        </div>
      </form>

      {opened ? (
        <div className="lightbox">
          <button type="button" className="backdrop" aria-label="Закрыть фото" onClick={() => setOpened(null)} />
          <img src={opened.fullUrl ?? opened.previewUrl} alt="" />
        </div>
      ) : null}
    </div>
  );
}
