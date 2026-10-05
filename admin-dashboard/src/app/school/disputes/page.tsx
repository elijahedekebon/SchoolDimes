"use client";

import { Alert, Button, Drawer, Group, SegmentedControl, Stack, Text, Textarea } from "@mantine/core";
import { useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { Suspense, useState } from "react";

import { ChoiceFilter } from "@/components/filters";
import { MoneyInput } from "@/components/MoneyInput";
import { TransactionDrawer } from "@/components/pos";
import { ConfirmAction, DataTable, ErrorAlert, Loading, Money, PageHeader, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/dates";
import { useApi, usePaginated } from "@/lib/hooks";
import { compareMoney, formatUGX, fromCents, toCents } from "@/lib/money";

type Dispute = {
  id: number;
  student: number;
  student_name: string;
  pos_transaction: number | null;
  ledger_entry: number | null;
  reason_category: string;
  description: string;
  status: string;
  resolution_notes: string;
  refund_amount: string;
  original_amount: string;
  refunded_total: string;
  resolved_at: string | null;
  created_at: string;
};

export default function DisputesPage() {
  return (
    <Suspense>
      <Disputes />
    </Suspense>
  );
}

function Disputes() {
  const t = useTranslations("disputes");
  const params = useSearchParams();
  const [status, setStatus] = useState("");
  const [openId, setOpenId] = useState<number | null>(params.get("open") ? Number(params.get("open")) : null);
  const list = usePaginated<Dispute>("/disputes/", { status });
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <ChoiceFilter label={t("status")} value={status} onChange={setStatus} options={["open", "under_review", "resolved_refunded", "resolved_denied"].map((v) => ({ value: v, label: v.replace(/_/g, " ") }))} />
      <DataTable<Dispute>
        testId="disputes-table"
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        onRowClick={(d) => setOpenId(d.id)}
        columns={[
          { key: "id", header: "#" },
          { key: "created_at", header: t("raised"), render: (d) => formatDateTime(d.created_at) },
          { key: "student_name", header: t("student") },
          { key: "reason_category", header: t("reason"), render: (d) => d.reason_category.replace(/_/g, " ") },
          { key: "original_amount", header: t("original"), render: (d) => <Money value={d.original_amount} /> },
          { key: "status", header: t("status"), render: (d) => <StatusBadge status={d.status} /> },
        ]}
      />
      <DisputeDrawer id={openId} onClose={() => setOpenId(null)} onChanged={list.reload} />
    </>
  );
}

function DisputeDrawer({ id, onClose, onChanged }: { id: number | null; onClose: () => void; onChanged: () => void }) {
  const t = useTranslations("disputes");
  const res = useApi<Dispute>(id ? `/disputes/${id}/` : null);
  const [txnId, setTxnId] = useState<number | null>(null);
  const d = res.data && res.data.id === id ? res.data : null;
  const refresh = () => {
    res.reload();
    onChanged();
  };
  const open = d && (d.status === "open" || d.status === "under_review");
  return (
    <Drawer opened={!!id} onClose={onClose} position="right" size="lg" title={id ? `${t("dispute")} #${id}` : ""}>
      <ErrorAlert error={res.error} />
      {!d ? (
        <Loading />
      ) : (
        <Stack>
          <Group>
            <StatusBadge status={d.status} />
            <Text size="sm">{d.student_name}</Text>
          </Group>
          <Text size="sm">
            <b>{t("reason")}:</b> {d.reason_category.replace(/_/g, " ")}
          </Text>
          <Text size="sm">{d.description || "—"}</Text>
          <Text size="sm">
            {t("original")}: <Money value={d.original_amount} /> · {t("alreadyRefunded")}: <Money value={d.refunded_total} />
          </Text>
          {d.pos_transaction && (
            <Button size="xs" variant="light" onClick={() => setTxnId(d.pos_transaction)} w="fit-content">
              {t("viewTransaction")}
            </Button>
          )}
          {d.ledger_entry && (
            <Text size="xs" c="dimmed">
              {t("ledgerEntry")} #{d.ledger_entry}
            </Text>
          )}
          {d.resolution_notes && (
            <Alert variant="light">
              <b>{t("resolution")}:</b> {d.resolution_notes} {d.refund_amount !== "0.00" && <>· {t("refund")}: <Money value={d.refund_amount} /></>}
            </Alert>
          )}
          {open && (
            <Group>
              {d.status === "open" && <ConfirmAction label={t("startReview")} title={t("startReview")} description={t("startReviewHelp")} onConfirm={() => api.post(`/disputes/${d.id}/review/`)} onDone={refresh} />}
              <Resolve d={d} onDone={refresh} />
            </Group>
          )}
        </Stack>
      )}
      <TransactionDrawer id={txnId} onClose={() => setTxnId(null)} />
    </Drawer>
  );
}

function Resolve({ d, onDone }: { d: Dispute; onDone: () => void }) {
  const t = useTranslations("disputes");
  const remaining = fromCents((toCents(d.original_amount) ?? 0n) - (toCents(d.refunded_total) ?? 0n));
  const [outcome, setOutcome] = useState<"refund" | "deny">("refund");
  const [amount, setAmount] = useState(remaining);
  const [notes, setNotes] = useState("");
  const over = outcome === "refund" && amount !== "" && compareMoney(amount, remaining) > 0;
  return (
    <ConfirmAction
      label={t("resolve")}
      title={t("resolveTitle", { id: d.id })}
      description={
        <Text size="sm">
          {outcome === "refund" ? t("refundHelp", { student: d.student_name, max: formatUGX(remaining) }) : t("denyHelp")}
        </Text>
      }
      canConfirm={outcome === "deny" || (!!amount && !over && compareMoney(amount, "0") > 0)}
      onConfirm={() => api.post(`/disputes/${d.id}/resolve/`, outcome === "refund" ? { outcome, refund_amount: amount, resolution_notes: notes } : { outcome, resolution_notes: notes })}
      onDone={onDone}
      testId="resolve-dispute"
    >
      <SegmentedControl
        value={outcome}
        onChange={(v) => setOutcome(v as "refund" | "deny")}
        data={[
          { value: "refund", label: t("refund") },
          { value: "deny", label: t("deny") },
        ]}
      />
      {outcome === "refund" && <MoneyInput label={t("refundAmount")} description={t("max", { max: formatUGX(remaining) })} value={amount} onChange={setAmount} error={over ? t("overMax") : undefined} data-testid="refund-amount" />}
      <Textarea label={t("notes")} value={notes} onChange={(e) => setNotes(e.currentTarget.value)} />
    </ConfirmAction>
  );
}
