"use client";

import { Tabs } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChoiceFilter } from "@/components/filters";
import { DepositIssues } from "@/components/PaymentIssues";
import { SchoolPicker } from "@/components/SchoolPicker";
import { ConfirmAction, DataTable, PageHeader, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/dates";
import { usePaginated } from "@/lib/hooks";

type Hook = { id: number; reference: string; aggregator_ref: string; reason: string; payload: Record<string, unknown>; reviewed: boolean; received_at: string };

export default function PlatformPaymentIssues() {
  const t = useTranslations("paymentIssues");
  const [school, setSchool] = useState<string | null>(null);
  return (
    <>
      <PageHeader title={t("platformTitle")} subtitle={t("platformSubtitle")} />
      <Tabs defaultValue="webhooks">
        <Tabs.List>
          <Tabs.Tab value="webhooks">{t("unmatched")}</Tabs.Tab>
          <Tabs.Tab value="deposits">{t("failedPayments")}</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="webhooks" pt="md">
          <Webhooks />
        </Tabs.Panel>
        <Tabs.Panel value="deposits" pt="md">
          <SchoolPicker label={t("school")} value={school} onChange={setSchool} />
          <DepositIssues school={school ?? undefined} />
        </Tabs.Panel>
      </Tabs>
    </>
  );
}

function Webhooks() {
  const t = useTranslations("paymentIssues");
  const [reviewed, setReviewed] = useState("false");
  const list = usePaginated<Hook>("/payments/unmatched-webhooks/", { reviewed });
  return (
    <>
      <ChoiceFilter label={t("reviewedFilter")} value={reviewed} onChange={setReviewed} options={[{ value: "false", label: t("toReview") }, { value: "true", label: t("reviewedDone") }]} />
      <DataTable<Hook>
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        empty={t("empty")}
        columns={[
          { key: "received_at", header: t("when"), render: (h) => formatDateTime(h.received_at) },
          { key: "reference", header: t("reference"), render: (h) => <span className="mono">{h.reference || "—"}</span> },
          { key: "aggregator_ref", header: t("aggregatorRef"), render: (h) => <span className="mono">{h.aggregator_ref || "—"}</span> },
          { key: "reason", header: t("reason"), render: (h) => <StatusBadge status={h.reason} /> },
          { key: "payload", header: t("payload"), render: (h) => <span className="mono" style={{ fontSize: 11 }}>{JSON.stringify(h.payload).slice(0, 120)}</span> },
          {
            key: "actions",
            header: "",
            render: (h) => (!h.reviewed ? <ConfirmAction label={t("markReviewed")} title={t("markReviewed")} description={t("markReviewedHelp")} onConfirm={() => api.post(`/payments/unmatched-webhooks/${h.id}/mark-reviewed/`)} onDone={list.reload} /> : null),
          },
        ]}
      />
    </>
  );
}
