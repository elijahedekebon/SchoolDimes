"use client";

import { Alert, Select, Text, Textarea } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChoiceFilter } from "@/components/filters";
import { ConfirmAction, DataTable, PageHeader, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/dates";
import { usePaginated } from "@/lib/hooks";

type Req = {
  id: number;
  requested_by: number;
  request_type: "export" | "correction" | "deletion";
  subject: "self" | "student";
  student: number | null;
  details: string;
  status: string;
  notes: string;
  handled_at: string | null;
  created_at: string;
  retention_notice: string | null;
};

export default function PrivacyPage() {
  const t = useTranslations("privacy");
  const [status, setStatus] = useState("pending");
  const [type, setType] = useState("");
  const list = usePaginated<Req>("/privacy/data-requests/", { status, request_type: type });
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <Alert variant="light" color="blue" mb="md">
        <Text size="sm">{t("retention")}</Text>
      </Alert>
      <ChoiceFilter label={t("status")} value={status} onChange={setStatus} options={["pending", "in_progress", "completed", "rejected"].map((v) => ({ value: v, label: v.replace("_", " ") }))} />
      <ChoiceFilter label={t("type")} value={type} onChange={setType} options={["export", "correction", "deletion"].map((v) => ({ value: v, label: t(`type_${v}`) }))} />
      <DataTable<Req>
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        empty={t("empty")}
        columns={[
          { key: "created_at", header: t("received"), render: (r) => formatDateTime(r.created_at) },
          { key: "request_type", header: t("type"), render: (r) => t(`type_${r.request_type}`) },
          { key: "subject", header: t("subject"), render: (r) => (r.subject === "self" ? t("subjectSelf") : t("subjectStudent", { id: r.student ?? "" })) },
          { key: "details", header: t("details"), render: (r) => r.details || "—" },
          { key: "status", header: t("status"), render: (r) => <StatusBadge status={r.status} /> },
          { key: "notes", header: t("notes"), render: (r) => r.notes || "—" },
          { key: "actions", header: "", render: (r) => (["pending", "in_progress"].includes(r.status) ? <Handle r={r} onDone={list.reload} /> : null) },
        ]}
      />
    </>
  );
}

function Handle({ r, onDone }: { r: Req; onDone: () => void }) {
  const t = useTranslations("privacy");
  const [status, setStatus] = useState(r.status === "pending" ? "in_progress" : "completed");
  const [notes, setNotes] = useState("");
  const irreversible = r.request_type === "deletion" && status === "completed";
  return (
    <ConfirmAction
      label={t("handle")}
      color={irreversible ? "red" : undefined}
      title={t("handleTitle", { type: t(`type_${r.request_type}`) })}
      description={<Text size="sm">{t(`handleHelp_${r.request_type}`)}</Text>}
      onConfirm={() => api.post(`/privacy/data-requests/${r.id}/handle/`, { status, notes })}
      onDone={onDone}
    >
      <Select
        label={t("newStatus")}
        value={status}
        onChange={(v) => setStatus(v ?? "in_progress")}
        allowDeselect={false}
        data={["in_progress", "completed", "rejected"].map((v) => ({ value: v, label: v.replace("_", " ") }))}
      />
      {irreversible && (
        <Alert color="red" title={t("irreversible")}>
          {r.retention_notice ?? t("retention")}
        </Alert>
      )}
      <Textarea label={t("notesToRequester")} value={notes} onChange={(e) => setNotes(e.currentTarget.value)} />
    </ConfirmAction>
  );
}
