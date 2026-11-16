import { useState } from "react";

export const PAGE_SIZE = 24;

export function usePageReset(filterKey: string): [number, (page: number) => void] {
  const [page, setPage] = useState(1);
  const [seen, setSeen] = useState(filterKey);
  if (seen !== filterKey) {
    setSeen(filterKey);
    if (page !== 1) setPage(1);
  }
  return [page, setPage];
}

function pageNumbers(page: number, pages: number): number[] {
  if (pages <= 7) return Array.from({ length: pages }, (_, index) => index + 1);
  const start = Math.max(1, Math.min(page - 2, pages - 4));
  const end = Math.min(pages, start + 4);
  return Array.from({ length: end - start + 1 }, (_, index) => start + index);
}

type Props = {
  page: number;
  total: number;
  onPage: (page: number) => void;
};

export function Pager({ page, total, onPage }: Props) {
  const pages = Math.max(1, Math.ceil(total / PAGE_SIZE));
  if (total <= PAGE_SIZE) return null;

  function go(next: number) {
    onPage(next);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  return (
    <nav className="pager" aria-label="Страницы">
      <button type="button" aria-label="Предыдущая страница" disabled={page <= 1} onClick={() => go(page - 1)}>
        ‹
      </button>
      {pageNumbers(page, pages).map((number) => (
        <button
          key={number}
          type="button"
          aria-label={`Страница ${number}`}
          aria-current={number === page ? "page" : undefined}
          onClick={() => go(number)}
        >
          {number}
        </button>
      ))}
      <button type="button" aria-label="Следующая страница" disabled={page >= pages} onClick={() => go(page + 1)}>
        ›
      </button>
    </nav>
  );
}
