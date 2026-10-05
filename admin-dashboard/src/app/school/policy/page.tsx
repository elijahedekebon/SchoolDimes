"use client";

import { Badge, Button, Card, Group, MultiSelect, NumberInput, SimpleGrid, Stack, Switch, Text } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { MoneyInput } from "@/components/MoneyInput";
import { ConfirmAction, DataTable, ErrorAlert, Loading, Money, PageHeader } from "@/components/ui";
import { api, type Paginated } from "@/lib/api";
import { useCatalogue } from "@/lib/catalogue";
import { formatDateTime } from "@/lib/dates";
import { useApi, usePaginated } from "@/lib/hooks";

type Policy = {
  id: number;
  student: number | null;
  student_name: string | null;
  daily_spend_cap: string | null;
  weekly_spend_cap: string | null;
  per_transaction_cap: string | null;
  p2p_daily_cap: string | null;
  p2p_enabled: boolean | null;
  low_balance_threshold: string | null;
  blocked_categories: number[];
  allowed_categories: number[];
  blocked_items: number[];
  blocked_merchants: number[];
  allowed_merchants: number[];
  updated_by_role: string | null;
  updated_by_name: string | null;
  updated_at: string;
};
type Settings = {
  offline_spend_ceiling: string;
  pin_lockout_threshold: number;
  device_stale_after_hours: number;
  attendance_notify_guardians: boolean;
  attendance_on_canteen_devices: boolean;
};

const CAPS = ["daily_spend_cap", "weekly_spend_cap", "per_transaction_cap", "p2p_daily_cap", "low_balance_threshold"] as const;
const LISTS = ["blocked_categories", "allowed_categories", "blocked_items", "blocked_merchants", "allowed_merchants"] as const;

export default function PolicyPage() {
  const t = useTranslations("policy");
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <Stack>
        <DefaultPolicy />
        <SchoolSettings />
        <Overrides />
      </Stack>
    </>
  );
}

function DefaultPolicy() {
  const t = useTranslations("policy");
  const res = useApi<Paginated<Policy>>("/policies/", { kind: "default" });
  const cat = useCatalogue();
  const policy = res.data?.results[0];
  const [form, setForm] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  useEffect(() => {
    if (!policy) return;
    const f: Record<string, unknown> = { p2p_enabled: policy.p2p_enabled !== false };
    for (const k of CAPS) f[k] = policy[k] ?? "";
    for (const k of LISTS) f[k] = policy[k].map(String);
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setForm(f);
  }, [policy]);
  if (res.error) return <ErrorAlert error={res.error} />;
  if (!form || !policy) return <Loading />;
  const opts = (m: Map<number, string>) => Array.from(m.entries()).map(([id, name]) => ({ value: String(id), label: name }));
  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      const body: Record<string, unknown> = { p2p_enabled: form.p2p_enabled };
      for (const k of CAPS) body[k] = form[k] === "" ? null : form[k];
      for (const k of LISTS) body[k] = (form[k] as string[]).map(Number);
      await api.patch(`/policies/${policy.id}/`, body);
      notifications.show({ color: "green", message: t("saved") });
      res.reload();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <Card withBorder>
      <Text fw={600}>{t("defaults")}</Text>
      <Text size="xs" c="dimmed" mb="sm">
        {t("defaultsHelp")}
      </Text>
      <SimpleGrid cols={{ base: 1, sm: 2, md: 3 }}>
        {CAPS.map((k) => (
          <MoneyInput key={k} label={t(k)} description={t("blankNoLimit")} value={form[k] as string} onChange={(v) => setForm({ ...form, [k]: v })} />
        ))}
        <Switch mt="lg" label={t("p2p_enabled")} checked={!!form.p2p_enabled} onChange={(e) => setForm({ ...form, p2p_enabled: e.currentTarget.checked })} />
      </SimpleGrid>
      <SimpleGrid cols={{ base: 1, md: 2 }} mt="sm">
        <MultiSelect label={t("blocked_categories")} data={opts(cat.categories)} value={form.blocked_categories as string[]} onChange={(v) => setForm({ ...form, blocked_categories: v })} searchable />
        <MultiSelect label={t("allowed_categories")} description={t("emptyAll")} data={opts(cat.categories)} value={form.allowed_categories as string[]} onChange={(v) => setForm({ ...form, allowed_categories: v })} searchable />
        <MultiSelect label={t("blocked_items")} data={opts(cat.products)} value={form.blocked_items as string[]} onChange={(v) => setForm({ ...form, blocked_items: v })} searchable />
        <MultiSelect label={t("blocked_merchants")} data={opts(cat.merchants)} value={form.blocked_merchants as string[]} onChange={(v) => setForm({ ...form, blocked_merchants: v })} searchable />
        <MultiSelect label={t("allowed_merchants")} description={t("emptyAll")} data={opts(cat.merchants)} value={form.allowed_merchants as string[]} onChange={(v) => setForm({ ...form, allowed_merchants: v })} searchable />
      </SimpleGrid>
      <ErrorAlert error={error} />
      <Group justify="space-between" mt="md">
        <Text size="xs" c="dimmed">
          {t("lastChanged", { who: policy.updated_by_name ?? "—", when: formatDateTime(policy.updated_at) })}
        </Text>
        <Button onClick={save} loading={busy}>
          {t("save")}
        </Button>
      </Group>
    </Card>
  );
}

function SchoolSettings() {
  const t = useTranslations("policy");
  const res = useApi<Settings>("/school-settings/");
  const [form, setForm] = useState<Settings | null>(null);
  const [error, setError] = useState<unknown>(null);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (res.data) setForm(res.data);
  }, [res.data]);
  if (!form) return res.error ? <ErrorAlert error={res.error} /> : <Loading />;
  const save = async () => {
    setError(null);
    try {
      await api.patch("/school-settings/", form);
      notifications.show({ color: "green", message: t("saved") });
      res.reload();
    } catch (e) {
      setError(e);
    }
  };
  return (
    <Card withBorder>
      <Text fw={600}>{t("posSettings")}</Text>
      <Text size="xs" c="dimmed" mb="sm">
        {t("posSettingsHelp")}
      </Text>
      <SimpleGrid cols={{ base: 1, sm: 3 }}>
        <MoneyInput label={t("offline_spend_ceiling")} description={t("offlineHelp")} value={form.offline_spend_ceiling} allowEmpty={false} onChange={(v) => setForm({ ...form, offline_spend_ceiling: v })} />
        <NumberInput label={t("pin_lockout_threshold")} description={t("pinLockHelp")} min={1} max={20} value={form.pin_lockout_threshold} onChange={(v) => setForm({ ...form, pin_lockout_threshold: Number(v) || 1 })} />
        <NumberInput label={t("device_stale_after_hours")} min={1} max={720} value={form.device_stale_after_hours} onChange={(v) => setForm({ ...form, device_stale_after_hours: Number(v) || 1 })} />
      </SimpleGrid>
      <Stack gap="xs" mt="sm">
        <Switch label={t("attendance_notify_guardians")} checked={form.attendance_notify_guardians} onChange={(e) => setForm({ ...form, attendance_notify_guardians: e.currentTarget.checked })} />
        <Switch label={t("attendance_on_canteen_devices")} checked={form.attendance_on_canteen_devices} onChange={(e) => setForm({ ...form, attendance_on_canteen_devices: e.currentTarget.checked })} />
      </Stack>
      <ErrorAlert error={error} />
      <Group justify="flex-end" mt="md">
        <Button onClick={save}>{t("save")}</Button>
      </Group>
    </Card>
  );
}

function Overrides() {
  const t = useTranslations("policy");
  const list = usePaginated<Policy>("/policies/", { kind: "override" });
  const cap = (v: string | null) => (v === null ? "—" : <Money value={v} />);
  return (
    <Card withBorder>
      <Text fw={600}>{t("overrides")}</Text>
      <Text size="xs" c="dimmed" mb="sm">
        {t("overridesHelp")}
      </Text>
      <DataTable<Policy>
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        empty={t("noOverrides")}
        columns={[
          { key: "student_name", header: t("student"), render: (p) => <Link href={`/school/students/${p.student}`}>{p.student_name}</Link> },
          { key: "daily", header: t("daily_spend_cap"), render: (p) => cap(p.daily_spend_cap) },
          { key: "ptx", header: t("per_transaction_cap"), render: (p) => cap(p.per_transaction_cap) },
          { key: "p2p", header: t("p2p_enabled"), render: (p) => (p.p2p_enabled === false ? t("off") : t("inherit")) },
          { key: "blocks", header: t("blocks"), render: (p) => p.blocked_items.length + p.blocked_categories.length + p.blocked_merchants.length },
          {
            key: "by",
            header: t("setBy"),
            render: (p) => (
              <Group gap={4}>
                {p.updated_by_name ?? "—"}
                {p.updated_by_role && <Badge size="xs" color={p.updated_by_role === "parent" ? "grape" : "blue"}>{p.updated_by_role}</Badge>}
              </Group>
            ),
          },
          { key: "updated_at", header: t("updated"), render: (p) => formatDateTime(p.updated_at) },
          {
            key: "actions",
            header: "",
            render: (p) => (
              <ConfirmAction label={t("remove")} color="red" title={t("removeTitle")} description={t("removeHelp", { name: p.student_name ?? "" })} onConfirm={() => api.del(`/policies/${p.id}/`)} onDone={list.reload} />
            ),
          },
        ]}
      />
    </Card>
  );
}
