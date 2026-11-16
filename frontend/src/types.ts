export type Unit = "шт" | "м" | "см" | "г" | "упаковка";

export const UNITS: Unit[] = ["шт", "м", "см", "г", "упаковка"];

export type ComponentType = {
  id: number;
  guid: string;
  name: string;
  parent_id: number | null;
  is_system: boolean;
  is_archived: boolean;
};

export type Color = {
  id: number;
  guid: string;
  name: string;
  is_archived: boolean;
};

export type Component = {
  id: number;
  guid: string;
  name: string;
  cost: number;
  unit: Unit;
  article: string | null;
  image: string;
  image_preview: string;
  type_id: number;
  color_id: number | null;
  type: ComponentType;
  color: Color | null;
  shops: string[];
  is_archived: boolean;
};

export type IdsResult = {
  ids: number[];
  skipped: { id: number; reason: string }[];
};
