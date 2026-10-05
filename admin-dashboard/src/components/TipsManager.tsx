"use client";

import { Button, Group, Modal, Select, Stack, TextInput, Textarea } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChoiceFilter } from "@/components/filters";
import { ConfirmAction, DataTable, ErrorAlert } from "@/components/ui";
import { api } from "@/lib/api";
import { usePaginated } from "@/lib/hooks";

type Tip = { id: number; school: number | null; title: string; body: string; language: string; target_age_range: string };
const LANGS = [
  { value: "en", label: "English" },
  { value: "lg", label: "Luganda" },
  { value: "sw", label: "Kiswahili" },
];

/** Financial-literacy tips CRUD. `global` (platform_admin) manages school=null tips. */
export function TipsManager({ global }: { global?: boolean }) {
  const t = useTranslations("tips");
  const [language, setLanguage] = useState("");
  const list = usePaginated<Tip>("/financial-literacy-tips/", { language });
  const rows = (list.data?.results ?? []).filter((r) => (global ? r.school === null : true));
  return (
    <>
      <Group justify="space-between" mb="sm" align="flex-end">
        <ChoiceFilter label={t("language")} value={language} onChange={setLanguage} options={LANGS} />
        <TipForm global={global} onDone={list.reload} />
      </Group>
      <DataTable<Tip>
        rows={rows}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        columns={[
          { key: "title", header: t("tipTitle") },
          { key: "language", header: t("language"), render: (r) => LANGS.find((l) => l.value === r.language)?.label ?? r.language },
          { key: "target_age_range", header: t("ages"), render: (r) => r.target_age_range || t("allAges") },
          { key: "scope", header: t("scope"), render: (r) => (r.school === null ? t("platformWide") : t("thisSchool")) },
          {
            key: "actions",
            header: "",
            render: (r) =>
              global || r.school !== null ? (
                <Group gap="xs">
                  <TipForm tip={r} global={global} onDone={list.reload} />
                  <ConfirmAction label={t("delete")} color="red" title={t("delete")} description={t("deleteHelp", { title: r.title })} onConfirm={() => api.del(`/financial-literacy-tips/${r.id}/`)} onDone={list.reload} />
                </Group>
              ) : null,
          },
        ]}
      />
    </>
  );
}

function TipForm({ tip, global, onDone }: { tip?: Tip; global?: boolean; onDone: () => void }) {
  const t = useTranslations("tips");
  const [open, setOpen] = useState(false);
  const [v, setV] = useState({ title: tip?.title ?? "", body: tip?.body ?? "", language: tip?.language ?? "en", target_age_range: tip?.target_age_range ?? "" });
  const [error, setError] = useState<unknown>(null);
  const save = async () => {
    setError(null);
    try {
      const body = global ? { ...v, school: null } : v;
      if (tip) await api.patch(`/financial-literacy-tips/${tip.id}/`, body);
      else await api.post("/financial-literacy-tips/", body);
      setOpen(false);
      onDone();
    } catch (e) {
      setError(e);
    }
  };
  return (
    <>
      <Button size="xs" variant={tip ? "light" : "filled"} onClick={() => setOpen(true)}>
        {tip ? t("edit") : t("new")}
      </Button>
      <Modal opened={open} onClose={() => setOpen(false)} title={tip ? t("edit") : t("new")} centered>
        <Stack>
          <TextInput label={t("tipTitle")} value={v.title} onChange={(e) => setV({ ...v, title: e.currentTarget.value })} required />
          <Textarea label={t("body")} autosize minRows={3} value={v.body} onChange={(e) => setV({ ...v, body: e.currentTarget.value })} required />
          <Select label={t("language")} value={v.language} onChange={(x) => setV({ ...v, language: x ?? "en" })} data={LANGS} allowDeselect={false} description={t("languageHelp")} />
          <TextInput label={t("ages")} placeholder="6-9" value={v.target_age_range} onChange={(e) => setV({ ...v, target_age_range: e.currentTarget.value })} />
          <ErrorAlert error={error} />
          <Group justify="flex-end">
            <Button onClick={save} disabled={!v.title || !v.body}>
              {t("save")}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
