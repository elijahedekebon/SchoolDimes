"use client";

import { Select } from "@mantine/core";

import type { Paginated } from "@/lib/api";
import { useApi } from "@/lib/hooks";

export type SchoolRow = { id: number; name: string };

/** platform_admin only: GET /schools/. */
export function SchoolPicker({ value, onChange, label, clearable = true }: { value: string | null; onChange: (v: string | null) => void; label: string; clearable?: boolean }) {
  const { data } = useApi<Paginated<SchoolRow>>("/schools/", { page_size: 100 });
  return (
    <Select
      size="xs"
      label={label}
      searchable
      clearable={clearable}
      w={280}
      value={value}
      onChange={onChange}
      data={(data?.results ?? []).map((s) => ({ value: String(s.id), label: s.name }))}
    />
  );
}
