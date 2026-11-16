import type { Color, Component, ComponentType, IdsResult, Unit } from "./types";

async function readError(response: Response): Promise<string> {
  try {
    const body = (await response.json()) as { detail?: unknown };
    if (typeof body.detail === "string") return body.detail;
    if (Array.isArray(body.detail) && body.detail.length > 0) {
      const first = body.detail[0] as { msg?: string };
      if (first.msg) return first.msg;
    }
  } catch {
    return `Ошибка ${response.status}`;
  }
  return `Ошибка ${response.status}`;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`/api${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
  });
  if (!response.ok) throw new Error(await readError(response));
  return (await response.json()) as T;
}

export function listTypes(includeArchived: boolean) {
  const query = new URLSearchParams({ limit: "200" });
  if (includeArchived) query.set("include_archived", "true");
  return request<ComponentType[]>(`/component-type/list?${query}`);
}

export function listColors(includeArchived: boolean) {
  const query = new URLSearchParams({ limit: "200" });
  if (includeArchived) query.set("include_archived", "true");
  return request<Color[]>(`/color/list?${query}`);
}

export function listComponents(search: string, includeArchived: boolean) {
  const query = new URLSearchParams({ limit: "200" });
  if (search.trim()) query.set("search", search.trim());
  if (includeArchived) query.set("include_archived", "true");
  return request<Component[]>(`/component/list?${query}`);
}

export type ComponentPayload = {
  name: string;
  cost: number;
  unit: Unit;
  article: string | null;
  type_id: number;
  color_id: number | null;
  shops: string[];
  image_base64?: string;
};

export function createComponent(body: ComponentPayload) {
  return request<Component>("/component/create", { method: "POST", body: JSON.stringify(body) });
}

export function updateComponent(id: number, body: ComponentPayload) {
  return request<Component>(`/component/${id}`, { method: "PATCH", body: JSON.stringify(body) });
}

export function archiveComponents(ids: number[]) {
  return request<IdsResult>("/component/archive", { method: "PATCH", body: JSON.stringify({ ids }) });
}

export function unarchiveComponents(ids: number[]) {
  return request<IdsResult>("/component/unarchive", { method: "PATCH", body: JSON.stringify({ ids }) });
}

export function createType(name: string, parentId: number) {
  return request<ComponentType>("/component-type/create", {
    method: "POST",
    body: JSON.stringify({ name, parent_id: parentId }),
  });
}

export function renameType(id: number, name: string) {
  return request<ComponentType>(`/component-type/${id}`, {
    method: "PATCH",
    body: JSON.stringify({ name }),
  });
}

export function archiveTypes(ids: number[]) {
  return request<IdsResult>("/component-type/archive", { method: "PATCH", body: JSON.stringify({ ids }) });
}

export function unarchiveTypes(ids: number[]) {
  return request<IdsResult>("/component-type/unarchive", { method: "PATCH", body: JSON.stringify({ ids }) });
}

export function createColor(name: string) {
  return request<Color>("/color/create", { method: "POST", body: JSON.stringify({ name }) });
}

export function renameColor(id: number, name: string) {
  return request<Color>(`/color/${id}`, { method: "PATCH", body: JSON.stringify({ name }) });
}

export function archiveColors(ids: number[]) {
  return request<IdsResult>("/color/archive", { method: "PATCH", body: JSON.stringify({ ids }) });
}

export function unarchiveColors(ids: number[]) {
  return request<IdsResult>("/color/unarchive", { method: "PATCH", body: JSON.stringify({ ids }) });
}
