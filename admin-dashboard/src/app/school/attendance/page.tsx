"use client";

import { Badge, Button, Group, Tabs, Text, TextInput } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useEffect, useState } from "react";

import { DayPicker } from "@/components/filters";
import { StudentPicker } from "@/components/StudentPicker";
import { DataTable, ErrorAlert, PageHeader } from "@/components/ui";
import { fetchAll } from "@/lib/api";
import { downloadCsv } from "@/lib/csv";
import { formatDateTime, kampalaToday } from "@/lib/dates";
import { usePaginated } from "@/lib/hooks";
import type { Student } from "@/lib/types";

type Record_ = { id: number; student: number; student_name: string; direction: "in" | "out"; device_name: string; device_local_timestamp: string };
type Row = { id: number; name: string; class_name: string; firstIn: string | null; lastOut: string | null; taps: number };

const timeOnly = (iso: string | null) =>
  iso ? new Intl.DateTimeFormat("en-GB", { timeZone: "Africa/Kampala", hour: "2-digit", minute: "2-digit" }).format(new Date(iso)) : "—";

export default function AttendancePage() {
  const t = useTranslations("attendance");
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <Tabs defaultValue="register">
        <Tabs.List>
          <Tabs.Tab value="register">{t("register")}</Tabs.Tab>
          <Tabs.Tab value="student">{t("perStudent")}</Tabs.Tab>
        </Tabs.List>
        <Tabs.Panel value="register" pt="md">
          <Register />
        </Tabs.Panel>
        <Tabs.Panel value="student" pt="md">
          <PerStudent />
        </Tabs.Panel>
      </Tabs>
    </>
  );
}

/** Daily register: every student of a class, present if they tapped in that Kampala day. */
function Register() {
  const t = useTranslations("attendance");
  const [date, setDate] = useState(kampalaToday());
  const [className, setClassName] = useState("");
  const [rows, setRows] = useState<Row[] | null>(null);
  const [error, setError] = useState<unknown>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let live = true;
    Promise.all([fetchAll<Student>("/students/", { class_name: className }), fetchAll<Record_>("/attendance/", { date })])
      .then(([students, records]) => {
        if (!live) return;
        const byStudent = new Map<number, Record_[]>();
        for (const r of records) byStudent.set(r.student, [...(byStudent.get(r.student) ?? []), r]);
        setError(null);
        setRows(
          students.map((s) => {
            const recs = (byStudent.get(s.id) ?? []).sort((a, b) => a.device_local_timestamp.localeCompare(b.device_local_timestamp));
            const ins = recs.filter((r) => r.direction === "in");
            const outs = recs.filter((r) => r.direction === "out");
            return { id: s.id, name: s.name, class_name: s.class_name, firstIn: ins[0]?.device_local_timestamp ?? null, lastOut: outs.at(-1)?.device_local_timestamp ?? null, taps: recs.length };
          }),
        );
      })
      .catch((e) => live && setError(e));
    return () => {
      live = false;
    };
  }, [date, className, tick]);

  const present = rows?.filter((r) => r.firstIn).length ?? 0;
  const exportCsv = () =>
    rows &&
    downloadCsv(
      `attendance-${date}${className ? "-" + className : ""}.csv`,
      rows.map((r) => ({ student: r.name, class: r.class_name, status: r.firstIn ? "present" : "absent", first_in: timeOnly(r.firstIn), last_out: timeOnly(r.lastOut), taps: r.taps })),
    );
  return (
    <>
      <Group mb="sm" align="flex-end" justify="space-between">
        <Group align="flex-end">
          <DayPicker value={date} onChange={setDate} />
          <TextInput size="xs" label={t("class")} placeholder="P4" value={className} onChange={(e) => setClassName(e.currentTarget.value)} w={120} />
          <Button size="xs" variant="default" onClick={() => setTick((x) => x + 1)}>
            {t("refresh")}
          </Button>
        </Group>
        <Group>
          {rows && (
            <Text size="sm">
              {t("summary", { present, total: rows.length })}
            </Text>
          )}
          <Button size="xs" variant="light" onClick={exportCsv} disabled={!rows}>
            {t("export")}
          </Button>
        </Group>
      </Group>
      <ErrorAlert error={error} />
      <DataTable<Row>
        rows={rows ?? undefined}
        loading={!rows && !error}
        columns={[
          { key: "name", header: t("student") },
          { key: "class_name", header: t("class") },
          { key: "status", header: t("status"), render: (r) => (r.firstIn ? <Badge color="green">{t("present")}</Badge> : <Badge color="gray">{t("absent")}</Badge>) },
          { key: "firstIn", header: t("firstIn"), render: (r) => timeOnly(r.firstIn) },
          { key: "lastOut", header: t("lastOut"), render: (r) => timeOnly(r.lastOut) },
          { key: "taps", header: t("taps") },
        ]}
      />
      <Text size="xs" c="dimmed" mt="xs">
        {t("registerHelp")}
      </Text>
    </>
  );
}

function PerStudent() {
  const t = useTranslations("attendance");
  const [student, setStudent] = useState<string | null>(null);
  const list = usePaginated<Record_>(student ? `/students/${student}/attendance/` : null);
  const exportCsv = async () => {
    if (!student) return;
    const rows = await fetchAll<Record_>(`/students/${student}/attendance/`);
    downloadCsv(`attendance-student-${student}.csv`, rows, ["device_local_timestamp", "direction", "device_name", "student_name"]);
  };
  return (
    <>
      <Group mb="sm" align="flex-end" justify="space-between">
        <StudentPicker label={t("student")} value={student} onChange={setStudent} />
        <Button size="xs" variant="light" onClick={exportCsv} disabled={!student}>
          {t("export")}
        </Button>
      </Group>
      {student && (
        <DataTable<Record_>
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
      )}
    </>
  );
}
