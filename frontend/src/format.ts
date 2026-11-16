import type { IdsResult } from "./types";

const SKIP_REASON: Record<string, string> = {
  "not found": "запись не найдена",
  "already archived": "уже в архиве",
  "already active": "уже в каталоге",
  "system type": "основной тип остаётся на месте",
  "used by active components": "его ещё используют комплектующие",
  "type is archived": "сначала верните тип из архива",
  "name already used": "такое имя уже занято",
};

export function money(value: number): string {
  return new Intl.NumberFormat("ru-RU", { style: "currency", currency: "RUB" }).format(value);
}

export function roundMoney(value: number): number {
  return Math.round((value + Number.EPSILON) * 100) / 100;
}

export function salePrice(cost: number, markupPercent: number): number {
  return roundMoney(cost * (1 + markupPercent / 100));
}

export function markupFromSale(cost: number, sale: number): number {
  if (!(cost > 0) || !Number.isFinite(sale)) return 30;
  const percent = (sale / cost - 1) * 100;
  if (!Number.isFinite(percent)) return 30;
  return Math.round(Math.min(300, Math.max(0, percent)));
}

export function skipMessage(result: IdsResult): string | null {
  if (result.skipped.length === 0) return null;
  const text = result.skipped.map((item) => SKIP_REASON[item.reason] ?? item.reason).join(". ");
  return text.endsWith(".") ? text : `${text}.`;
}
