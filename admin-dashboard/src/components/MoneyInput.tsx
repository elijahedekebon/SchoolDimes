"use client";

import { TextInput, type TextInputProps } from "@mantine/core";

import { toCents } from "@/lib/money";

/** Decimal-string amount input ("" = empty / no limit). Never parses to float. */
export function MoneyInput({
  value,
  onChange,
  allowEmpty = true,
  ...rest
}: Omit<TextInputProps, "value" | "onChange"> & { value: string; onChange: (v: string) => void; allowEmpty?: boolean }) {
  const bad = value !== "" && (toCents(value) === null || (toCents(value) ?? 0n) < 0n);
  return (
    <TextInput
      {...rest}
      inputMode="decimal"
      value={value}
      onChange={(e) => onChange(e.currentTarget.value.trim())}
      error={bad ? "0.00" : !allowEmpty && value === "" ? " " : rest.error}
      leftSection={<span style={{ fontSize: 11 }}>UGX</span>}
      leftSectionWidth={44}
    />
  );
}
