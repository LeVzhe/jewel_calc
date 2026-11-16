import { useEffect, useState } from "react";
import {
  archiveColors,
  archiveTypes,
  createColor,
  createType,
  listColors,
  listTypes,
  renameColor,
  renameType,
  unarchiveColors,
  unarchiveTypes,
} from "../api";
import { skipMessage } from "../format";
import type { Color, ComponentType, IdsResult } from "../types";

export function ReferencesPage() {
  const [types, setTypes] = useState<ComponentType[]>([]);
  const [colors, setColors] = useState<Color[]>([]);
  const [showArchived, setShowArchived] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  function reload() {
    setLoading(true);
    Promise.all([listTypes(showArchived), listColors(showArchived)])
      .then(([nextTypes, nextColors]) => {
        setTypes(nextTypes);
        setColors(nextColors);
        setError(null);
      })
      .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Не удалось открыть справочники"))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    reload();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [showArchived]);

  function note(result: IdsResult) {
    const message = skipMessage(result);
    setError(message);
    if (result.ids.length > 0) reload();
  }

  const roots = types.filter((item) => item.parent_id === null);

  return (
    <section className="page">
      <div className="page-head">
        <div>
          <h1>Справочники</h1>
          <p>Типы и цвета, из которых собирается каталог. Сюда заходят редко.</p>
        </div>
        <label className="check">
          <input type="checkbox" checked={showArchived} onChange={(event) => setShowArchived(event.target.checked)} />
          Архив
        </label>
      </div>
      {error ? <p className="banner">{error}</p> : null}
      {loading ? <p className="muted">Открываю…</p> : null}

      <div className="ref-grid">
        <article className="panel">
          <h2>Типы</h2>
          <p className="panel-lead">Фурнитура, упаковка и нить остаются основами. Под ними можно завести свои виды.</p>
          {roots.map((root) => (
            <section key={root.id} className="root-block">
              <h3>{root.name}</h3>
              <ul>
                {types
                  .filter((item) => item.parent_id === root.id)
                  .map((item) => (
                    <NameRow
                      key={item.id}
                      name={item.name}
                      archived={item.is_archived}
                      onRename={(name) =>
                        renameType(item.id, name)
                          .then(() => reload())
                          .catch((cause: unknown) =>
                            setError(cause instanceof Error ? cause.message : "Не удалось переименовать"),
                          )
                      }
                      onArchive={() =>
                        (item.is_archived ? unarchiveTypes([item.id]) : archiveTypes([item.id])).then(note).catch(
                          (cause: unknown) => setError(cause instanceof Error ? cause.message : "Не удалось архивировать"),
                        )
                      }
                    />
                  ))}
              </ul>
              <AddRow
                placeholder={`Подтип для «${root.name}»`}
                onAdd={(name) =>
                  createType(name, root.id)
                    .then(() => reload())
                    .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Не удалось создать тип"))
                }
              />
            </section>
          ))}
        </article>

        <article className="panel">
          <h2>Цвета</h2>
          <p className="panel-lead">Подпись к фото. Если оттенок и так ясен по снимку, цвет можно не ставить.</p>
          <AddRow
            placeholder="Новый цвет"
            onAdd={(name) =>
              createColor(name)
                .then(() => reload())
                .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Не удалось создать цвет"))
            }
          />
          <ul className="plain-list">
            {colors.map((item) => (
              <NameRow
                key={item.id}
                name={item.name}
                archived={item.is_archived}
                onRename={(name) =>
                  renameColor(item.id, name)
                    .then(() => reload())
                    .catch((cause: unknown) => setError(cause instanceof Error ? cause.message : "Не удалось переименовать"))
                }
                onArchive={() =>
                  (item.is_archived ? unarchiveColors([item.id]) : archiveColors([item.id])).then(note).catch(
                    (cause: unknown) => setError(cause instanceof Error ? cause.message : "Не удалось архивировать"),
                  )
                }
              />
            ))}
          </ul>
        </article>
      </div>
    </section>
  );
}

function AddRow({ placeholder, onAdd }: { placeholder: string; onAdd: (name: string) => void }) {
  const [value, setValue] = useState("");
  return (
    <form
      className="add-row"
      onSubmit={(event) => {
        event.preventDefault();
        const name = value.trim();
        if (!name) return;
        onAdd(name);
        setValue("");
      }}
    >
      <input value={value} onChange={(event) => setValue(event.target.value)} placeholder={placeholder} maxLength={255} />
      <button type="submit" className="ghost">
        Добавить
      </button>
    </form>
  );
}

function NameRow({
  name,
  archived,
  onRename,
  onArchive,
}: {
  name: string;
  archived: boolean;
  onRename: (name: string) => void;
  onArchive: () => void;
}) {
  const [value, setValue] = useState(name);
  return (
    <li className={archived ? "name-row is-archived" : "name-row"}>
      <input value={value} onChange={(event) => setValue(event.target.value)} maxLength={255} />
      <button type="button" className="text-button" onClick={() => value.trim() && value.trim() !== name && onRename(value.trim())}>
        Сохранить
      </button>
      <button type="button" className="text-button" onClick={onArchive}>
        {archived ? "Вернуть" : "В архив"}
      </button>
    </li>
  );
}
