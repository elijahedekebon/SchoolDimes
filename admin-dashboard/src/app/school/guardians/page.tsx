"use client";

import { Select, Tabs, Text, Textarea } from "@mantine/core";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChoiceFilter } from "@/components/filters";
import { ConfirmAction, DataTable, PageHeader, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDateTime } from "@/lib/dates";
import { usePaginated } from "@/lib/hooks";

type Verification = {
  id: number;
  parent: number;
  parent_email: string;
  full_name: string;
  id_document_type: string;
  id_number: string;
  status: string;
  verified_at: string | null;
  review_notes: string;
  reviewed_at: string | null;
  created_at: string;
};
type Link_ = {
  id: number;
  student: number;
  student_name: string;
  parent_email: string;
  parent_name: string;
  relationship: string;
  is_primary_contact: boolean;
  verification_status: string | null;
};

export default function GuardiansPage() {
  const t = useTranslations("guardians");
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <Tabs defaultValue="kyc">
        <Tabs.List>
          <Tabs.Tab value="kyc">{t("kyc")}</Tabs.Tab>
          <Tabs.Tab value="links">{t("links")}</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="kyc" pt="md">
          <KycQueue />
        </Tabs.Panel>
        <Tabs.Panel value="links" pt="md">
          <Links />
        </Tabs.Panel>
      </Tabs>
    </>
  );
}

function KycQueue() {
  const t = useTranslations("guardians");
  const list = usePaginated<Verification>("/guardian-verifications/");
  return (
    <DataTable<Verification>
      rows={list.data?.results}
      loading={list.loading}
      error={list.error}
      page={list.page}
      totalPages={list.totalPages}
      onPage={list.setPage}
      empty={t("noKyc")}
      columns={[
        { key: "full_name", header: t("nameOnId") },
        { key: "parent_email", header: t("account") },
        { key: "doc", header: t("document"), render: (v) => `${v.id_document_type.replace("_", " ")} · ${v.id_number}` },
        { key: "created_at", header: t("submitted"), render: (v) => formatDateTime(v.created_at) },
        { key: "status", header: t("status"), render: (v) => <StatusBadge status={v.status} /> },
        { key: "review_notes", header: t("notes"), render: (v) => v.review_notes || "—" },
        { key: "actions", header: "", render: (v) => <ReviewButton v={v} onDone={list.reload} /> },
      ]}
    />
  );
}

function ReviewButton({ v, onDone }: { v: Verification; onDone: () => void }) {
  const t = useTranslations("guardians");
  const [status, setStatus] = useState(v.status === "verified" ? "rejected" : "verified");
  const [notes, setNotes] = useState("");
  return (
    <ConfirmAction
      label={t("review")}
      title={t("reviewTitle", { name: v.full_name })}
      description={
        <Text size="sm">
          {t("reviewHelp", { doc: v.id_document_type.replace("_", " "), number: v.id_number })}
        </Text>
      }
      onConfirm={() => api.post(`/guardian-verifications/${v.id}/review/`, { status, review_notes: notes })}
      onDone={onDone}
    >
      <Select
        label={t("decision")}
        value={status}
        onChange={(x) => setStatus(x ?? "verified")}
        allowDeselect={false}
        data={[
          { value: "verified", label: t("approve") },
          { value: "rejected", label: t("reject") },
        ]}
      />
      <Textarea label={t("notes")} value={notes} onChange={(e) => setNotes(e.currentTarget.value)} />
    </ConfirmAction>
  );
}

function Links() {
  const t = useTranslations("guardians");
  const [kyc, setKyc] = useState("");
  const list = usePaginated<Link_>("/guardians/");
  const rows = (list.data?.results ?? []).filter((r) => !kyc || (r.verification_status ?? "none") === kyc);
  return (
    <>
      <ChoiceFilter
        label={t("kycFilter")}
        value={kyc}
        onChange={setKyc}
        options={["pending", "verified", "rejected", "none"].map((v) => ({ value: v, label: v }))}
      />
      <Text size="xs" c="dimmed" my="xs">
        {t("linkHint")}
      </Text>
      <DataTable<Link_>
        rows={rows}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        columns={[
          { key: "student_name", header: t("student"), render: (r) => <Link href={`/school/students/${r.student}`}>{r.student_name}</Link> },
          { key: "parent_name", header: t("guardian"), render: (r) => r.parent_name || r.parent_email },
          { key: "parent_email", header: t("account") },
          { key: "relationship", header: t("relationship") },
          { key: "kyc", header: t("status"), render: (r) => <StatusBadge status={r.verification_status ?? "not_submitted"} /> },
        ]}
      />
    </>
  );
}
