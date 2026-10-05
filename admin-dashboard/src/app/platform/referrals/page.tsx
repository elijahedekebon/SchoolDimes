"use client";

import { Button, Group, Modal, Stack } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { SchoolPicker, type SchoolRow } from "@/components/SchoolPicker";
import { ConfirmAction, DataTable, ErrorAlert, PageHeader, StatusBadge } from "@/components/ui";
import { api, type Paginated } from "@/lib/api";
import { formatDate } from "@/lib/dates";
import { useApi, usePaginated } from "@/lib/hooks";

type Referral = { id: number; referring_school: number; referred_school: number; status: string; reward_applied: boolean; created_at: string };

export default function ReferralsPage() {
  const t = useTranslations("referrals");
  const list = usePaginated<Referral>("/school-referrals/");
  const schools = useApi<Paginated<SchoolRow>>("/schools/", { page_size: 100 });
  const name = (id: number) => schools.data?.results.find((s) => s.id === id)?.name ?? `#${id}`;
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} actions={<NewReferral onDone={list.reload} />} />
      <DataTable<Referral>
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        columns={[
          { key: "referring", header: t("referring"), render: (r) => name(r.referring_school) },
          { key: "referred", header: t("referred"), render: (r) => name(r.referred_school) },
          { key: "status", header: t("status"), render: (r) => <StatusBadge status={r.status} /> },
          { key: "reward", header: t("reward"), render: (r) => (r.reward_applied ? "✓" : "—") },
          { key: "created_at", header: t("created"), render: (r) => formatDate(r.created_at) },
          {
            key: "actions",
            header: "",
            render: (r) =>
              r.status === "pending" ? (
                <ConfirmAction label={t("apply")} color="green" title={t("applyTitle")} description={t("applyHelp", { school: name(r.referring_school) })} onConfirm={() => api.post(`/school-referrals/${r.id}/apply/`)} onDone={list.reload} />
              ) : null,
          },
        ]}
      />
    </>
  );
}

function NewReferral({ onDone }: { onDone: () => void }) {
  const t = useTranslations("referrals");
  const [open, setOpen] = useState(false);
  const [from, setFrom] = useState<string | null>(null);
  const [to, setTo] = useState<string | null>(null);
  const [error, setError] = useState<unknown>(null);
  const save = async () => {
    setError(null);
    try {
      await api.post("/school-referrals/", { referring_school: Number(from), referred_school: Number(to) });
      setOpen(false);
      onDone();
    } catch (e) {
      setError(e);
    }
  };
  return (
    <>
      <Button size="xs" onClick={() => setOpen(true)}>
        {t("new")}
      </Button>
      <Modal opened={open} onClose={() => setOpen(false)} title={t("new")} centered>
        <Stack>
          <SchoolPicker label={t("referring")} value={from} onChange={setFrom} />
          <SchoolPicker label={t("referred")} value={to} onChange={setTo} />
          <ErrorAlert error={error} />
          <Group justify="flex-end">
            <Button onClick={save} disabled={!from || !to || from === to}>
              {t("create")}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
