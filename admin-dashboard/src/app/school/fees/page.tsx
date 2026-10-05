"use client";

import { Button, Checkbox, Group, Modal, Select, Stack, Tabs, TagsInput, Text, TextInput } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChoiceFilter } from "@/components/filters";
import { MoneyInput } from "@/components/MoneyInput";
import { StudentPicker } from "@/components/StudentPicker";
import { ConfirmAction, DataTable, ErrorAlert, Money, PageHeader, StatusBadge } from "@/components/ui";
import { api, fetchAll, newIdempotencyKey, type Paginated } from "@/lib/api";
import { downloadCsv } from "@/lib/csv";
import { formatDate, formatDateTime } from "@/lib/dates";
import { useApi, usePaginated } from "@/lib/hooks";
import { formatUGX } from "@/lib/money";
import type { Student } from "@/lib/types";

type FeeCategory = {
  id: number;
  name: string;
  amount_type: "fixed" | "range";
  fixed_amount: string | null;
  min_amount: string | null;
  max_amount: string | null;
  active: boolean;
  due_date: string | null;
  applicable_classes: string[];
};
type FeePayment = { id: number; student: number; student_name: string; fee_category: number; fee_category_name: string; amount: string; paid_by: number; ledger_reference: string; status: string; created_at: string };

const amountLabel = (c: FeeCategory) => (c.amount_type === "fixed" ? formatUGX(c.fixed_amount) : `${formatUGX(c.min_amount)} – ${formatUGX(c.max_amount)}`);

export default function FeesPage() {
  const t = useTranslations("fees");
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <Tabs defaultValue="categories">
        <Tabs.List>
          <Tabs.Tab value="categories">{t("categories")}</Tabs.Tab>
          <Tabs.Tab value="payments">{t("payments")}</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="categories" pt="md">
          <Categories />
        </Tabs.Panel>
        <Tabs.Panel value="payments" pt="md">
          <Payments />
        </Tabs.Panel>
      </Tabs>
    </>
  );
}

function Categories() {
  const t = useTranslations("fees");
  const list = usePaginated<FeeCategory>("/fee-categories/");
  return (
    <>
      <Group justify="flex-end" mb="sm">
        <CategoryForm onDone={list.reload} />
      </Group>
      <DataTable<FeeCategory>
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        columns={[
          { key: "name", header: t("name") },
          { key: "amount", header: t("amount"), render: amountLabel },
          { key: "due_date", header: t("due"), render: (c) => formatDate(c.due_date) },
          { key: "classes", header: t("classes"), render: (c) => (c.applicable_classes.length ? c.applicable_classes.join(", ") : t("allClasses")) },
          { key: "active", header: t("active"), render: (c) => <StatusBadge status={c.active ? "active" : "closed"} /> },
          {
            key: "actions",
            header: "",
            render: (c) => (
              <Group gap="xs">
                <CategoryForm category={c} onDone={list.reload} />
                <PayFee category={c} onDone={list.reload} />
              </Group>
            ),
          },
        ]}
      />
    </>
  );
}

function CategoryForm({ category, onDone }: { category?: FeeCategory; onDone: () => void }) {
  const t = useTranslations("fees");
  const [open, setOpen] = useState(false);
  const [v, setV] = useState({
    name: category?.name ?? "",
    amount_type: category?.amount_type ?? "fixed",
    fixed_amount: category?.fixed_amount ?? "",
    min_amount: category?.min_amount ?? "",
    max_amount: category?.max_amount ?? "",
    due_date: category?.due_date ?? "",
    applicable_classes: category?.applicable_classes ?? [],
    active: category?.active ?? true,
  });
  const [error, setError] = useState<unknown>(null);
  const save = async () => {
    setError(null);
    const body = {
      ...v,
      fixed_amount: v.amount_type === "fixed" ? v.fixed_amount || null : null,
      min_amount: v.amount_type === "range" ? v.min_amount || null : null,
      max_amount: v.amount_type === "range" ? v.max_amount || null : null,
      due_date: v.due_date || null,
    };
    try {
      if (category) await api.patch(`/fee-categories/${category.id}/`, body);
      else await api.post("/fee-categories/", body);
      setOpen(false);
      onDone();
    } catch (e) {
      setError(e);
    }
  };
  return (
    <>
      <Button size="xs" variant={category ? "light" : "filled"} onClick={() => setOpen(true)}>
        {category ? t("edit") : t("newCategory")}
      </Button>
      <Modal opened={open} onClose={() => setOpen(false)} title={category ? t("edit") : t("newCategory")} centered>
        <Stack>
          <TextInput label={t("name")} placeholder="Exam fee" value={v.name} onChange={(e) => setV({ ...v, name: e.currentTarget.value })} required />
          <Select label={t("amountType")} value={v.amount_type} onChange={(x) => setV({ ...v, amount_type: (x as "fixed" | "range") ?? "fixed" })} allowDeselect={false} data={[{ value: "fixed", label: t("fixed") }, { value: "range", label: t("range") }]} />
          {v.amount_type === "fixed" ? (
            <MoneyInput label={t("fixedAmount")} value={v.fixed_amount} onChange={(x) => setV({ ...v, fixed_amount: x })} allowEmpty={false} />
          ) : (
            <Group grow>
              <MoneyInput label={t("min")} value={v.min_amount} onChange={(x) => setV({ ...v, min_amount: x })} allowEmpty={false} />
              <MoneyInput label={t("max")} value={v.max_amount} onChange={(x) => setV({ ...v, max_amount: x })} allowEmpty={false} />
            </Group>
          )}
          <TextInput type="date" label={t("due")} value={v.due_date} onChange={(e) => setV({ ...v, due_date: e.currentTarget.value })} />
          <TagsInput label={t("classes")} description={t("classesHelp")} value={v.applicable_classes} onChange={(x) => setV({ ...v, applicable_classes: x })} />
          <Checkbox label={t("active")} checked={v.active} onChange={(e) => setV({ ...v, active: e.currentTarget.checked })} />
          <ErrorAlert error={error} />
          <Group justify="flex-end">
            <Button onClick={save} disabled={!v.name}>
              {t("save")}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}

function PayFee({ category, onDone }: { category: FeeCategory; onDone: () => void }) {
  const t = useTranslations("fees");
  const [student, setStudent] = useState<Student | null>(null);
  const [amount, setAmount] = useState(category.fixed_amount ?? "");
  const [key, setKey] = useState(newIdempotencyKey);
  if (!category.active) return null;
  return (
    <ConfirmAction
      label={t("pay")}
      title={t("payTitle", { name: category.name })}
      description={<Text size="sm">{t("payHelp")}</Text>}
      canConfirm={!!student && !!amount}
      onConfirm={() => api.post("/fees/pay/", { student: student!.id, fee_category: category.id, amount, idempotency_key: key })}
      onDone={() => {
        setKey(newIdempotencyKey());
        setStudent(null);
        onDone();
      }}
    >
      <StudentPicker label={t("student")} value={student ? String(student.id) : null} onChange={(_v, s) => setStudent(s ?? null)} w="100%" />
      <MoneyInput label={t("amount")} value={amount} onChange={setAmount} disabled={category.amount_type === "fixed"} description={category.amount_type === "range" ? amountLabel(category) : undefined} />
    </ConfirmAction>
  );
}

function Payments() {
  const t = useTranslations("fees");
  const [category, setCategory] = useState("");
  const [student, setStudent] = useState<string | null>(null);
  const cats = useApi<Paginated<FeeCategory>>("/fee-categories/", { page_size: 100 });
  const filters = { fee_category: category, student: student ?? "" };
  const list = usePaginated<FeePayment>("/fees/payments/", filters);
  const exportCsv = async () => {
    const rows = await fetchAll<FeePayment>("/fees/payments/", filters);
    downloadCsv("fee-payments.csv", rows, ["id", "created_at", "student_name", "fee_category_name", "amount", "status", "ledger_reference"]);
  };
  return (
    <>
      <Group mb="sm" align="flex-end" justify="space-between">
        <Group align="flex-end">
          <ChoiceFilter label={t("category")} value={category} onChange={setCategory} options={(cats.data?.results ?? []).map((c) => ({ value: String(c.id), label: c.name }))} />
          <StudentPicker label={t("student")} value={student} onChange={setStudent} />
        </Group>
        <Button size="xs" variant="light" onClick={exportCsv}>
          {t("export")}
        </Button>
      </Group>
      <DataTable<FeePayment>
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        columns={[
          { key: "created_at", header: t("when"), render: (p) => formatDateTime(p.created_at) },
          { key: "student_name", header: t("student") },
          { key: "fee_category_name", header: t("category") },
          { key: "amount", header: t("amount"), render: (p) => <Money value={p.amount} /> },
          { key: "status", header: t("status"), render: (p) => <StatusBadge status={p.status} /> },
          { key: "ledger_reference", header: t("reference"), render: (p) => <span className="mono">{p.ledger_reference}</span> },
        ]}
      />
    </>
  );
}
