"use client";

import { Drawer, Select, Stack, Text, Textarea } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChoiceFilter } from "@/components/filters";
import { ConfirmAction, DataTable, Money, PageHeader, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/dates";
import { usePaginated } from "@/lib/hooks";

type Alert_ = { id: number; student: number; student_name: string; rule: string; details: Record<string, unknown>; status: string; review_notes: string; reviewed_at: string | null; created_at: string };
type P2P = { id: number; sender_student: number; sender_name: string; recipient_name: string; amount: string; note: string; created_at: string };

export default function P2PAlertsPage() {
  const t = useTranslations("p2pAlerts");
  const [status, setStatus] = useState("open");
  const [history, setHistory] = useState<Alert_ | null>(null);
  const list = usePaginated<Alert_>("/p2p-alerts/", { status });
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <ChoiceFilter label={t("status")} value={status} onChange={setStatus} options={["open", "reviewed", "dismissed"].map((v) => ({ value: v, label: v }))} />
      <DataTable<Alert_>
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        empty={t("empty")}
        columns={[
          { key: "created_at", header: t("raised"), render: (a) => formatDateTime(a.created_at) },
          { key: "student_name", header: t("student"), render: (a) => <a style={{ cursor: "pointer" }} onClick={() => setHistory(a)}>{a.student_name}</a> },
          { key: "rule", header: t("rule"), render: (a) => t(`rule_${a.rule}`) },
          { key: "details", header: t("details"), render: (a) => Object.entries(a.details).map(([k, v]) => `${k.replace(/_/g, " ")}: ${String(v)}`).join(" · ") },
          { key: "status", header: t("status"), render: (a) => <StatusBadge status={a.status} /> },
          { key: "notes", header: t("notes"), render: (a) => a.review_notes || "—" },
          { key: "actions", header: "", render: (a) => (a.status === "open" ? <Review a={a} onDone={list.reload} /> : null) },
        ]}
      />
      <HistoryDrawer alert={history} onClose={() => setHistory(null)} />
    </>
  );
}

function Review({ a, onDone }: { a: Alert_; onDone: () => void }) {
  const t = useTranslations("p2pAlerts");
  const [status, setStatus] = useState("reviewed");
  const [notes, setNotes] = useState("");
  return (
    <ConfirmAction label={t("review")} title={t("reviewTitle", { name: a.student_name })} description={t("reviewHelp")} onConfirm={() => api.post(`/p2p-alerts/${a.id}/review/`, { status, review_notes: notes })} onDone={onDone}>
      <Select label={t("outcome")} value={status} onChange={(v) => setStatus(v ?? "reviewed")} allowDeselect={false} data={[{ value: "reviewed", label: t("reviewed") }, { value: "dismissed", label: t("dismissed") }]} />
      <Textarea label={t("notes")} value={notes} onChange={(e) => setNotes(e.currentTarget.value)} />
    </ConfirmAction>
  );
}

function HistoryDrawer({ alert, onClose }: { alert: Alert_ | null; onClose: () => void }) {
  const t = useTranslations("p2pAlerts");
  const list = usePaginated<P2P>(alert ? `/students/${alert.student}/p2p-history/` : null);
  return (
    <Drawer opened={!!alert} onClose={onClose} position="right" size="lg" title={t("historyTitle", { name: alert?.student_name ?? "" })}>
      <Stack>
        <Text size="xs" c="dimmed">
          {t("historyHelp")}
        </Text>
        <DataTable<P2P>
          rows={list.data?.results}
          loading={list.loading}
          error={list.error}
          page={list.page}
          totalPages={list.totalPages}
          onPage={list.setPage}
          columns={[
            { key: "created_at", header: t("when"), render: (r) => formatDateTime(r.created_at) },
            { key: "from", header: t("from"), render: (r) => r.sender_name },
            { key: "to", header: t("to"), render: (r) => r.recipient_name },
            { key: "amount", header: t("amount"), render: (r) => <Money value={r.amount} /> },
            { key: "note", header: t("note") },
          ]}
        />
      </Stack>
    </Drawer>
  );
}
