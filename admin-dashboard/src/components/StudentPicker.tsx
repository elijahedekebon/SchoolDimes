"use client";

import { Select } from "@mantine/core";
import { useDebouncedValue } from "@mantine/hooks";
import { useState } from "react";

import type { Paginated } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Student } from "@/lib/types";

/** Searchable student select backed by GET /students/?search= (server-side). */
export function StudentPicker({
  value,
  onChange,
  label,
  required,
  w = 260,
}: {
  value: string | null;
  onChange: (id: string | null, student?: Student) => void;
  label: string;
  required?: boolean;
  w?: number | string;
}) {
  const [search, setSearch] = useState("");
  const [q] = useDebouncedValue(search, 300);
  const { data } = useApi<Paginated<Student>>("/students/", { search: q, page_size: 25 });
  const rows = data?.results ?? [];
  return (
    <Select
      label={label}
      required={required}
      searchable
      clearable
      w={w}
      size="xs"
      value={value}
      searchValue={search}
      onSearchChange={setSearch}
      filter={({ options }) => options}
      onChange={(v) => onChange(v, rows.find((s) => String(s.id) === v))}
      data={rows.map((s) => ({ value: String(s.id), label: `${s.name} (${s.class_name || "—"})` }))}
      nothingFoundMessage="—"
    />
  );
}
