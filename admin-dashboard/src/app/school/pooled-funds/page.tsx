"use client";

import { Button, Drawer, Group, Modal, Progress, Select, Stack, Text, TextInput, Textarea } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChoiceFilter } from "@/components/filters";
import { MoneyInput } from "@/components/MoneyInput";
import { ConfirmAction, DataTable, ErrorAlert, Loading, Money, PageHeader, StatusBadge } from "@/components/ui";
import { api, newIdempotencyKey } from "@/lib/api";
import { formatDate, formatDateTime } from "@/lib/dates";
import { useApi, usePaginated } from "@/lib/hooks";
import { compareMoney, formatUGX } from "@/lib/money";

type Fund = {
  id: number;
  title: string;
  purpose: string;
  group_label: string;
  target_amount: string | null;
  deadline: string | null;
  status: string;
  total_contributed: string;
  balance: string;
  progress_percent: number | null;
  created_at: string;
};
type FundDetail = Fund & {
  total_disbursed: string;
  contributions: Array<{ id: number; contributor_name: string; amount: string; deposit_reference: string; created_at: string }>;
  disbursements: Array<{ id: number; amount: string; destination: string; description: string; payout_status: string | null; created_at: string }>;
};

export default function PooledFundsPage() {
  const t = useTranslations("pooled");
  const [status, setStatus] = useState("");
  const [openId, setOpenId] = useState<number | null>(null);
  const list = usePaginated<Fund>("/pooled-funds/", { status });
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} actions={<NewFund onDone={list.reload} />} />
      <ChoiceFilter label={t("status")} value={status} onChange={setStatus} options={["open", "closed", "disbursed"].map((v) => ({ value: v, label: v }))} />
      <DataTable<Fund>
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        onRowClick={(f) => setOpenId(f.id)}
        columns={[
          { key: "title", header: t("fund") },
          { key: "group_label", header: t("group"), render: (f) => f.group_label || "—" },
          { key: "status", header: t("status"), render: (f) => <StatusBadge status={f.status} /> },
          { key: "total", header: t("raised"), render: (f) => <Money value={f.total_contributed} /> },
          { key: "target", header: t("target"), render: (f) => (f.target_amount ? <Money value={f.target_amount} /> : "—") },
          { key: "progress", header: t("progress"), render: (f) => (f.progress_percent === null ? "—" : <Progress value={f.progress_percent} w={120} />) },
          { key: "balance", header: t("held"), render: (f) => <Money value={f.balance} /> },
          { key: "deadline", header: t("deadline"), render: (f) => formatDate(f.deadline) },
        ]}
      />
      <FundDrawer id={openId} onClose={() => setOpenId(null)} onChanged={list.reload} />
    </>
  );
}

function FundDrawer({ id, onClose, onChanged }: { id: number | null; onClose: () => void; onChanged: () => void }) {
  const t = useTranslations("pooled");
  const fund = useApi<FundDetail>(id ? `/pooled-funds/${id}/` : null);
  const f = fund.data && fund.data.id === id ? fund.data : null;
  const refresh = () => {
    fund.reload();
    onChanged();
  };
  return (
    <Drawer opened={!!id} onClose={onClose} position="right" size="xl" title={f?.title ?? ""}>
      <ErrorAlert error={fund.error} />
      {!f ? (
        <Loading />
      ) : (
        <Stack>
          <Text size="sm" c="dimmed">
            {f.purpose}
          </Text>
          <Group>
            <StatusBadge status={f.status} />
            <Text size="sm">
              {t("raised")}: <Money value={f.total_contributed} /> · {t("disbursed")}: <Money value={f.total_disbursed} /> · {t("held")}: <Money value={f.balance} />
            </Text>
          </Group>
          <Text size="xs" c="dimmed">
            {t("ledgerNote")}
          </Text>
          <Group>
            {f.status === "open" && (
              <ConfirmAction label={t("close")} color="orange" title={t("closeTitle")} description={t("closeHelp")} onConfirm={() => api.post(`/pooled-funds/${f.id}/close/`)} onDone={refresh} />
            )}
            {f.status !== "disbursed" && compareMoney(f.balance, "0") > 0 && <Disburse fund={f} onDone={refresh} />}
          </Group>
          <Text fw={600}>{t("contributions")}</Text>
          <DataTable
            rows={f.contributions}
            empty={t("noContributions")}
            columns={[
              { key: "created_at", header: t("when"), render: (c) => formatDateTime(c.created_at) },
              { key: "contributor_name", header: t("contributor") },
              { key: "amount", header: t("amount"), render: (c) => <Money value={c.amount} /> },
              { key: "deposit_reference", header: t("reference"), render: (c) => <span className="mono">{c.deposit_reference}</span> },
            ]}
          />
          <Text fw={600}>{t("disbursements")}</Text>
          <DataTable
            rows={f.disbursements}
            empty={t("noDisbursements")}
            columns={[
              { key: "created_at", header: t("when"), render: (d) => formatDateTime(d.created_at) },
              { key: "amount", header: t("amount"), render: (d) => <Money value={d.amount} /> },
              { key: "destination", header: t("destination"), render: (d) => t(`dest_${d.destination}`) },
              { key: "description", header: t("description") },
              { key: "payout_status", header: t("payout"), render: (d) => <StatusBadge status={d.payout_status} /> },
            ]}
          />
        </Stack>
      )}
    </Drawer>
  );
}

function Disburse({ fund, onDone }: { fund: FundDetail; onDone: () => void }) {
  const t = useTranslations("pooled");
  const [v, setV] = useState({ amount: "", destination: "school_settlement", description: "", phone_number: "" });
  const [key, setKey] = useState(newIdempotencyKey);
  const tooMuch = v.amount !== "" && compareMoney(v.amount, fund.balance) > 0;
  return (
    <ConfirmAction
      label={t("disburse")}
      title={t("disburseTitle", { title: fund.title })}
      description={<Text size="sm">{t("disburseHelp", { held: formatUGX(fund.balance) })}</Text>}
      canConfirm={!!v.amount && !tooMuch && !!v.description && (v.destination !== "external" || !!v.phone_number)}
      onConfirm={() => api.post(`/pooled-funds/${fund.id}/disburse/`, { ...v, idempotency_key: key })}
      onDone={() => {
        setKey(newIdempotencyKey());
        setV({ amount: "", destination: "school_settlement", description: "", phone_number: "" });
        onDone();
      }}
    >
      <MoneyInput label={t("amount")} value={v.amount} onChange={(x) => setV({ ...v, amount: x })} error={tooMuch ? t("tooMuch") : undefined} />
      <Select
        label={t("destination")}
        value={v.destination}
        onChange={(x) => setV({ ...v, destination: x ?? "school_settlement" })}
        allowDeselect={false}
        data={[
          { value: "school_settlement", label: t("dest_school_settlement") },
          { value: "external", label: t("dest_external") },
        ]}
      />
      {v.destination === "external" && <TextInput label={t("phone")} value={v.phone_number} onChange={(e) => setV({ ...v, phone_number: e.currentTarget.value })} required />}
      <Textarea label={t("description")} description={t("descriptionHelp")} value={v.description} onChange={(e) => setV({ ...v, description: e.currentTarget.value })} required />
    </ConfirmAction>
  );
}

function NewFund({ onDone }: { onDone: () => void }) {
  const t = useTranslations("pooled");
  const [open, setOpen] = useState(false);
  const [v, setV] = useState({ title: "", purpose: "", group_label: "", target_amount: "", deadline: "" });
  const [error, setError] = useState<unknown>(null);
  const save = async () => {
    setError(null);
    try {
      await api.post("/pooled-funds/", { ...v, target_amount: v.target_amount || null, deadline: v.deadline || null });
      setOpen(false);
      setV({ title: "", purpose: "", group_label: "", target_amount: "", deadline: "" });
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
          <TextInput label={t("fund")} placeholder="P4 trip to Entebbe Zoo" value={v.title} onChange={(e) => setV({ ...v, title: e.currentTarget.value })} required />
          <Textarea label={t("purpose")} value={v.purpose} onChange={(e) => setV({ ...v, purpose: e.currentTarget.value })} />
          <TextInput label={t("group")} placeholder="P4" value={v.group_label} onChange={(e) => setV({ ...v, group_label: e.currentTarget.value })} />
          <MoneyInput label={t("target")} description={t("optional")} value={v.target_amount} onChange={(x) => setV({ ...v, target_amount: x })} />
          <TextInput type="date" label={t("deadline")} value={v.deadline} onChange={(e) => setV({ ...v, deadline: e.currentTarget.value })} />
          <ErrorAlert error={error} />
          <Group justify="flex-end">
            <Button onClick={save} disabled={!v.title}>
              {t("create")}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
