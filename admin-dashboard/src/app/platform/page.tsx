"use client";

import { Button, Group } from "@mantine/core";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";

import { DataTable, ErrorAlert, Money, PageHeader } from "@/components/ui";
import { formatDate } from "@/lib/dates";
import { useApi } from "@/lib/hooks";

type Row = {
  id: number;
  name: string;
  created_at: string;
  students: number;
  school_admins: number;
  active_cards: number;
  active_devices: number;
  student_balances_total: string;
  sales_30d_count: number;
  sales_30d_collected: string;
  supported_languages: string[];
};

export default function SchoolsPage() {
  const t = useTranslations("platform");
  const router = useRouter();
  const stats = useApi<{ results: Row[] }>("/platform/schools/stats/");
  return (
    <>
      <PageHeader
        title={t("schools")}
        subtitle={t("schoolsHelp")}
        actions={
          <Button size="xs" component={Link} href="/platform/onboard">
            {t("onboard")}
          </Button>
        }
      />
      <ErrorAlert error={stats.error} />
      <DataTable<Row>
        testId="schools-table"
        rows={stats.data?.results}
        loading={stats.loading}
        onRowClick={(s) => router.push(`/platform/support?school=${s.id}`)}
        columns={[
          { key: "name", header: t("school") },
          { key: "students", header: t("students") },
          { key: "active_cards", header: t("activeCards") },
          { key: "active_devices", header: t("activeDevices") },
          { key: "school_admins", header: t("admins") },
          { key: "balances", header: t("balances"), render: (s) => <Money value={s.student_balances_total} /> },
          { key: "sales", header: t("sales30"), render: (s) => <Group gap={4}><Money value={s.sales_30d_collected} /> ({s.sales_30d_count})</Group> },
          { key: "languages", header: t("languages"), render: (s) => s.supported_languages.join(", ") },
          { key: "created_at", header: t("since"), render: (s) => formatDate(s.created_at) },
        ]}
      />
    </>
  );
}
