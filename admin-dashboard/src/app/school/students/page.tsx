"use client";

import { Group, Switch, TextInput } from "@mantine/core";
import { useDebouncedValue } from "@mantine/hooks";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { ChoiceFilter } from "@/components/filters";
import { StudentFormButton } from "@/components/StudentForm";
import { DataTable, PageHeader } from "@/components/ui";
import { formatDate } from "@/lib/dates";
import { usePaginated } from "@/lib/hooks";
import type { Student } from "@/lib/types";

export default function StudentsPage() {
  const t = useTranslations("students");
  const router = useRouter();
  const [search, setSearch] = useState("");
  const [q] = useDebouncedValue(search, 300);
  const [cardStatus, setCardStatus] = useState("");
  const [low, setLow] = useState(false);
  const list = usePaginated<Student>("/students/", { search: q, card_status: cardStatus, low_balance: low ? "true" : "" });

  return (
    <>
      <PageHeader title={t("title")} actions={<StudentFormButton onDone={(s) => router.push(`/school/students/${s.id}`)} />} />
      <Group mb="sm" align="flex-end">
        <TextInput size="xs" label={t("search")} placeholder={t("searchPlaceholder")} value={search} onChange={(e) => setSearch(e.currentTarget.value)} w={260} />
        <ChoiceFilter
          label={t("cardStatus")}
          value={cardStatus}
          onChange={setCardStatus}
          options={["active", "frozen", "lost", "none"].map((v) => ({ value: v, label: t(`card_${v}`) }))}
        />
        <Switch label={t("lowBalance")} checked={low} onChange={(e) => setLow(e.currentTarget.checked)} />
      </Group>
      <DataTable<Student>
        testId="students-table"
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        onRowClick={(s) => router.push(`/school/students/${s.id}`)}
        columns={[
          { key: "name", header: t("name") },
          { key: "class_name", header: t("className") },
          { key: "dob", header: t("dob"), render: (s) => formatDate(s.date_of_birth) },
          { key: "created_at", header: t("added"), render: (s) => formatDate(s.created_at) },
        ]}
      />
    </>
  );
}
