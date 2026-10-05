"use client";

import { Alert, Card, Group, SimpleGrid, Tabs, Text } from "@mantine/core";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { Suspense, useState } from "react";

import { Flags, TransactionDrawer } from "@/components/pos";
import { SchoolPicker } from "@/components/SchoolPicker";
import { DataTable, Money, PageHeader, Stat, StatusBadge } from "@/components/ui";
import { formatDateTime, kampalaToday, shiftDay } from "@/lib/dates";
import { useApi, usePaginated } from "@/lib/hooks";
import { formatUGX } from "@/lib/money";
import type { Card as CardT, Device, PosTransaction, SalesSummary, Student } from "@/lib/types";

export default function SupportPage() {
  return (
    <Suspense>
      <Support />
    </Suspense>
  );
}

/** Read-only cross-tenant support views. Every request names the school (?school=). */
function Support() {
  const t = useTranslations("support");
  const router = useRouter();
  const params = useSearchParams();
  const school = params.get("school");
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} actions={<SchoolPicker label={t("school")} value={school} onChange={(v) => router.replace(v ? `/platform/support?school=${v}` : "/platform/support")} />} />
      <Alert variant="light" color="gray" mb="md">
        <Text size="sm">{t("readOnly")}</Text>
      </Alert>
      {!school ? <Text c="dimmed">{t("pick")}</Text> : <SchoolViews school={school} />}
    </>
  );
}

function SchoolViews({ school }: { school: string }) {
  const t = useTranslations("support");
  const today = kampalaToday();
  const sales = useApi<SalesSummary>("/analytics/sales-summary/", { school, from: shiftDay(today, -29), to: today });
  const [txn, setTxn] = useState<number | null>(null);
  const students = usePaginated<Student>("/students/", { school });
  const devices = usePaginated<Device>("/pos/devices/", { school });
  const cards = usePaginated<CardT & { student_name: string }>("/cards/", { school });
  const txns = usePaginated<PosTransaction>("/pos/transactions/", { school });
  return (
    <>
      {sales.data && (
        <SimpleGrid cols={{ base: 2, md: 4 }} mb="md">
          <Card withBorder>
            <Stat label={t("sales30")} value={formatUGX(sales.data.totals.collected_amount)} hint={`${sales.data.totals.transactions}`} />
          </Card>
          <Card withBorder>
            <Stat label={t("shortfall30")} value={formatUGX(sales.data.totals.shortfall_amount)} />
          </Card>
        </SimpleGrid>
      )}
      <Tabs defaultValue="students">
        <Tabs.List>
          <Tabs.Tab value="students">{t("students")}</Tabs.Tab>
          <Tabs.Tab value="cards">{t("cards")}</Tabs.Tab>
          <Tabs.Tab value="devices">{t("devices")}</Tabs.Tab>
          <Tabs.Tab value="transactions">{t("transactions")}</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="students" pt="md">
          <DataTable<Student> rows={students.data?.results} loading={students.loading} error={students.error} page={students.page} totalPages={students.totalPages} onPage={students.setPage} columns={[{ key: "id", header: "#" }, { key: "name", header: t("name") }, { key: "class_name", header: t("class") }]} />
        </Tabs.Panel>
        <Tabs.Panel value="cards" pt="md">
          <DataTable rows={cards.data?.results} loading={cards.loading} error={cards.error} page={cards.page} totalPages={cards.totalPages} onPage={cards.setPage} columns={[{ key: "student_name", header: t("student") }, { key: "card_uid", header: t("uid"), render: (c) => <span className="mono">{c.card_uid}</span> }, { key: "status", header: t("status"), render: (c) => <StatusBadge status={c.status} /> }, { key: "updated_at", header: t("updated"), render: (c) => formatDateTime(c.updated_at) }]} />
        </Tabs.Panel>
        <Tabs.Panel value="devices" pt="md">
          <DataTable<Device> rows={devices.data?.results} loading={devices.loading} error={devices.error} page={devices.page} totalPages={devices.totalPages} onPage={devices.setPage} columns={[{ key: "device_name", header: t("name") }, { key: "device_role", header: t("role") }, { key: "status", header: t("status"), render: (d) => <StatusBadge status={d.status} /> }, { key: "last_seen_at", header: t("lastSeen"), render: (d) => formatDateTime(d.last_seen_at) }, { key: "last_sync_at", header: t("lastSync"), render: (d) => formatDateTime(d.last_sync_at) }, { key: "app_version", header: t("version"), render: (d) => d.app_version || "—" }]} />
        </Tabs.Panel>
        <Tabs.Panel value="transactions" pt="md">
          <DataTable<PosTransaction> rows={txns.data?.results} loading={txns.loading} error={txns.error} page={txns.page} totalPages={txns.totalPages} onPage={txns.setPage} onRowClick={(r) => setTxn(r.id)} columns={[{ key: "id", header: "#" }, { key: "time", header: t("when"), render: (r) => formatDateTime(r.device_local_timestamp) }, { key: "student_name", header: t("student") }, { key: "device_name", header: t("device") }, { key: "amount", header: t("amount"), render: (r) => <Money value={r.amount} /> }, { key: "sync_status", header: t("status"), render: (r) => <Group gap={4}><StatusBadge status={r.sync_status} /><Flags flags={r.flags} /></Group> }]} />
        </Tabs.Panel>
      </Tabs>
      <TransactionDrawer id={txn} onClose={() => setTxn(null)} />
    </>
  );
}
