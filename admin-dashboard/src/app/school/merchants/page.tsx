"use client";

import { Button, Drawer, Group, Modal, Stack, Text, TextInput } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { DeviceTokenModal, RegisterButton } from "@/components/DeviceToken";
import { ChoiceFilter, DateRange } from "@/components/filters";
import { ConfirmAction, DataTable, ErrorAlert, Money, PageHeader, StatusBadge } from "@/components/ui";
import { api, type Paginated } from "@/lib/api";
import { formatDateTime, kampalaToday, shiftDay } from "@/lib/dates";
import { useApi, usePaginated } from "@/lib/hooks";
import type { Device, LedgerEntry } from "@/lib/types";

type Merchant = {
  id: number;
  name: string;
  category: string;
  contact_phone: string;
  status: string;
  approved_school_ids: number[];
  my_school_approval: string | null;
};
type Statement = {
  balances: Array<{ school_id: number; wallet_id: number; balance: string }>;
  total_credits: string;
  total_debits: string;
  entries: Paginated<LedgerEntry>;
};

export default function MerchantsPage() {
  const t = useTranslations("merchants");
  const [approval, setApproval] = useState("");
  const [statementFor, setStatementFor] = useState<Merchant | null>(null);
  const [shown, setShown] = useState<Device | null>(null);
  const list = usePaginated<Merchant>("/merchants/");
  const rows = (list.data?.results ?? []).filter((m) => !approval || (m.my_school_approval ?? "none") === approval);
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} actions={<NewMerchant onDone={list.reload} />} />
      <ChoiceFilter
        label={t("myApproval")}
        value={approval}
        onChange={setApproval}
        options={["approved", "pending", "suspended", "none"].map((v) => ({ value: v, label: t(`approval_${v}`) }))}
      />
      <DataTable<Merchant>
        rows={rows}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        columns={[
          { key: "name", header: t("name") },
          { key: "category", header: t("category"), render: (m) => m.category || "—" },
          { key: "contact_phone", header: t("phone"), render: (m) => m.contact_phone || "—" },
          { key: "status", header: t("platformStatus"), render: (m) => <StatusBadge status={m.status} /> },
          { key: "mine", header: t("myApproval"), render: (m) => <StatusBadge status={m.my_school_approval ?? "none"} /> },
          {
            key: "actions",
            header: "",
            render: (m) => (
              <Group gap="xs">
                {m.my_school_approval !== "approved" ? (
                  <ConfirmAction
                    label={t("approve")}
                    color="green"
                    title={t("approveTitle", { name: m.name })}
                    description={t("approveHelp")}
                    onConfirm={() => api.post(`/merchants/${m.id}/approve/`)}
                    onDone={list.reload}
                  />
                ) : (
                  <>
                    <ConfirmAction
                      label={t("suspend")}
                      color="red"
                      title={t("suspendTitle", { name: m.name })}
                      description={t("suspendHelp")}
                      onConfirm={() => api.post(`/merchants/${m.id}/suspend/`)}
                      onDone={list.reload}
                    />
                    <Button size="xs" variant="light" onClick={() => setStatementFor(m)}>
                      {t("statement")}
                    </Button>
                    <RegisterButton fixedMerchant={m.id} onRegistered={(d) => setShown(d)} />
                  </>
                )}
              </Group>
            ),
          },
        ]}
      />
      <Text size="xs" c="dimmed" mt="sm">
        {t("staffHint")}
      </Text>
      <StatementDrawer merchant={statementFor} onClose={() => setStatementFor(null)} />
      <DeviceTokenModal device={shown} onClose={() => setShown(null)} />
    </>
  );
}

function StatementDrawer({ merchant, onClose }: { merchant: Merchant | null; onClose: () => void }) {
  const t = useTranslations("merchants");
  const today = kampalaToday();
  const [range, setRange] = useState({ from: shiftDay(today, -29), to: today });
  const [page, setPage] = useState(1);
  const st = useApi<Statement>(merchant ? `/merchants/${merchant.id}/statement/` : null, { ...range, page });
  const total = st.data ? Math.max(1, Math.ceil(st.data.entries.count / 20)) : 1;
  return (
    <Drawer opened={!!merchant} onClose={onClose} position="right" size="xl" title={t("statementTitle", { name: merchant?.name ?? "" })}>
      <Stack>
        <DateRange {...range} onChange={setRange} />
        <ErrorAlert error={st.error} />
        {st.data && (
          <>
            <Group>
              <Text size="sm">
                {t("credits")}: <Money value={st.data.total_credits} />
              </Text>
              <Text size="sm">
                {t("debits")}: <Money value={st.data.total_debits} />
              </Text>
              {st.data.balances.map((b) => (
                <Text size="sm" key={b.wallet_id}>
                  {t("settlementBalance")}: <Money value={b.balance} />
                </Text>
              ))}
            </Group>
            <DataTable<LedgerEntry>
              rows={st.data.entries.results}
              page={page}
              totalPages={total}
              onPage={setPage}
              columns={[
                { key: "created_at", header: t("when"), render: (e) => formatDateTime(e.created_at) },
                { key: "entry_type", header: t("type"), render: (e) => e.entry_type.replace(/_/g, " ") },
                { key: "amount", header: t("amount"), render: (e) => <Money value={e.direction === "debit" ? `-${e.amount}` : e.amount} /> },
                { key: "reference_id", header: t("reference"), render: (e) => <span className="mono">{e.reference_id}</span> },
              ]}
            />
          </>
        )}
      </Stack>
    </Drawer>
  );
}

function NewMerchant({ onDone }: { onDone: () => void }) {
  const t = useTranslations("merchants");
  const [open, setOpen] = useState(false);
  const [v, setV] = useState({ name: "", category: "", contact_phone: "" });
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      await api.post("/merchants/", v);
      setOpen(false);
      setV({ name: "", category: "", contact_phone: "" });
      onDone();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <Button size="xs" onClick={() => setOpen(true)}>
        {t("new")}
      </Button>
      <Modal opened={open} onClose={() => setOpen(false)} title={t("new")} centered>
        <Stack>
          <Text size="xs" c="dimmed">
            {t("newHelp")}
          </Text>
          <TextInput label={t("name")} value={v.name} onChange={(e) => setV({ ...v, name: e.currentTarget.value })} required />
          <TextInput label={t("category")} placeholder="bookshop" value={v.category} onChange={(e) => setV({ ...v, category: e.currentTarget.value })} />
          <TextInput label={t("phone")} value={v.contact_phone} onChange={(e) => setV({ ...v, contact_phone: e.currentTarget.value })} />
          <ErrorAlert error={error} />
          <Group justify="flex-end">
            <Button onClick={submit} loading={busy} disabled={!v.name}>
              {t("create")}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
