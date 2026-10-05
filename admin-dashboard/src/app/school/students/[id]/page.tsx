"use client";

import { Alert, Button, Card as MCard, Group, Progress, Select, SimpleGrid, Stack, Tabs, Text, TextInput } from "@mantine/core";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { CardActions, IssueCardButton } from "@/components/cards";
import { StudentFormButton } from "@/components/StudentForm";
import { ConfirmAction, DataTable, ErrorAlert, Loading, Money, PageHeader, StatusBadge } from "@/components/ui";
import { api, type Paginated } from "@/lib/api";
import { useCatalogue } from "@/lib/catalogue";
import { formatDate, formatDateTime } from "@/lib/dates";
import { useApi, usePaginated } from "@/lib/hooks";
import type { Card, LedgerEntry, Student, Wallet } from "@/lib/types";

type Guardian = {
  id: number;
  parent: number;
  student: number;
  relationship: string;
  is_primary_contact: boolean;
  parent_email: string;
  parent_name: string;
  parent_phone: string;
  verification_status: string | null;
};
type Goal = { id: number; goal_name: string; target_amount: string; target_date: string | null; current_amount: string; progress_percent: number; is_reached: boolean };
type Effective = {
  daily_spend_cap: string | null;
  weekly_spend_cap: string | null;
  per_transaction_cap: string | null;
  p2p_daily_cap: string | null;
  p2p_enabled: boolean;
  low_balance_threshold: string | null;
  blocked_category_ids: number[];
  allowed_category_ids: number[] | null;
  blocked_product_ids: number[];
  blocked_merchant_ids: number[];
  allowed_merchant_ids: number[] | null;
};

export default function StudentDetailPage() {
  const t = useTranslations("student");
  const { id } = useParams<{ id: string }>();
  const student = useApi<Student>(`/students/${id}/`);
  if (student.error) return <ErrorAlert error={student.error} />;
  if (!student.data) return <Loading />;
  const s = student.data;
  return (
    <>
      <PageHeader
        title={s.name}
        subtitle={`${s.class_name || "—"} · ${t("born")} ${formatDate(s.date_of_birth)}`}
        actions={
          <>
            <Button component={Link} href="/school/students" size="xs" variant="default">
              {t("back")}
            </Button>
            <StudentFormButton student={s} onDone={student.reload} />
          </>
        }
      />
      <Tabs defaultValue="overview" keepMounted={false}>
        <Tabs.List>
          <Tabs.Tab value="overview">{t("overview")}</Tabs.Tab>
          <Tabs.Tab value="guardians">{t("guardians")}</Tabs.Tab>
          <Tabs.Tab value="cards">{t("cards")}</Tabs.Tab>
          <Tabs.Tab value="ledger">{t("ledger")}</Tabs.Tab>
          <Tabs.Tab value="p2p">{t("p2p")}</Tabs.Tab>
          <Tabs.Tab value="attendance">{t("attendance")}</Tabs.Tab>
          <Tabs.Tab value="disputes">{t("disputes")}</Tabs.Tab>
          <Tabs.Tab value="portal">{t("portal")}</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="overview" pt="md">
          <OverviewTab student={s} />
        </Tabs.Panel>
        <Tabs.Panel value="guardians" pt="md">
          <GuardiansTab student={s} />
        </Tabs.Panel>
        <Tabs.Panel value="cards" pt="md">
          <CardsTab student={s} />
        </Tabs.Panel>
        <Tabs.Panel value="ledger" pt="md">
          <LedgerTab student={s} />
        </Tabs.Panel>
        <Tabs.Panel value="p2p" pt="md">
          <P2PTab student={s} />
        </Tabs.Panel>
        <Tabs.Panel value="attendance" pt="md">
          <AttendanceTab student={s} />
        </Tabs.Panel>
        <Tabs.Panel value="disputes" pt="md">
          <DisputesTab student={s} />
        </Tabs.Panel>
        <Tabs.Panel value="portal" pt="md">
          <PortalTab student={s} />
        </Tabs.Panel>
      </Tabs>
    </>
  );
}

function OverviewTab({ student }: { student: Student }) {
  const t = useTranslations("student");
  const wallets = useApi<Paginated<Wallet>>("/wallets/", { student: student.id });
  const goals = useApi<Paginated<Goal>>("/savings-goals/", { student: student.id });
  const policy = useApi<Effective>(`/students/${student.id}/effective-policy/`);
  const overrides = useApi<Paginated<{ id: number; updated_by_role: string | null; updated_by_name: string | null; updated_at: string }>>(
    "/policies/",
    { student: student.id },
  );
  const cat = useCatalogue();
  const p = policy.data;
  const cap = (v: string | null) => (v === null ? t("noLimit") : <Money value={v} />);
  return (
    <SimpleGrid cols={{ base: 1, md: 2 }}>
      <MCard withBorder>
        <Text fw={600} mb="xs">
          {t("balances")}
        </Text>
        <ErrorAlert error={wallets.error} />
        {wallets.data?.results.map((w) => (
          <Group key={w.id} justify="space-between">
            <Text size="sm">{t(`wallet_${w.wallet_type}`)}</Text>
            <Money value={w.balance} />
          </Group>
        ))}
        <Text fw={600} mt="md" mb="xs">
          {t("goals")}
        </Text>
        {goals.data?.results.length === 0 && (
          <Text size="sm" c="dimmed">
            {t("noGoals")}
          </Text>
        )}
        {goals.data?.results.map((g) => (
          <Stack key={g.id} gap={2} mb="xs">
            <Group justify="space-between">
              <Text size="sm">
                {g.goal_name} {g.is_reached ? "✓" : ""}
              </Text>
              <Text size="xs" c="dimmed">
                <Money value={g.current_amount} /> / <Money value={g.target_amount} />
              </Text>
            </Group>
            <Progress value={g.progress_percent} color={g.is_reached ? "green" : undefined} />
          </Stack>
        ))}
      </MCard>
      <MCard withBorder>
        <Text fw={600} mb="xs">
          {t("effectivePolicy")}
        </Text>
        <ErrorAlert error={policy.error} />
        {p && (
          <Stack gap={4}>
            <Line label={t("dailyCap")} value={cap(p.daily_spend_cap)} />
            <Line label={t("weeklyCap")} value={cap(p.weekly_spend_cap)} />
            <Line label={t("perTxnCap")} value={cap(p.per_transaction_cap)} />
            <Line label={t("p2p")} value={p.p2p_enabled ? t("p2pOn") : t("p2pOff")} />
            <Line label={t("p2pCap")} value={cap(p.p2p_daily_cap)} />
            <Line label={t("lowBalance")} value={cap(p.low_balance_threshold)} />
            <Line label={t("blockedCategories")} value={cat.names(p.blocked_category_ids, cat.categories)} />
            <Line label={t("allowedCategories")} value={p.allowed_category_ids ? cat.names(p.allowed_category_ids, cat.categories) : t("all")} />
            <Line label={t("blockedItems")} value={cat.names(p.blocked_product_ids, cat.products)} />
            <Line label={t("blockedMerchants")} value={cat.names(p.blocked_merchant_ids, cat.merchants)} />
            {overrides.data?.results[0] && (
              <Alert variant="light" color="blue" mt="xs">
                {t("overrideBy", {
                  who: overrides.data.results[0].updated_by_name ?? "—",
                  role: overrides.data.results[0].updated_by_role ?? "—",
                  when: formatDateTime(overrides.data.results[0].updated_at),
                })}
              </Alert>
            )}
          </Stack>
        )}
      </MCard>
    </SimpleGrid>
  );
}

function Line({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <Group justify="space-between" wrap="nowrap">
      <Text size="sm" c="dimmed">
        {label}
      </Text>
      <Text size="sm" ta="right">
        {value}
      </Text>
    </Group>
  );
}

function GuardiansTab({ student }: { student: Student }) {
  const t = useTranslations("student");
  const list = useApi<Paginated<Guardian>>("/guardians/", { student: student.id });
  const [email, setEmail] = useState("");
  const [relationship, setRelationship] = useState("guardian");
  const [found, setFound] = useState<{ id: number; email: string; full_name: string } | null>(null);
  const [lookupError, setLookupError] = useState<unknown>(null);
  const lookup = async () => {
    setFound(null);
    setLookupError(null);
    try {
      setFound(await api.get("/users/lookup/", { email }));
    } catch (e) {
      setLookupError(e);
    }
  };
  return (
    <Stack>
      <DataTable<Guardian>
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        empty={t("noGuardians")}
        columns={[
          { key: "parent_name", header: t("guardianName"), render: (g) => g.parent_name || "—" },
          { key: "parent_email", header: t("email") },
          { key: "parent_phone", header: t("phone"), render: (g) => g.parent_phone || "—" },
          { key: "relationship", header: t("relationship") },
          { key: "primary", header: t("primary"), render: (g) => (g.is_primary_contact ? "✓" : "") },
          { key: "kyc", header: t("kyc"), render: (g) => <StatusBadge status={g.verification_status ?? "not_submitted"} /> },
          {
            key: "actions",
            header: "",
            render: (g) => (
              <ConfirmAction
                label={t("unlink")}
                color="red"
                title={t("unlinkTitle")}
                description={t("unlinkHelp", { parent: g.parent_email, student: student.name })}
                onConfirm={() => api.del(`/guardians/${g.id}/`)}
                onDone={list.reload}
              />
            ),
          },
        ]}
      />
      <MCard withBorder>
        <Text fw={600} mb="xs">
          {t("linkGuardian")}
        </Text>
        <Text size="xs" c="dimmed" mb="xs">
          {t("linkHelp")}
        </Text>
        <Group align="flex-end">
          <TextInput size="xs" label={t("email")} value={email} onChange={(e) => setEmail(e.currentTarget.value)} w={280} />
          <Button size="xs" variant="light" onClick={lookup} disabled={!email}>
            {t("find")}
          </Button>
        </Group>
        <ErrorAlert error={lookupError} />
        {found && (
          <Group mt="sm" align="flex-end">
            <Text size="sm">
              {found.full_name || found.email} ({found.email})
            </Text>
            <Select
              size="xs"
              label={t("relationship")}
              value={relationship}
              onChange={(v) => setRelationship(v ?? "guardian")}
              data={["mother", "father", "guardian", "other"]}
              allowDeselect={false}
              w={140}
            />
            <ConfirmAction
              label={t("link")}
              title={t("linkTitle")}
              description={t("linkConfirm", { parent: found.email, student: student.name })}
              onConfirm={() => api.post("/guardians/", { parent: found.id, student: student.id, relationship })}
              onDone={() => {
                setFound(null);
                setEmail("");
                list.reload();
              }}
            />
          </Group>
        )}
      </MCard>
    </Stack>
  );
}

function CardsTab({ student }: { student: Student }) {
  const t = useTranslations("student");
  const cards = useApi<Paginated<Card>>("/cards/", { student: student.id });
  const rows = cards.data?.results ?? [];
  const hasUsable = rows.some((c) => c.status !== "lost");
  return (
    <Stack>
      {!hasUsable && cards.data && (
        <Group>
          <Text size="sm" c="dimmed">
            {t("noActiveCard")}
          </Text>
          <IssueCardButton studentId={student.id} studentName={student.name} onDone={cards.reload} />
        </Group>
      )}
      <DataTable<Card>
        rows={cards.data?.results}
        loading={cards.loading}
        error={cards.error}
        empty={t("noCards")}
        columns={[
          { key: "card_uid", header: t("uid"), render: (c) => <span className="mono">{c.card_uid}</span> },
          { key: "status", header: t("status"), render: (c) => <StatusBadge status={c.status} /> },
          { key: "issued_at", header: t("issued"), render: (c) => formatDateTime(c.issued_at) },
          { key: "actions", header: "", render: (c) => <CardActions card={c} studentName={student.name} onDone={cards.reload} /> },
        ]}
      />
    </Stack>
  );
}

function LedgerTab({ student }: { student: Student }) {
  const t = useTranslations("student");
  const wallets = useApi<Paginated<Wallet>>("/wallets/", { student: student.id });
  const [walletId, setWalletId] = useState<string | null>(null);
  const current = walletId ?? (wallets.data?.results.find((w) => w.wallet_type === "main")?.id.toString() || null);
  const [page, setPage] = useState(1);
  const hist = useApi<{ balance: string; history: Paginated<LedgerEntry> }>(current ? `/wallets/${current}/balance/` : null, { page });
  const total = hist.data ? Math.max(1, Math.ceil(hist.data.history.count / 20)) : 1;
  return (
    <Stack>
      <Group align="flex-end">
        <Select
          size="xs"
          label={t("wallet")}
          value={current}
          onChange={(v) => {
            setWalletId(v);
            setPage(1);
          }}
          data={(wallets.data?.results ?? []).map((w) => ({ value: String(w.id), label: t(`wallet_${w.wallet_type}`) }))}
          allowDeselect={false}
        />
        {hist.data && (
          <Text size="sm">
            {t("balance")}: <Money value={hist.data.balance} />
          </Text>
        )}
      </Group>
      <DataTable<LedgerEntry>
        rows={hist.data?.history.results}
        loading={hist.loading}
        error={hist.error}
        page={page}
        totalPages={total}
        onPage={setPage}
        columns={[
          { key: "created_at", header: t("when"), render: (e) => formatDateTime(e.created_at) },
          { key: "entry_type", header: t("type"), render: (e) => e.entry_type.replace(/_/g, " ") },
          { key: "amount", header: t("amount"), render: (e) => <Money value={e.direction === "debit" ? `-${e.amount}` : e.amount} c={e.direction === "debit" ? "red" : "green"} /> },
          { key: "reference_id", header: t("reference"), render: (e) => <span className="mono">{e.reference_id || "—"}</span> },
          { key: "description", header: t("description") },
        ]}
      />
      <Text size="xs" c="dimmed">
        {t("ledgerHelp")}
      </Text>
    </Stack>
  );
}

type P2P = { id: number; sender_name: string; recipient_name: string; sender_student: number; amount: string; note: string; created_at: string; device: number | null };

function P2PTab({ student }: { student: Student }) {
  const t = useTranslations("student");
  const list = usePaginated<P2P>(`/students/${student.id}/p2p-history/`);
  return (
    <DataTable<P2P>
      rows={list.data?.results}
      loading={list.loading}
      error={list.error}
      page={list.page}
      totalPages={list.totalPages}
      onPage={list.setPage}
      columns={[
        { key: "created_at", header: t("when"), render: (r) => formatDateTime(r.created_at) },
        { key: "dir", header: t("direction"), render: (r) => (r.sender_student === student.id ? t("sent") : t("received")) },
        { key: "other", header: t("otherStudent"), render: (r) => (r.sender_student === student.id ? r.recipient_name : r.sender_name) },
        { key: "amount", header: t("amount"), render: (r) => <Money value={r.amount} /> },
        { key: "via", header: t("via"), render: (r) => (r.device ? t("viaPos") : t("viaParent")) },
        { key: "note", header: t("note") },
      ]}
    />
  );
}

type Attendance = { id: number; direction: string; device_name: string; device_local_timestamp: string };

function AttendanceTab({ student }: { student: Student }) {
  const t = useTranslations("student");
  const list = usePaginated<Attendance>(`/students/${student.id}/attendance/`);
  return (
    <DataTable<Attendance>
      rows={list.data?.results}
      loading={list.loading}
      error={list.error}
      page={list.page}
      totalPages={list.totalPages}
      onPage={list.setPage}
      columns={[
        { key: "time", header: t("when"), render: (r) => formatDateTime(r.device_local_timestamp) },
        { key: "direction", header: t("direction") },
        { key: "device_name", header: t("device") },
      ]}
    />
  );
}

type Dispute = { id: number; reason_category: string; status: string; original_amount: string; refund_amount: string; created_at: string };

function DisputesTab({ student }: { student: Student }) {
  const t = useTranslations("student");
  const router = useRouter();
  const list = usePaginated<Dispute>("/disputes/", { student: student.id });
  return (
    <DataTable<Dispute>
      rows={list.data?.results}
      loading={list.loading}
      error={list.error}
      page={list.page}
      totalPages={list.totalPages}
      onPage={list.setPage}
      onRowClick={(d) => router.push(`/school/disputes?open=${d.id}`)}
      columns={[
        { key: "id", header: "#" },
        { key: "created_at", header: t("when"), render: (r) => formatDateTime(r.created_at) },
        { key: "reason_category", header: t("reason") },
        { key: "original_amount", header: t("amount"), render: (r) => <Money value={r.original_amount} /> },
        { key: "status", header: t("status"), render: (r) => <StatusBadge status={r.status} /> },
        { key: "refund_amount", header: t("refunded"), render: (r) => <Money value={r.refund_amount} /> },
      ]}
    />
  );
}

/** Section H: a school-issued student portal login. */
function PortalTab({ student }: { student: Student }) {
  const t = useTranslations("student");
  const acct = useApi<{ email: string; is_active: boolean } | null>(`/students/${student.id}/portal-account/`);
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const exists = acct.data && acct.data.email;
  return (
    <MCard withBorder maw={560}>
      <Text size="sm" c="dimmed" mb="sm">
        {t("portalHelp")}
      </Text>
      {acct.error && acct.error.status !== 404 && <ErrorAlert error={acct.error} />}
      {exists ? (
        <Group justify="space-between">
          <Text size="sm">
            {t("portalLogin")}: <b>{acct.data!.email}</b>
          </Text>
          <ConfirmAction
            label={t("portalRemove")}
            color="red"
            title={t("portalRemove")}
            description={t("portalRemoveHelp")}
            onConfirm={() => api.del(`/students/${student.id}/portal-account/`)}
            onDone={acct.reload}
          />
        </Group>
      ) : (
        <Stack>
          <TextInput size="xs" label={t("portalEmail")} value={email} onChange={(e) => setEmail(e.currentTarget.value)} />
          <TextInput size="xs" type="password" label={t("portalPassword")} description={t("portalPasswordHelp")} value={password} onChange={(e) => setPassword(e.currentTarget.value)} />
          <ConfirmAction
            label={t("portalCreate")}
            title={t("portalCreate")}
            description={t("portalCreateHelp", { name: student.name })}
            canConfirm={!!email && password.length >= 8}
            onConfirm={() => api.post(`/students/${student.id}/portal-account/`, { email, password })}
            onDone={() => {
              setPassword("");
              acct.reload();
            }}
          />
        </Stack>
      )}
    </MCard>
  );
}
