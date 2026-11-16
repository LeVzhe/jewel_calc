import { useEffect, useState, type FormEvent } from "react";
import {
  archiveComponents,
  createComponent,
  unarchiveComponents,
  updateComponent,
  type ComponentPayload,
} from "../api";
import { skipMessage } from "../format";
import type { Color, Component, ComponentType, Unit } from "../types";
import { UNITS } from "../types";

type Props = {
  types: ComponentType[];
  colors: Color[];
  initial: Component | null;
  onClose: () => void;
  onSaved: () => void;
};

function fileToDataUrl(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result));
    reader.onerror = () => reject(reader.error ?? new Error("Не удалось прочитать файл"));
    reader.readAsDataURL(file);
  });
}

export function ComponentForm({ types, colors, initial, onClose, onSaved }: Props) {
  const activeTypes = types.filter((item) => !item.is_archived);
  const activeColors = colors.filter((item) => !item.is_archived);
  const roots = activeTypes.filter((item) => item.parent_id === null);

  const [name, setName] = useState(initial?.name ?? "");
  const [cost, setCost] = useState(initial ? String(initial.cost) : "");
  const [unit, setUnit] = useState<Unit>(initial?.unit ?? "шт");
  const [typeId, setTypeId] = useState(initial?.type_id ?? roots[0]?.id ?? activeTypes[0]?.id ?? 0);
  const [colorId, setColorId] = useState<number | "">(initial?.color_id ?? "");
  const [article, setArticle] = useState(initial?.article ?? "");
  const [shops, setShops] = useState<string[]>(initial?.shops ?? []);
  const [shopDraft, setShopDraft] = useState("");
  const [imageData, setImageData] = useState<string | null>(null);
  const [preview, setPreview] = useState(initial?.image ?? "");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") onClose();
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [onClose]);

  function addShop() {
    const label = shopDraft.trim();
    if (!label) return;
    if (shops.some((item) => item.toLocaleLowerCase("ru") === label.toLocaleLowerCase("ru"))) {
      setShopDraft("");
      return;
    }
    setShops((current) => [...current, label]);
    setShopDraft("");
  }

  async function onFile(file: File | undefined) {
    if (!file) return;
    if (!file.type.startsWith("image/")) {
      setError("Нужен файл картинки.");
      return;
    }
    if (file.size > 10 * 1024 * 1024) {
      setError("Файл больше 10 МБ.");
      return;
    }
    const data = await fileToDataUrl(file);
    setImageData(data);
    setPreview(data);
    setError(null);
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    const parsedCost = Number(cost.replace(",", "."));
    if (!name.trim()) {
      setError("Нужно название.");
      return;
    }
    if (!Number.isFinite(parsedCost) || parsedCost < 0) {
      setError("Цена — число от нуля.");
      return;
    }
    if (!typeId) {
      setError("Выберите тип.");
      return;
    }
    if (!initial && !imageData) {
      setError("Добавьте фото.");
      return;
    }

    const body: ComponentPayload = {
      name: name.trim(),
      cost: parsedCost,
      unit,
      article: article.trim() || null,
      type_id: typeId,
      color_id: colorId === "" ? null : colorId,
      shops,
    };
    if (imageData) body.image_base64 = imageData;

    setBusy(true);
    setError(null);
    try {
      if (initial) await updateComponent(initial.id, body);
      else await createComponent(body);
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
      const result = archived
        ? await archiveComponents([initial.id])
        : await unarchiveComponents([initial.id]);
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
      <form className="drawer" onSubmit={onSubmit}>
        <div className="drawer-head">
          <h2>{initial ? "Комплектующее" : "Новое комплектующее"}</h2>
          <button type="button" className="text-button" onClick={onClose}>
            Закрыть
          </button>
        </div>

        <label className="photo-picker">
          {preview ? <img src={preview} alt="" /> : <span>Фото ляжет в квадрат с белым полем</span>}
          <input
            type="file"
            accept="image/*"
            onChange={(event) => void onFile(event.target.files?.[0])}
          />
        </label>

        <label>
          Название
          <input value={name} onChange={(event) => setName(event.target.value)} maxLength={255} required />
        </label>

        <div className="split">
          <label>
            Цена за единицу
            <input
              inputMode="decimal"
              value={cost}
              onChange={(event) => setCost(event.target.value)}
              placeholder="0,00"
              required
            />
          </label>
          <label>
            Единица
            <select value={unit} onChange={(event) => setUnit(event.target.value as Unit)}>
              {UNITS.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </label>
        </div>

        <label>
          Тип
          <select value={typeId} onChange={(event) => setTypeId(Number(event.target.value))}>
            {roots.map((root) => (
              <optgroup key={root.id} label={root.name}>
                <option value={root.id}>{root.name}</option>
                {activeTypes
                  .filter((item) => item.parent_id === root.id)
                  .map((item) => (
                    <option key={item.id} value={item.id}>
                      {item.name}
                    </option>
                  ))}
              </optgroup>
            ))}
          </select>
        </label>

        <label>
          Цвет
          <select
            value={colorId}
            onChange={(event) => setColorId(event.target.value ? Number(event.target.value) : "")}
          >
            <option value="">Смотреть по фото</option>
            {activeColors.map((item) => (
              <option key={item.id} value={item.id}>
                {item.name}
              </option>
            ))}
          </select>
        </label>

        <label>
          Артикул
          <input value={article} onChange={(event) => setArticle(event.target.value)} maxLength={128} />
        </label>

        <div className="shops">
          <label>
            Где купить
            <input
              value={shopDraft}
              onChange={(event) => setShopDraft(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  event.preventDefault();
                  addShop();
                }
              }}
              placeholder="Ozon, магазин, павильон"
              maxLength={500}
            />
          </label>
          <button type="button" className="ghost" onClick={addShop}>
            Добавить
          </button>
          <ul>
            {shops.map((shop) => (
              <li key={shop}>
                {shop}
                <button type="button" onClick={() => setShops((current) => current.filter((item) => item !== shop))}>
                  убрать
                </button>
              </li>
            ))}
          </ul>
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
              {initial.is_archived ? "Вернуть в каталог" : "В архив"}
            </button>
          ) : null}
        </div>
      </form>
    </div>
  );
}
