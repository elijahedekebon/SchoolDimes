"use client";

import { Alert, Button, CopyButton, Group, Modal, Select, Stack, Text, TextInput } from "@mantine/core";
import { useTranslations } from "next-intl";
import { QRCodeSVG } from "qrcode.react";
import { useState } from "react";

import { api, type Paginated } from "@/lib/api";
import { useApi } from "@/lib/hooks";
import type { Device } from "@/lib/types";

import { ErrorAlert } from "./ui";

type Merchant = { id: number; name: string; my_school_approval: string | null };

/**
 * Device-provisioning QR payload (Part 3 scans this). JSON, UTF-8:
 *   {"type":"schooldimes_device","v":1,"api_base_url":"http://192.168.1.20:8000","device_token":"<raw token>"}
 * api_base_url is the backend origin the DEVICE must use (a LAN IP for a
 * phone on Wi-Fi), editable here before the code is shown.
 */
export function provisioningPayload(apiBaseUrl: string, token: string): string {
  return JSON.stringify({ type: "schooldimes_device", v: 1, api_base_url: apiBaseUrl.replace(/\/+$/, ""), device_token: token });
}

export function DeviceTokenModal({ device, onClose }: { device: Device | null; onClose: () => void }) {
  const t = useTranslations("devices");
  const [base, setBase] = useState(process.env.NEXT_PUBLIC_DEVICE_API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL || "");
  const token = device?.device_token ?? "";
  return (
    <Modal opened={!!device} onClose={onClose} title={t("tokenTitle", { name: device?.device_name ?? "" })} centered size="lg" closeOnClickOutside={false}>
      <Stack>
        <Alert color="red" variant="light" title={t("onceTitle")}>
          {t("onceHelp")}
        </Alert>
        <Text size="sm" fw={600}>
          {t("rawToken")}
        </Text>
        <Group wrap="nowrap" align="flex-start">
          <Text className="mono" size="sm" data-testid="device-token" style={{ flex: 1 }}>
            {token}
          </Text>
          <CopyButton value={token}>
            {({ copied, copy }) => (
              <Button size="xs" onClick={copy} color={copied ? "green" : undefined}>
                {copied ? t("copied") : t("copy")}
              </Button>
            )}
          </CopyButton>
        </Group>
        <TextInput label={t("deviceApiUrl")} description={t("deviceApiUrlHelp")} value={base} onChange={(e) => setBase(e.currentTarget.value)} />
        <Group justify="center" p="md" bg="white">
          {token && <QRCodeSVG value={provisioningPayload(base, token)} size={240} level="M" includeMargin />}
        </Group>
        <Text size="xs" c="dimmed">
          {t("qrHelp")}
        </Text>
        <Group justify="flex-end">
          <Button onClick={onClose} data-testid="token-saved">
            {t("iSavedIt")}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}

export function RegisterButton({ onRegistered, fixedMerchant }: { onRegistered: (d: Device) => void; fixedMerchant?: number }) {
  const t = useTranslations("devices");
  const [open, setOpen] = useState(false);
  const [name, setName] = useState("");
  const [role, setRole] = useState<string>(fixedMerchant ? "merchant" : "canteen");
  const [merchant, setMerchant] = useState<string | null>(fixedMerchant ? String(fixedMerchant) : null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const merchants = useApi<Paginated<Merchant>>(open && role === "merchant" ? "/merchants/" : null, { page_size: 100 });
  const approved = (merchants.data?.results ?? []).filter((m) => m.my_school_approval === "approved");
  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const d = await api.post<Device>("/pos/devices/register/", { device_name: name, device_role: role, ...(role === "merchant" ? { merchant: Number(merchant) } : {}) });
      setOpen(false);
      setName("");
      onRegistered(d);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <Button size="xs" onClick={() => setOpen(true)} data-testid="register-device">
        {t("register")}
      </Button>
      <Modal opened={open} onClose={() => setOpen(false)} title={t("registerTitle")} centered>
        <Stack>
          <TextInput label={t("name")} placeholder={t("namePlaceholder")} value={name} onChange={(e) => setName(e.currentTarget.value)} required data-testid="device-name" />
          <Select
            label={t("role")}
            value={role}
            onChange={(v) => setRole(v ?? "canteen")}
            allowDeselect={false}
            disabled={!!fixedMerchant}
            data={["canteen", "merchant", "attendance"].map((v) => ({ value: v, label: t(`role_${v}`) }))}
          />
          <Text size="xs" c="dimmed">
            {t(`roleHelp_${role}`)}
          </Text>
          {role === "merchant" && !fixedMerchant && (
            <Select label={t("merchant")} value={merchant} onChange={setMerchant} data={approved.map((m) => ({ value: String(m.id), label: m.name }))} required />
          )}
          <ErrorAlert error={error} />
          <Group justify="flex-end">
            <Button onClick={submit} loading={busy} disabled={!name || (role === "merchant" && !merchant)} data-testid="confirm-register">
              {t("register")}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}
