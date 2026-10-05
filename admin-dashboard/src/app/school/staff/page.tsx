"use client";

import { Button, Group, Modal, PasswordInput, Select, Stack, Text, TextInput } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChoiceFilter } from "@/components/filters";
import { ConfirmAction, DataTable, ErrorAlert, PageHeader, StatusBadge } from "@/components/ui";
import { api, type Paginated } from "@/lib/api";
import { formatDate } from "@/lib/dates";
import { useApi, usePaginated } from "@/lib/hooks";

type Staff = { id: number; email: string; full_name: string; phone_number: string; role: string; is_active: boolean; merchant_name: string | null; date_joined: string };
type Merchant = { id: number; name: string; my_school_approval: string | null };

export default function StaffPage() {
  const t = useTranslations("staff");
  const [role, setRole] = useState("");
  const list = usePaginated<Staff>("/users/", { role });
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} actions={<NewStaff onDone={list.reload} />} />
      <ChoiceFilter label={t("role")} value={role} onChange={setRole} options={["school_admin", "canteen_staff", "merchant_staff", "student"].map((r) => ({ value: r, label: t(`role_${r}`) }))} />
      <DataTable<Staff>
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        columns={[
          { key: "full_name", header: t("name"), render: (u) => u.full_name || "—" },
          { key: "email", header: t("email") },
          { key: "role", header: t("role"), render: (u) => t(`role_${u.role}`) },
          { key: "merchant_name", header: t("merchant"), render: (u) => u.merchant_name ?? "—" },
          { key: "is_active", header: t("status"), render: (u) => <StatusBadge status={u.is_active ? "active" : "suspended"} /> },
          { key: "date_joined", header: t("joined"), render: (u) => formatDate(u.date_joined) },
          {
            key: "actions",
            header: "",
            render: (u) => (
              <Group gap="xs">
                <ConfirmAction
                  label={u.is_active ? t("deactivate") : t("activate")}
                  color={u.is_active ? "red" : "green"}
                  title={u.is_active ? t("deactivate") : t("activate")}
                  description={u.is_active ? t("deactivateHelp", { email: u.email }) : t("activateHelp", { email: u.email })}
                  onConfirm={() => api.patch(`/users/${u.id}/`, { is_active: !u.is_active })}
                  onDone={list.reload}
                />
                <SetPassword user={u} />
              </Group>
            ),
          },
        ]}
      />
    </>
  );
}

function SetPassword({ user }: { user: Staff }) {
  const t = useTranslations("staff");
  const [pw, setPw] = useState("");
  return (
    <ConfirmAction label={t("setPassword")} title={t("setPasswordTitle", { email: user.email })} description={t("setPasswordHelp")} canConfirm={pw.length >= 8} onConfirm={() => api.post(`/users/${user.id}/set-password/`, { password: pw })} onDone={() => setPw("")}>
      <PasswordInput label={t("newPassword")} value={pw} onChange={(e) => setPw(e.currentTarget.value)} />
    </ConfirmAction>
  );
}

function NewStaff({ onDone }: { onDone: () => void }) {
  const t = useTranslations("staff");
  const [open, setOpen] = useState(false);
  const [v, setV] = useState({ email: "", full_name: "", phone_number: "", role: "canteen_staff", password: "", merchant: "" });
  const [error, setError] = useState<unknown>(null);
  const merchants = useApi<Paginated<Merchant>>(open ? "/merchants/" : null, { page_size: 100 });
  const approved = (merchants.data?.results ?? []).filter((m) => m.my_school_approval === "approved");
  const save = async () => {
    setError(null);
    try {
      await api.post("/users/", { ...v, merchant: v.role === "merchant_staff" ? Number(v.merchant) : undefined });
      setOpen(false);
      setV({ email: "", full_name: "", phone_number: "", role: "canteen_staff", password: "", merchant: "" });
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
          <Select label={t("role")} value={v.role} onChange={(x) => setV({ ...v, role: x ?? "canteen_staff" })} allowDeselect={false} data={["canteen_staff", "merchant_staff", "school_admin"].map((r) => ({ value: r, label: t(`role_${r}`) }))} />
          <Text size="xs" c="dimmed">
            {t(`roleHelp_${v.role}`)}
          </Text>
          {v.role === "merchant_staff" && <Select label={t("merchant")} value={v.merchant} onChange={(x) => setV({ ...v, merchant: x ?? "" })} data={approved.map((m) => ({ value: String(m.id), label: m.name }))} required />}
          <TextInput label={t("name")} value={v.full_name} onChange={(e) => setV({ ...v, full_name: e.currentTarget.value })} />
          <TextInput label={t("email")} type="email" value={v.email} onChange={(e) => setV({ ...v, email: e.currentTarget.value })} required />
          <TextInput label={t("phone")} value={v.phone_number} onChange={(e) => setV({ ...v, phone_number: e.currentTarget.value })} />
          <PasswordInput label={t("initialPassword")} description={t("passwordHelp")} value={v.password} onChange={(e) => setV({ ...v, password: e.currentTarget.value })} required />
          <ErrorAlert error={error} />
          <Group justify="flex-end">
            <Button onClick={save} disabled={!v.email || v.password.length < 8 || (v.role === "merchant_staff" && !v.merchant)}>
              {t("create")}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
