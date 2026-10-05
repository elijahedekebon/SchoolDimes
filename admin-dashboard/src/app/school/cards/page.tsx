"use client";

import { Alert, Group, Text, TextInput } from "@mantine/core";
import { useDebouncedValue } from "@mantine/hooks";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { CardActions, IssueCardButton, normalizeUid } from "@/components/cards";
import { ChoiceFilter } from "@/components/filters";
import { StudentPicker } from "@/components/StudentPicker";
import { DataTable, PageHeader, StatusBadge } from "@/components/ui";
import { usePaginated } from "@/lib/hooks";
import type { Card, Student } from "@/lib/types";

export default function CardsPage() {
  const t = useTranslations("cards");
  const [status, setStatus] = useState("");
  const [uid, setUid] = useState("");
  const [q] = useDebouncedValue(uid, 300);
  const [issueFor, setIssueFor] = useState<Student | null>(null);
  const list = usePaginated<Card & { student_name: string }>("/cards/", { status, card_uid: q ? (normalizeUid(q) ?? q) : "" });
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <Alert variant="light" color="blue" mb="md">
        <Text size="sm">{t("uidFormat")}</Text>
      </Alert>
      <Group mb="md" align="flex-end">
        <StudentPicker label={t("issueFor")} value={issueFor ? String(issueFor.id) : null} onChange={(_v, s) => setIssueFor(s ?? null)} />
        {issueFor && (
          <IssueCardButton
            studentId={issueFor.id}
            studentName={issueFor.name}
            onDone={() => {
              setIssueFor(null);
              list.reload();
            }}
          />
        )}
      </Group>
      <Group mb="sm" align="flex-end">
        <TextInput size="xs" label={t("findUid")} placeholder="04:A2:2B:7C" value={uid} onChange={(e) => setUid(e.currentTarget.value)} w={240} />
        <ChoiceFilter label={t("status")} value={status} onChange={setStatus} options={["active", "frozen", "lost"].map((v) => ({ value: v, label: v }))} />
      </Group>
      <DataTable
        testId="cards-table"
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        columns={[
          { key: "student_name", header: t("student"), render: (c) => <Link href={`/school/students/${c.student}`}>{c.student_name}</Link> },
          { key: "card_uid", header: t("uid"), render: (c) => <span className="mono">{c.card_uid}</span> },
          { key: "status", header: t("status"), render: (c) => <StatusBadge status={c.status} /> },
          { key: "actions", header: "", render: (c) => <CardActions card={c} studentName={c.student_name} onDone={list.reload} /> },
        ]}
      />
    </>
  );
}
