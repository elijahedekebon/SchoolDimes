"use client";

import { Badge, Group, Switch, Text } from "@mantine/core";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { DeviceTokenModal, RegisterButton } from "@/components/DeviceToken";
import { ChoiceFilter } from "@/components/filters";
import { ConfirmAction, DataTable, PageHeader, StatusBadge } from "@/components/ui";
import { api } from "@/lib/api";
import { formatDateTime, hoursSince } from "@/lib/dates";
import { useApi, usePaginated } from "@/lib/hooks";
import type { Device } from "@/lib/types";

type Settings = { device_stale_after_hours: number };

export default function DevicesPage() {
  const t = useTranslations("devices");
  const [role, setRole] = useState("");
  const [status, setStatus] = useState("");
  const [staleOnly, setStaleOnly] = useState(false);
  const [shown, setShown] = useState<Device | null>(null);
  const settings = useApi<Settings>("/school-settings/");
  const list = usePaginated<Device>("/pos/devices/", { device_role: role, status, stale: staleOnly ? "true" : "" });
  const staleAfter = settings.data?.device_stale_after_hours ?? 24;
  const isStale = (d: Device) => d.status === "active" && (hoursSince(d.last_sync_at ?? d.created_at) ?? 0) > staleAfter;

  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle", { hours: staleAfter })} actions={<RegisterButton onRegistered={(d) => { setShown(d); list.reload(); }} />} />
      <Group mb="sm" align="flex-end">
        <ChoiceFilter label={t("role")} value={role} onChange={setRole} options={["canteen", "merchant", "attendance"].map((v) => ({ value: v, label: t(`role_${v}`) }))} />
        <ChoiceFilter label={t("status")} value={status} onChange={setStatus} options={["active", "revoked"].map((v) => ({ value: v, label: v }))} />
        <Switch label={t("staleOnly")} checked={staleOnly} onChange={(e) => setStaleOnly(e.currentTarget.checked)} />
      </Group>
      <DataTable<Device>
        testId="devices-table"
        rows={list.data?.results}
        loading={list.loading}
        error={list.error}
        page={list.page}
        totalPages={list.totalPages}
        onPage={list.setPage}
        columns={[
          {
            key: "device_name",
            header: t("name"),
            render: (d) => (
              <Group gap={6}>
                {d.device_name}
                {isStale(d) && (
                  <Badge color="red" size="xs">
                    {t("stale")}
                  </Badge>
                )}
              </Group>
            ),
          },
          { key: "device_role", header: t("role"), render: (d) => t(`role_${d.device_role}`) },
          { key: "token_prefix", header: t("tokenPrefix"), render: (d) => <span className="mono">{d.token_prefix}…</span> },
          { key: "status", header: t("status"), render: (d) => <StatusBadge status={d.status} /> },
          { key: "last_seen_at", header: t("lastSeen"), render: (d) => formatDateTime(d.last_seen_at) },
          { key: "last_sync_at", header: t("lastSync"), render: (d) => <Text size="sm" c={isStale(d) ? "red" : undefined}>{formatDateTime(d.last_sync_at)}</Text> },
          { key: "app_version", header: t("appVersion"), render: (d) => d.app_version || "—" },
          {
            key: "actions",
            header: "",
            render: (d) =>
              d.status === "active" ? (
                <Group gap="xs">
                  <ConfirmAction
                    label={t("rotate")}
                    title={t("rotateTitle")}
                    description={t("rotateHelp", { name: d.device_name })}
                    onConfirm={() => api.post<Device>(`/pos/devices/${d.id}/rotate-token/`)}
                    onDone={(r) => {
                      setShown(r as Device);
                      list.reload();
                    }}
                  />
                  <ConfirmAction
                    label={t("revoke")}
                    color="red"
                    title={t("revokeTitle")}
                    description={t("revokeHelp", { name: d.device_name })}
                    onConfirm={() => api.post(`/pos/devices/${d.id}/revoke/`)}
                    onDone={list.reload}
                    testId="revoke-device"
                  />
                </Group>
              ) : null,
          },
        ]}
      />
      <DeviceTokenModal device={shown} onClose={() => setShown(null)} />
    </>
  );
}
