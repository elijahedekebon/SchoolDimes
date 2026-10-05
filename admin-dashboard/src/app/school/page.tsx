"use client";

import { Alert, Card, SimpleGrid, Text } from "@mantine/core";
import { useTranslations } from "next-intl";

import { ErrorAlert, PageHeader, Stat } from "@/components/ui";
import type { Paginated } from "@/lib/api";
import { kampalaToday } from "@/lib/dates";
import { useApi } from "@/lib/hooks";
import { formatUGX } from "@/lib/money";
import type { Reconciliation, SalesSummary } from "@/lib/types";

const count = (d?: Paginated<unknown>) => (d ? String(d.count) : "…");

export default function OverviewPage() {
  const t = useTranslations("overview");
  const today = kampalaToday();
  const sales = useApi<SalesSummary>("/analytics/sales-summary/", { from: today, to: today });
  const recon = useApi<Reconciliation>("/analytics/reconciliation/", { date: today });
  const reviews = useApi<Paginated<unknown>>("/pos/shortfalls/", { page_size: 1 });
  const disputes = useApi<Paginated<unknown>>("/disputes/", { status: "open", page_size: 1 });
  const alerts = useApi<Paginated<unknown>>("/p2p-alerts/", { status: "open", page_size: 1 });
  const stale = useApi<Paginated<unknown>>("/pos/devices/", { stale: "true", page_size: 1 });
  const requests = useApi<Paginated<unknown>>("/privacy/data-requests/", { status: "pending", page_size: 1 });

  const error = sales.error || recon.error;
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle", { date: today })} />
      <ErrorAlert error={error} />
      <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} mt="md">
        <Card withBorder>
          <Stat
            label={t("salesToday")}
            value={sales.data ? formatUGX(sales.data.totals.collected_amount) : "…"}
            hint={sales.data ? t("salesCount", { count: sales.data.totals.transactions }) : undefined}
            href="/school/sales"
          />
        </Card>
        <Card withBorder>
          <Stat
            label={t("depositsConfirmed")}
            value={recon.data ? formatUGX(recon.data.deposits.confirmed_amount) : "…"}
            hint={recon.data ? t("depositsHint", { confirmed: recon.data.deposits.confirmed_count, pending: recon.data.deposits.pending_count }) : undefined}
            href="/school/reconciliation"
          />
        </Card>
        <Card withBorder>
          <Stat label={t("reviewQueue")} value={count(reviews.data)} hint={t("reviewHint")} href="/school/shortfalls" color={reviews.data?.count ? "orange" : undefined} />
        </Card>
        <Card withBorder>
          <Stat label={t("openDisputes")} value={count(disputes.data)} href="/school/disputes" color={disputes.data?.count ? "orange" : undefined} />
        </Card>
        <Card withBorder>
          <Stat label={t("openP2pAlerts")} value={count(alerts.data)} href="/school/p2p-alerts" color={alerts.data?.count ? "orange" : undefined} />
        </Card>
        <Card withBorder>
          <Stat label={t("staleDevices")} value={count(stale.data)} hint={t("staleHint")} href="/school/devices" color={stale.data?.count ? "red" : undefined} />
        </Card>
        <Card withBorder>
          <Stat label={t("pendingRequests")} value={count(requests.data)} href="/school/privacy" />
        </Card>
        <Card withBorder>
          <Stat
            label={t("books")}
            value={recon.data ? (recon.data.books_balanced ? t("balanced") : t("unbalanced")) : "…"}
            color={recon.data && !recon.data.books_balanced ? "red" : "green"}
            hint={t("booksHint")}
            href="/school/reconciliation"
          />
        </Card>
      </SimpleGrid>
      <Alert mt="lg" color="gray" variant="light">
        <Text size="sm">{t("simulatorNote")}</Text>
      </Alert>
    </>
  );
}
