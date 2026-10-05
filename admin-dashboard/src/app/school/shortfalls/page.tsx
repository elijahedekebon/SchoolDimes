"use client";

import { Alert, Group, Select, Text, Textarea } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChoiceFilter } from "@/components/filters";
import { Flags, TransactionDrawer } from "@/components/pos";
import { ConfirmAction, DataTable, Money, PageHeader, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/dates";
import { usePaginated } from "@/lib/hooks";
import type { PosTransaction } from "@/lib/types";

export default function ShortfallsPage() {
  const t = useTranslations("review");
  const [type, setType] = useState("");
  const [reviewStatus, setReviewStatus] = useState("");
  const [openId, setOpenId] = useState<number | null>(null);
  const list = usePaginated<PosTransaction>("/pos/shortfalls/", { type, review_status: reviewStatus });

  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <Alert color="gray" variant="light" mb="md">
        <Text size="sm">{t("simulatorNote")}</Text>
      </Alert>
      <Group mb="sm">
        <ChoiceFilter
          label={t("type")}
          value={type}
          onChange={setType}
          options={[
            { value: "shortfall", label: t("typeShortfall") },
            { value: "flagged", label: t("typeFlagged") },
          ]}
        />
        <ChoiceFilter
          label={t("reviewStatus")}
          value={reviewStatus}
          onChange={setReviewStatus}
          options={[
            { value: "recovery_pending", label: "recovery pending" },
            { value: "resolved", label: "resolved" },
          ]}
        />
      </Group>
      <DataTable<PosTransaction>
        testId="review-table"
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        empty={t("empty")}
        columns={[
          { key: "id", header: "#", render: (r) => <a onClick={() => setOpenId(r.id)} style={{ cursor: "pointer" }}>#{r.id}</a> },
          { key: "time", header: t("when"), render: (r) => formatDateTime(r.device_local_timestamp) },
          { key: "student_name", header: t("student") },
          { key: "device_name", header: t("device") },
          { key: "amount", header: t("amount"), render: (r) => <Money value={r.amount} /> },
          { key: "shortfall", header: t("outstanding"), render: (r) => <Money value={r.outstanding_amount} c={r.outstanding_amount !== "0.00" ? "orange" : undefined} /> },
          { key: "flags", header: t("flags"), render: (r) => <Flags flags={r.flags} /> },
          { key: "review_status", header: t("reviewStatus"), render: (r) => <StatusBadge status={r.review_status} /> },
          {
            key: "actions",
            header: "",
            render: (r) => (r.review_status === "pending" ? <ResolveButton txn={r} onDone={list.reload} /> : null),
          },
        ]}
      />
      <TransactionDrawer id={openId} onClose={() => setOpenId(null)} />
    </>
  );
}

function ResolveButton({ txn, onDone }: { txn: PosTransaction; onDone: () => void }) {
  const t = useTranslations("review");
  const hasShortfall = txn.shortfall_amount !== "0.00";
  const options = hasShortfall ? ["recover_from_next_topup", "charge_guardian", "write_off"] : ["accept"];
  const [resolution, setResolution] = useState<string>(options[0]);
  const [notes, setNotes] = useState("");
  return (
    <ConfirmAction
      label={t("resolve")}
      title={t("resolveTitle", { id: txn.id })}
      description={
        <Text size="sm">
          {txn.student_name} — <Money value={txn.amount} />
          {hasShortfall && (
            <>
              {" · "}
              {t("outstanding")}: <Money value={txn.outstanding_amount} />
            </>
          )}
        </Text>
      }
      onConfirm={() => api.post(`/pos/shortfalls/${txn.id}/resolve/`, { resolution, review_notes: notes })}
      onDone={onDone}
    >
      <Select
        label={t("resolution")}
        value={resolution}
        onChange={(v) => setResolution(v ?? options[0])}
        allowDeselect={false}
        data={options.map((o) => ({ value: o, label: t(`res_${o}`) }))}
      />
      <Alert color="blue" variant="light">
        <Text size="sm">{t(`resHelp_${resolution}`)}</Text>
      </Alert>
      <Textarea label={t("notes")} value={notes} onChange={(e) => setNotes(e.currentTarget.value)} />
    </ConfirmAction>
  );
}
