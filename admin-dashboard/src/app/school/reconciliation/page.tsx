"use client";

import { Alert, Badge, Button, Card, Group, SimpleGrid, Stack, Text } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { DayPicker } from "@/components/filters";
import { DataTable, ErrorAlert, Loading, Money, PageHeader, StatusBadge } from "@/components/ui";
import { downloadCsv } from "@/lib/csv";
import { formatDateTime, kampalaToday } from "@/lib/dates";
import { useApi } from "@/lib/hooks";
import type { Reconciliation } from "@/lib/types";

function Match({ ok }: { ok: boolean }) {
  const t = useTranslations("recon");
  return (
    <Badge color={ok ? "green" : "red"} variant="light">
      {ok ? t("matches") : t("mismatch")}
    </Badge>
  );
}

export default function ReconciliationPage() {
  const t = useTranslations("recon");
  const [date, setDate] = useState(kampalaToday());
  const { data, error, loading } = useApi<Reconciliation>("/analytics/reconciliation/", { date });

  const exportCsv = () => {
    if (!data) return;
    const rows: Array<Record<string, unknown>> = [
      ...data.devices.map((d) => ({
        section: "device",
        name: d.device_name,
        role: d.device_role,
        count: d.transactions,
        rejected: d.rejected,
        amount: d.collected_amount,
        ledger_amount: d.ledger_amount,
        matches: d.matches,
        last_sync_at: d.last_sync_at,
      })),
      { section: "deposits_confirmed", count: data.deposits.confirmed_count, amount: data.deposits.confirmed_amount, ledger_amount: data.deposits.ledger_amount, matches: data.deposits.matches },
      { section: "deposits_pending", count: data.deposits.pending_count, amount: data.deposits.pending_amount },
      { section: "fee_payments", count: data.fee_payments.count, amount: data.fee_payments.amount, ledger_amount: data.fee_payments.ledger_amount, matches: data.fee_payments.matches },
      { section: "unresolved_reviews", count: data.unresolved_reviews.count, amount: data.unresolved_reviews.outstanding_shortfall },
      ...data.pooled_funds.map((f) => ({ section: "pooled_fund", name: f.title, role: f.status, amount: f.balance })),
      ...Object.entries(data.system_wallets).map(([k, v]) => ({ section: "system_wallet", name: k, amount: v })),
      ...data.stale_devices.map((d) => ({ section: "stale_device", name: d.device_name, last_sync_at: d.last_sync_at })),
      { section: "books_total", amount: data.books_total, matches: data.books_balanced },
    ];
    downloadCsv(`reconciliation-${data.date}.csv`, rows, ["section", "name", "role", "count", "rejected", "amount", "ledger_amount", "matches", "last_sync_at"]);
  };

  return (
    <>
      <PageHeader
        title={t("title")}
        subtitle={t("subtitle")}
        actions={
          <Group align="flex-end">
            <DayPicker value={date} onChange={setDate} />
            <Button size="xs" onClick={exportCsv} disabled={!data}>
              {t("export")}
            </Button>
          </Group>
        }
      />
      <ErrorAlert error={error} />
      {loading && !data && <Loading />}
      {data && (
        <Stack>
          <Alert color={data.books_balanced ? "green" : "red"} title={data.books_balanced ? t("balancedTitle") : t("unbalancedTitle")}>
            {t("traceNote")} <Money value={data.books_total} />
          </Alert>
          <Card withBorder>
            <Text fw={600} mb="xs">
              {t("devices")}
            </Text>
            <DataTable
              rows={data.devices.map((d) => ({ ...d, id: d.device_id }))}
              columns={[
                { key: "device_name", header: t("device") },
                { key: "device_role", header: t("role") },
                { key: "status", header: t("status"), render: (r) => <StatusBadge status={r.status} /> },
                { key: "last_sync_at", header: t("lastSync"), render: (r) => formatDateTime(r.last_sync_at) },
                { key: "transactions", header: t("transactions") },
                { key: "rejected", header: t("rejected") },
                { key: "collected", header: t("posCollected"), render: (r) => <Money value={r.collected_amount} /> },
                { key: "ledger", header: t("ledgerAmount"), render: (r) => <Money value={r.ledger_amount} /> },
                { key: "matches", header: "", render: (r) => <Match ok={r.matches} /> },
              ]}
            />
          </Card>
          <SimpleGrid cols={{ base: 1, md: 3 }}>
            <Card withBorder>
              <Group justify="space-between">
                <Text fw={600}>{t("deposits")}</Text>
                <Match ok={data.deposits.matches} />
              </Group>
              <Text size="sm">
                {t("confirmed", { count: data.deposits.confirmed_count })}: <Money value={data.deposits.confirmed_amount} />
              </Text>
              <Text size="sm">
                {t("ledgerAmount")}: <Money value={data.deposits.ledger_amount} />
              </Text>
              <Text size="sm" c="dimmed">
                {t("pending", { count: data.deposits.pending_count })}: <Money value={data.deposits.pending_amount} />
              </Text>
            </Card>
            <Card withBorder>
              <Group justify="space-between">
                <Text fw={600}>{t("fees")}</Text>
                <Match ok={data.fee_payments.matches} />
              </Group>
              <Text size="sm">
                {t("count", { count: data.fee_payments.count })}: <Money value={data.fee_payments.amount} />
              </Text>
              <Text size="sm">
                {t("ledgerAmount")}: <Money value={data.fee_payments.ledger_amount} />
              </Text>
            </Card>
            <Card withBorder>
              <Text fw={600}>{t("reviews")}</Text>
              <Text size="sm">{t("count", { count: data.unresolved_reviews.count })}</Text>
              <Text size="sm">
                {t("outstanding")}: <Money value={data.unresolved_reviews.outstanding_shortfall} />
              </Text>
            </Card>
          </SimpleGrid>
          <SimpleGrid cols={{ base: 1, md: 3 }}>
            <Card withBorder>
              <Text fw={600} mb="xs">
                {t("staleDevices")}
              </Text>
              {data.stale_devices.length === 0 && (
                <Text size="sm" c="dimmed">
                  {t("noneStale")}
                </Text>
              )}
              {data.stale_devices.map((d) => (
                <Text size="sm" key={d.device_id}>
                  {d.device_name} — {formatDateTime(d.last_sync_at)}
                </Text>
              ))}
            </Card>
            <Card withBorder>
              <Text fw={600} mb="xs">
                {t("pooledFunds")}
              </Text>
              {data.pooled_funds.map((f) => (
                <Group key={f.fund_id} justify="space-between">
                  <Text size="sm">{f.title}</Text>
                  <Money value={f.balance} size="sm" />
                </Group>
              ))}
            </Card>
            <Card withBorder>
              <Text fw={600} mb="xs">
                {t("systemWallets")}
              </Text>
              {Object.entries(data.system_wallets).map(([k, v]) => (
                <Group key={k} justify="space-between">
                  <Text size="sm">{k.replace(/_/g, " ")}</Text>
                  <Money value={v} size="sm" />
                </Group>
              ))}
              <Text size="xs" c="dimmed" mt="xs">
                {t("clearingNote")}
              </Text>
            </Card>
          </SimpleGrid>
        </Stack>
      )}
    </>
  );
}
