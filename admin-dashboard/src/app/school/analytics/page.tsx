"use client";

import { Alert, Badge, Card, Group, SimpleGrid, Stack, Text } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";
import { Bar, BarChart, CartesianGrid, Cell, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { DateRange } from "@/components/filters";
import { StudentPicker } from "@/components/StudentPicker";
import { DataTable, ErrorAlert, Money, PageHeader, Stat } from "@/components/ui";
import { kampalaToday, shiftDay } from "@/lib/dates";
import { useApi } from "@/lib/hooks";
import { formatUGX, toCents } from "@/lib/money";

type BestSellers = { results: Array<{ product_id: number | null; name: string; quantity: number; revenue: string; transactions: number }> };
type PeakHours = { timezone: string; results: Array<{ hour: number; transactions: number; gross_amount: string }> };
type Categories = {
  total_item_revenue: string;
  unhealthy_revenue: string;
  unhealthy_share_percent: number | null;
  results: Array<{ category_id: number | null; name: string; is_unhealthy: boolean; quantity: number; revenue: string; share_percent: number | null }>;
};
type Spending = {
  purchases_total: string;
  fees_total: string;
  p2p_sent_total: string;
  p2p_received_total: string;
  topups_total: string;
  refunds_total: string;
  by_day: Array<{ date: string; spent: string }>;
  by_category: Array<{ name: string; is_unhealthy: boolean; quantity: number; revenue: string }>;
  top_items: Array<{ name: string; quantity: number; revenue: string }>;
};

// Chart geometry only (whole shillings); money shown to users always comes from the API strings.
const shillings = (v: string) => Number((toCents(v) ?? 0n) / 100n);

export default function AnalyticsPage() {
  const t = useTranslations("analytics");
  const today = kampalaToday();
  const [range, setRange] = useState({ from: shiftDay(today, -29), to: today });
  const [studentId, setStudentId] = useState<string | null>(null);
  const best = useApi<BestSellers>("/analytics/best-sellers/", { ...range, limit: 10 });
  const peak = useApi<PeakHours>("/analytics/peak-hours/", range);
  const cats = useApi<Categories>("/analytics/category-breakdown/", range);
  const spend = useApi<Spending>(studentId ? `/analytics/students/${studentId}/spending/` : null, range);

  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} actions={<DateRange {...range} onChange={setRange} />} />
      <Stack>
        <SimpleGrid cols={{ base: 1, lg: 2 }}>
          <Card withBorder>
            <Text fw={600}>{t("bestSellers")}</Text>
            <ErrorAlert error={best.error} />
            <div style={{ width: "100%", height: 260 }}>
              <ResponsiveContainer>
                <BarChart data={best.data?.results ?? []} layout="vertical" margin={{ left: 40 }}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis type="number" fontSize={11} allowDecimals={false} />
                  <YAxis type="category" dataKey="name" fontSize={11} width={110} />
                  <Tooltip />
                  <Bar dataKey="quantity" name={t("quantity")} fill="var(--mantine-primary-color-filled)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <DataTable
              rows={(best.data?.results ?? []).map((r, i) => ({ ...r, id: i }))}
              columns={[
                { key: "name", header: t("product") },
                { key: "quantity", header: t("quantity") },
                { key: "transactions", header: t("transactions") },
                { key: "revenue", header: t("revenue"), render: (r) => <Money value={r.revenue} /> },
              ]}
            />
          </Card>
          <Card withBorder>
            <Text fw={600}>{t("peakHours", { tz: peak.data?.timezone ?? "Africa/Kampala" })}</Text>
            <ErrorAlert error={peak.error} />
            <div style={{ width: "100%", height: 260 }}>
              <ResponsiveContainer>
                <BarChart data={peak.data?.results ?? []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" fontSize={11} />
                  <YAxis fontSize={11} allowDecimals={false} />
                  <Tooltip />
                  <Bar dataKey="transactions" name={t("transactions")} fill="var(--mantine-color-orange-6)" />
                </BarChart>
              </ResponsiveContainer>
            </div>
            <DataTable
              rows={(peak.data?.results ?? []).filter((r) => r.transactions > 0).map((r) => ({ ...r, id: r.hour }))}
              columns={[
                { key: "hour", header: t("hour"), render: (r) => `${String(r.hour).padStart(2, "0")}:00` },
                { key: "transactions", header: t("transactions") },
                { key: "gross", header: t("gross"), render: (r) => <Money value={r.gross_amount} /> },
              ]}
            />
          </Card>
        </SimpleGrid>

        <Card withBorder>
          <Group justify="space-between">
            <Text fw={600}>{t("categories")}</Text>
            {cats.data && (
              <Badge color="orange" size="lg" variant="light">
                {t("unhealthyShare", { pct: cats.data.unhealthy_share_percent ?? 0 })}
              </Badge>
            )}
          </Group>
          <Text size="xs" c="dimmed">
            {t("nutritionNote")}
          </Text>
          <ErrorAlert error={cats.error} />
          <SimpleGrid cols={{ base: 1, md: 2 }} mt="sm">
            <div style={{ width: "100%", height: 240 }}>
              <ResponsiveContainer>
                <PieChart>
                  <Pie
                    data={(cats.data?.results ?? []).map((c) => ({ name: c.name, value: shillings(c.revenue), unhealthy: c.is_unhealthy }))}
                    dataKey="value"
                    nameKey="name"
                    outerRadius={90}
                    isAnimationActive={false}
                    label
                  >
                    {(cats.data?.results ?? []).map((c, i) => (
                      <Cell key={i} fill={c.is_unhealthy ? "var(--mantine-color-red-5)" : `var(--mantine-color-teal-${4 + (i % 4)})`} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(v) => formatUGX(String(v))} />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <DataTable
              rows={(cats.data?.results ?? []).map((r, i) => ({ ...r, id: i }))}
              columns={[
                {
                  key: "name",
                  header: t("category"),
                  render: (r) => (
                    <Group gap={4}>
                      {r.name}
                      {r.is_unhealthy && (
                        <Badge size="xs" color="red">
                          {t("unhealthy")}
                        </Badge>
                      )}
                    </Group>
                  ),
                },
                { key: "quantity", header: t("quantity") },
                { key: "revenue", header: t("revenue"), render: (r) => <Money value={r.revenue} /> },
                { key: "share", header: t("share"), render: (r) => (r.share_percent === null ? "—" : `${r.share_percent}%`) },
              ]}
            />
          </SimpleGrid>
        </Card>

        <Card withBorder>
          <Group justify="space-between" align="flex-end">
            <Text fw={600}>{t("perStudent")}</Text>
            <StudentPicker label={t("pickStudent")} value={studentId} onChange={(v) => setStudentId(v)} />
          </Group>
          {!studentId && (
            <Alert variant="light" color="gray" mt="sm">
              {t("pickStudentHint")}
            </Alert>
          )}
          <ErrorAlert error={spend.error} />
          {spend.data && (
            <Stack mt="sm">
              <SimpleGrid cols={{ base: 2, md: 6 }}>
                <Stat label={t("purchases")} value={formatUGX(spend.data.purchases_total)} />
                <Stat label={t("fees")} value={formatUGX(spend.data.fees_total)} />
                <Stat label={t("p2pSent")} value={formatUGX(spend.data.p2p_sent_total)} />
                <Stat label={t("p2pReceived")} value={formatUGX(spend.data.p2p_received_total)} />
                <Stat label={t("topups")} value={formatUGX(spend.data.topups_total)} />
                <Stat label={t("refunds")} value={formatUGX(spend.data.refunds_total)} />
              </SimpleGrid>
              <SimpleGrid cols={{ base: 1, md: 2 }}>
                <DataTable
                  rows={spend.data.by_category.map((r, i) => ({ ...r, id: i }))}
                  columns={[
                    { key: "name", header: t("category") },
                    { key: "quantity", header: t("quantity") },
                    { key: "revenue", header: t("spent"), render: (r) => <Money value={r.revenue} /> },
                  ]}
                />
                <DataTable
                  rows={spend.data.top_items.map((r, i) => ({ ...r, id: i }))}
                  columns={[
                    { key: "name", header: t("product") },
                    { key: "quantity", header: t("quantity") },
                    { key: "revenue", header: t("spent"), render: (r) => <Money value={r.revenue} /> },
                  ]}
                />
              </SimpleGrid>
            </Stack>
          )}
        </Card>
      </Stack>
    </>
  );
}
