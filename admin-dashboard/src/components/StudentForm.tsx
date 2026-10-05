"use client";

import { Button, Group, Modal, Stack, TextInput } from "@mantine/core";
import { useForm } from "@mantine/form";
import { notifications } from "@mantine/notifications";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { api } from "@/lib/api";
import type { Student } from "@/lib/types";

import { ErrorAlert } from "./ui";

/** Create (POST /students/) or edit (PATCH /students/{id}/) a student. */
export function StudentFormButton({ student, onDone }: { student?: Student; onDone: (s: Student) => void }) {
  const t = useTranslations("students");
  const tc = useTranslations("common");
  const [open, setOpen] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const form = useForm({
    initialValues: {
      name: student?.name ?? "",
      class_name: student?.class_name ?? "",
      date_of_birth: student?.date_of_birth ?? "",
    },
    validate: {
      name: (v) => (v.trim() ? null : t("nameRequired")),
      class_name: (v) => (v.trim() ? null : t("classRequired")),
    },
  });
  const submit = form.onSubmit(async (v) => {
    setBusy(true);
    setError(null);
    try {
      const body = { ...v, date_of_birth: v.date_of_birth || null };
      const saved = student ? await api.patch<Student>(`/students/${student.id}/`, body) : await api.post<Student>("/students/", body);
      notifications.show({ color: "green", message: tc("done") });
      setOpen(false);
      if (!student) form.reset();
      onDone(saved);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  });
  return (
    <>
      <Button size="xs" variant={student ? "light" : "filled"} onClick={() => setOpen(true)} data-testid={student ? "edit-student" : "new-student"}>
        {student ? tc("edit") : t("new")}
      </Button>
      <Modal opened={open} onClose={() => setOpen(false)} title={student ? t("editTitle") : t("newTitle")} centered>
        <form onSubmit={submit}>
          <Stack>
            <TextInput label={t("name")} required {...form.getInputProps("name")} />
            <TextInput label={t("className")} placeholder="P4" required {...form.getInputProps("class_name")} />
            <TextInput label={t("dob")} type="date" {...form.getInputProps("date_of_birth")} />
            <ErrorAlert error={error} />
            <Group justify="flex-end">
              <Button type="submit" loading={busy}>
                {tc("save")}
              </Button>
            </Group>
          </Stack>
        </form>
      </Modal>
    </>
  );
}
