"use client";

import { Group, Select, TextInput } from "@mantine/core";
import { useTranslations } from "next-intl";

export function DateRange({
  from,
  to,
  onChange,
}: {
  from: string;
  to: string;
  onChange: (v: { from: string; to: string }) => void;
}) {
  const t = useTranslations("common");
  return (
    <Group gap="xs">
      <TextInput type="date" size="xs" label={t("from")} value={from} max={to} onChange={(e) => onChange({ from: e.currentTarget.value, to })} />
      <TextInput type="date" size="xs" label={t("to")} value={to} min={from} onChange={(e) => onChange({ from, to: e.currentTarget.value })} />
    </Group>
  );
}

export function DayPicker({ value, onChange, label }: { value: string; onChange: (v: string) => void; label?: string }) {
  const t = useTranslations("common");
  return <TextInput type="date" size="xs" label={label ?? t("date")} value={value} onChange={(e) => onChange(e.currentTarget.value)} />;
}

export function ChoiceFilter({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: Array<{ value: string; label: string }>;
}) {
  const t = useTranslations("common");
  return (
    <Select
      size="xs"
      label={label}
      value={value}
      onChange={(v) => onChange(v ?? "")}
      data={[{ value: "", label: t("all") }, ...options]}
      allowDeselect={false}
      w={180}
    />
  );
}
