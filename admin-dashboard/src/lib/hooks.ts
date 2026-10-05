"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError, api, type Paginated, type Query } from "./api";

export type Loadable<T> = { data: T | undefined; error: ApiError | null; loading: boolean; reload: () => void };

type Result<T> = { key: string; data?: T; error: ApiError | null };

/** GET a path (null = skip). Re-fetches when the path or query changes. */
export function useApi<T>(path: string | null, query?: Query): Loadable<T> {
  const [tick, setTick] = useState(0);
  const [result, setResult] = useState<Result<T> | null>(null);
  const key = path ? `${path}${JSON.stringify(query ?? {})}#${tick}` : null;
  const latest = useRef<string | null>(null);

  useEffect(() => {
    latest.current = key;
    if (!path || !key) return;
    api
      .get<T>(path, query)
      .then((d) => latest.current === key && setResult({ key, data: d, error: null }))
      .catch(
        (e) =>
          latest.current === key &&
          setResult((prev) => ({
            key,
            data: prev?.data,
            error: e instanceof ApiError ? e : new ApiError(0, { detail: String(e) }),
          })),
      );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  const reload = useCallback(() => setTick((t) => t + 1), []);
  return {
    // keep showing the previous data while a refetch is in flight
    data: result?.data,
    error: result?.key === key ? result.error : null,
    loading: !!key && result?.key !== key,
    reload,
  };
}

/** Server-side paginated list with page + filter state (page resets when filters change). */
export function usePaginated<T>(path: string | null, filters: Query = {}, pageSize = 20) {
  const filterKey = JSON.stringify(filters);
  const [state, setState] = useState({ filterKey, page: 1 });
  const page = state.filterKey === filterKey ? state.page : 1;
  const setPage = useCallback((p: number) => setState({ filterKey, page: p }), [filterKey]);
  const res = useApi<Paginated<T>>(path, { ...filters, page, page_size: pageSize });
  const totalPages = res.data ? Math.max(1, Math.ceil(res.data.count / pageSize)) : 1;
  return { ...res, page, setPage, totalPages };
}
