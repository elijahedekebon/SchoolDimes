"use client";

import { Text } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChoiceFilter } from "@/components/filters";
import { DataTable, Money, StatusBadge } from "@/components/ui";
import { formatDateTime } from "@/lib/dates";
import { usePaginated } from "@/lib/hooks";

type Deposit = {
  id: number;
  school: number;
  purpose: string;
  student: number | null;
  amount: string;
  channel: string;
  payer_phone: string;
  status: string;
  reference: string;
  aggregator_ref: string;
  contributor_name: string | null;
  failure_reason: string;
  created_at: string;
};

/** Failed / expired / long-pending collections (deposits, gift vouchers, fund contributions). */
export function DepositIssues({ school }: { school?: string }) {
  const t = useTranslations("paymentIssues");
  const [status, setStatus] = useState("failed");
  const list = usePaginated<Deposit>("/payments/deposits/", { status, school: school ?? "" });
  return (
    <>
      <ChoiceFilter label={t("status")} value={status} onChange={setStatus} options={["failed", "expired", "pending"].map((v) => ({ value: v, label: v }))} />
      <Text size="xs" c="dimmed" my="xs">
        {t("depositsHelp")}
      </Text>
      <DataTable<Deposit>
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        empty={t("empty")}
        columns={[
          { key: "created_at", header: t("when"), render: (d) => formatDateTime(d.created_at) },
          { key: "reference", header: t("reference"), render: (d) => <span className="mono">{d.reference}</span> },
          { key: "purpose", header: t("purpose"), render: (d) => d.purpose.replace(/_/g, " ") },
          { key: "amount", header: t("amount"), render: (d) => <Money value={d.amount} /> },
          { key: "channel", header: t("channel") },
          { key: "payer", header: t("payer"), render: (d) => d.contributor_name || d.payer_phone || "—" },
          { key: "status", header: t("status"), render: (d) => <StatusBadge status={d.status} /> },
          { key: "failure_reason", header: t("reason"), render: (d) => d.failure_reason || "—" },
        ]}
      />
    </>
  );
}
