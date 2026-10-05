"use client";

import type { Paginated } from "./api";
import { useApi } from "./hooks";

type Named = { id: number; name: string };

/** id -> name maps for categories, products and merchants (policy displays). */
export function useCatalogue() {
  const cats = useApi<Paginated<Named & { is_unhealthy: boolean }>>("/product-categories/", { page_size: 100 });
  const prods = useApi<Paginated<Named>>("/products/", { page_size: 100 });
  const merchants = useApi<Paginated<Named>>("/merchants/", { page_size: 100 });
  const map = (rows?: Named[]) => new Map((rows ?? []).map((r) => [r.id, r.name]));
  return {
    categories: map(cats.data?.results),
    products: map(prods.data?.results),
    merchants: map(merchants.data?.results),
    names: (ids: number[] | null | undefined, m: Map<number, string>) =>
      ids && ids.length ? ids.map((i) => m.get(i) ?? `#${i}`).join(", ") : "—",
  };
}
