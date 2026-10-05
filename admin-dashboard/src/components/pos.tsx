"use client";

import { Badge, Drawer, Group, Stack, Table, Text } from "@mantine/core";
import { useTranslations } from "next-intl";

import { formatDateTime } from "@/lib/dates";
import { useApi } from "@/lib/hooks";
import type { PosTransaction } from "@/lib/types";

import { ErrorAlert, Loading, Money, StatusBadge } from "./ui";

export function Flags({ flags }: { flags: string[] }) {
  if (!flags?.length) return null;
  return (
    <Group gap={4}>
      {flags.map((f) => (
        <Badge key={f} size="xs" color="orange" variant="outline">
          {f.replace(/_/g, " ")}
        </Badge>
      ))}
    </Group>
  );
}

/** Per-transaction detail with line items, from GET /pos/transactions/{id}/. */
export function TransactionDrawer({ id, onClose }: { id: number | null; onClose: () => void }) {
  const t = useTranslations("sales");
  const { data, error, loading } = useApi<PosTransaction>(id ? `/pos/transactions/${id}/` : null);
  return (
    <Drawer opened={!!id} onClose={onClose} position="right" size="lg" title={id ? `${t("transaction")} #${id}` : ""}>
      {loading && !data ? <Loading /> : null}
      <ErrorAlert error={error} />
      {data && data.id === id && (
        <Stack gap="xs">
          <Row label={t("student")} value={data.student_name || "—"} />
          <Row label={t("device")} value={data.device_name} />
          <Row label={t("deviceTime")} value={formatDateTime(data.device_local_timestamp)} />
          <Row label={t("received")} value={formatDateTime(data.received_at)} />
          <Row label={t("channel")} value={data.channel.replace(/_/g, " ")} />
          <Row label={t("syncStatus")} value={<StatusBadge status={data.sync_status} />} />
          <Row label={t("amount")} value={<Money value={data.amount} />} />
          <Row label={t("collected")} value={<Money value={data.applied_amount} />} />
          {data.shortfall_amount !== "0.00" && <Row label={t("shortfall")} value={<Money value={data.shortfall_amount} c="orange" />} />}
          {data.recovered_amount !== "0.00" && <Row label={t("recovered")} value={<Money value={data.recovered_amount} />} />}
          <Row label={t("flags")} value={data.flags.length ? <Flags flags={data.flags} /> : "—"} />
          {data.reject_reason && <Row label={t("rejectReason")} value={data.reject_reason} />}
          <Row label={t("ledgerReference")} value={<span className="mono">{data.ledger_reference || "—"}</span>} />
          <Row label={t("review")} value={<StatusBadge status={data.review_status} />} />
          {data.review_notes && <Row label={t("reviewNotes")} value={data.review_notes} />}
          <Text fw={600} mt="md">
            {t("items")}
          </Text>
          <Table>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>{t("item")}</Table.Th>
                <Table.Th>{t("qty")}</Table.Th>
                <Table.Th>{t("unitPrice")}</Table.Th>
                <Table.Th>{t("lineTotal")}</Table.Th>
              </Table.Tr>
            </Table.Thead>
            <Table.Tbody>
              {data.items.length === 0 && (
                <Table.Tr>
                  <Table.Td colSpan={4}>
                    <Text c="dimmed" size="sm">
                      {t("noItems")}
                    </Text>
                  </Table.Td>
                </Table.Tr>
              )}
              {data.items.map((i) => (
                <Table.Tr key={i.id}>
                  <Table.Td>{i.description}</Table.Td>
                  <Table.Td>{i.quantity}</Table.Td>
                  <Table.Td>
                    <Money value={i.unit_price} />
                  </Table.Td>
                  <Table.Td>
                    <Money value={i.line_total} />
                  </Table.Td>
                </Table.Tr>
              ))}
            </Table.Tbody>
          </Table>
        </Stack>
      )}
    </Drawer>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <Group justify="space-between" wrap="nowrap" align="flex-start">
      <Text size="sm" c="dimmed">
        {label}
      </Text>
      <div style={{ textAlign: "right" }}>{value}</div>
    </Group>
  );
}
