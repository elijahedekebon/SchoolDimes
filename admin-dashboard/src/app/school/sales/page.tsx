"use client";

import { Card, Group, SimpleGrid, Tabs, Text } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { ChoiceFilter, DateRange } from "@/components/filters";
import { Flags, TransactionDrawer } from "@/components/pos";
import { DataTable, ErrorAlert, Money, PageHeader, Stat, StatusBadge } from "@/components/ui";
import { kampalaToday, formatDateTime, shiftDay } from "@/lib/dates";
import { useApi, usePaginated } from "@/lib/hooks";
import { formatUGX, toCents } from "@/lib/money";
import type { Device, PosTransaction, SalesSummary } from "@/lib/types";
import type { Paginated } from "@/lib/api";

// Chart heights only: values plotted are whole shillings (display), never used for money maths.
const shillings = (v: string) => Number((toCents(v) ?? 0n) / 100n);

export default function SalesPage() {
  const t = useTranslations("sales");
  const today = kampalaToday();
  const [range, setRange] = useState({ from: shiftDay(today, -6), to: today });
  const [device, setDevice] = useState("");
  const [syncStatus, setSyncStatus] = useState("");
  const [openId, setOpenId] = useState<number | null>(null);
  const summary = useApi<SalesSummary>("/analytics/sales-summary/", range);
  const devices = useApi<Paginated<Device>>("/pos/devices/", { page_size: 100 });
  const txns = usePaginated<PosTransaction>("/pos/transactions/", { device, sync_status: syncStatus });
  const s = summary.data;

  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} actions={<DateRange {...range} onChange={setRange} />} />
      <ErrorAlert error={summary.error} />
      {s && (
        <>
          <SimpleGrid cols={{ base: 2, md: 4 }}>
            <Card withBorder>
              <Stat label={t("transactions")} value={s.totals.transactions} />
            </Card>
            <Card withBorder>
              <Stat label={t("gross")} value={formatUGX(s.totals.gross_amount)} hint={t("grossHint")} />
            </Card>
            <Card withBorder>
              <Stat label={t("collected")} value={formatUGX(s.totals.collected_amount)} hint={t("collectedHint")} />
            </Card>
            <Card withBorder>
              <Stat label={t("shortfall")} value={formatUGX(s.totals.shortfall_amount)} color={s.totals.shortfall_amount !== "0.00" ? "orange" : undefined} />
            </Card>
          </SimpleGrid>
          <Card withBorder mt="md">
            <Text fw={600} mb="xs">
              {t("byDay")}
            </Text>
            <div style={{ width: "100%", height: 240 }}>
              <ResponsiveContainer>
                <BarChart data={s.by_day.map((d) => ({ date: d.date, collected: shillings(d.collected_amount) }))}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" fontSize={11} />
                  <YAxis fontSize={11} />
                  <Tooltip formatter={(v) => formatUGX(String(v))} />
                  <Bar dataKey="collected" fill="var(--mantine-primary-color-filled)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </Card>
          <Tabs defaultValue="day" mt="md">
            <Tabs.List>
              <Tabs.Tab value="day">{t("byDay")}</Tabs.Tab>
              <Tabs.Tab value="device">{t("byDevice")}</Tabs.Tab>
              <Tabs.Tab value="merchant">{t("byMerchant")}</Tabs.Tab>
            </Tabs.List>
            <Tabs.Panel value="day" pt="sm">
              <BucketTable rows={s.by_day.map((r) => ({ ...r, label: r.date }))} />
            </Tabs.Panel>
            <Tabs.Panel value="device" pt="sm">
              <BucketTable rows={s.by_device.map((r) => ({ ...r, label: r.device_name }))} />
            </Tabs.Panel>
            <Tabs.Panel value="merchant" pt="sm">
              <BucketTable rows={s.by_merchant.map((r) => ({ ...r, label: r.merchant_name }))} />
            </Tabs.Panel>
          </Tabs>
        </>
      )}

      <Group mt="xl" mb="xs" justify="space-between" align="flex-end">
        <Text fw={600}>{t("allTransactions")}</Text>
        <Group>
          <ChoiceFilter
            label={t("device")}
            value={device}
            onChange={setDevice}
            options={(devices.data?.results ?? []).map((d) => ({ value: String(d.id), label: d.device_name }))}
          />
          <ChoiceFilter
            label={t("syncStatus")}
            value={syncStatus}
            onChange={setSyncStatus}
            options={["applied", "shortfall", "rejected"].map((v) => ({ value: v, label: v }))}
          />
        </Group>
      </Group>
      <DataTable<PosTransaction>
        testId="transactions-table"
        rows={txns.data?.results}
        loading={txns.loading}
        error={txns.error}
        page={txns.page}
        totalPages={txns.totalPages}
        onPage={txns.setPage}
        onRowClick={(r) => setOpenId(r.id)}
        columns={[
          { key: "id", header: "#" },
          { key: "time", header: t("deviceTime"), render: (r) => formatDateTime(r.device_local_timestamp) },
          { key: "student_name", header: t("student") },
          { key: "device_name", header: t("device") },
          { key: "amount", header: t("amount"), render: (r) => <Money value={r.amount} /> },
          { key: "sync_status", header: t("syncStatus"), render: (r) => <StatusBadge status={r.sync_status} /> },
          { key: "flags", header: t("flags"), render: (r) => <Flags flags={r.flags} /> },
        ]}
      />
      <TransactionDrawer id={openId} onClose={() => setOpenId(null)} />
    </>
  );
}

function BucketTable({ rows }: { rows: Array<{ label: string; transactions: number; gross_amount: string; collected_amount: string }> }) {
  const t = useTranslations("sales");
  return (
    <DataTable
      rows={rows.map((r, i) => ({ ...r, id: i }))}
      columns={[
        { key: "label", header: "" },
        { key: "transactions", header: t("transactions") },
        { key: "gross", header: t("gross"), render: (r) => <Money value={r.gross_amount} /> },
        { key: "collected", header: t("collected"), render: (r) => <Money value={r.collected_amount} /> },
      ]}
    />
  );
}
