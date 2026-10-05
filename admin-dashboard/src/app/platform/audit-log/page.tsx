"use client";

import { Group, TextInput } from "@mantine/core";
import { useDebouncedValue } from "@mantine/hooks";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { SchoolPicker } from "@/components/SchoolPicker";
import { DataTable, PageHeader } from "@/components/ui";
import { formatDateTime } from "@/lib/dates";
import { usePaginated } from "@/lib/hooks";

type Log = { id: number; actor_email: string | null; actor_role: string; school_name: string | null; action: string; target_type: string; target_id: string; details: Record<string, unknown>; created_at: string };

export default function AuditLogPage() {
  const t = useTranslations("audit");
  const [school, setSchool] = useState<string | null>(null);
  const [action, setAction] = useState("");
  const [q] = useDebouncedValue(action, 300);
  const list = usePaginated<Log>("/audit-logs/", { school: school ?? "", action: q });
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <Group mb="sm" align="flex-end">
        <SchoolPicker label={t("school")} value={school} onChange={setSchool} />
        <TextInput size="xs" label={t("action")} placeholder="card." value={action} onChange={(e) => setAction(e.currentTarget.value)} />
      </Group>
      <DataTable<Log>
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        columns={[
          { key: "created_at", header: t("when"), render: (l) => formatDateTime(l.created_at) },
          { key: "actor", header: t("actor"), render: (l) => `${l.actor_email ?? "—"} (${l.actor_role})` },
          { key: "school_name", header: t("school"), render: (l) => l.school_name ?? "—" },
          { key: "action", header: t("action") },
          { key: "target", header: t("target"), render: (l) => (l.target_type ? `${l.target_type} #${l.target_id}` : "—") },
          { key: "details", header: t("details"), render: (l) => <span className="mono" style={{ fontSize: 11 }}>{JSON.stringify(l.details)}</span> },
        ]}
      />
    </>
  );
}
