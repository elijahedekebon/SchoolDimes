"use client";

import { Alert, Button, Card, Checkbox, ColorInput, Group, PasswordInput, SimpleGrid, Stack, Stepper, Switch, Text, TextInput, Textarea } from "@mantine/core";
import Link from "next/link";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { MoneyInput } from "@/components/MoneyInput";
import { ErrorAlert, PageHeader } from "@/components/ui";
import { api } from "@/lib/api";

type Result = { school: { id: number; name: string }; admin: { email: string } };

const LANGS = [
  { value: "en", label: "English" },
  { value: "lg", label: "Luganda" },
  { value: "sw", label: "Kiswahili" },
];

export default function OnboardPage() {
  const t = useTranslations("onboard");
  const [step, setStep] = useState(0);
  const [school, setSchool] = useState({ name: "", address: "", logo_url: "", primary_color: "#0E7C66", languages: ["en"] });
  const [policy, setPolicy] = useState({ daily_spend_cap: "", weekly_spend_cap: "", per_transaction_cap: "", p2p_daily_cap: "", low_balance_threshold: "2000", p2p_enabled: true });
  const [settings, setSettings] = useState({ offline_spend_ceiling: "2000", pin_lockout_threshold: 5, attendance_notify_guardians: false, attendance_on_canteen_devices: false });
  const [admin, setAdmin] = useState({ full_name: "", email: "", phone_number: "", password: "" });
  const [error, setError] = useState<unknown>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState<Result | null>(null);

  const submit = async () => {
    setBusy(true);
    setError(null);
    const nullIfEmpty = (v: string) => (v === "" ? null : v);
    try {
      const r = await api.post<Result>("/platform/schools/onboard/", {
        name: school.name,
        address: school.address,
        branding: { logo_url: school.logo_url, primary_color: school.primary_color },
        supported_languages: school.languages,
        policy: {
          daily_spend_cap: nullIfEmpty(policy.daily_spend_cap),
          weekly_spend_cap: nullIfEmpty(policy.weekly_spend_cap),
          per_transaction_cap: nullIfEmpty(policy.per_transaction_cap),
          p2p_daily_cap: nullIfEmpty(policy.p2p_daily_cap),
          low_balance_threshold: nullIfEmpty(policy.low_balance_threshold),
          p2p_enabled: policy.p2p_enabled,
        },
        settings,
        admin,
      });
      setDone(r);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  if (done)
    return (
      <>
        <PageHeader title={t("doneTitle", { name: done.school.name })} />
        <Alert color="green" title={t("ready")}>
          <Text size="sm">{t("doneHelp", { email: done.admin.email })}</Text>
        </Alert>
        <Group mt="md">
          <Button component={Link} href="/platform">
            {t("backToSchools")}
          </Button>
        </Group>
      </>
    );

  const valid = [!!school.name && school.languages.length > 0, true, true, !!admin.email && admin.password.length >= 8];
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <Stepper active={step} onStepClick={setStep} allowNextStepsSelect={false}>
        <Stepper.Step label={t("stepSchool")}>
          <Card withBorder>
            <Stack>
              <TextInput label={t("name")} value={school.name} onChange={(e) => setSchool({ ...school, name: e.currentTarget.value })} required data-testid="onboard-name" />
              <Textarea label={t("address")} value={school.address} onChange={(e) => setSchool({ ...school, address: e.currentTarget.value })} />
              <TextInput label={t("logoUrl")} placeholder="https://…/logo.png" value={school.logo_url} onChange={(e) => setSchool({ ...school, logo_url: e.currentTarget.value })} />
              <ColorInput label={t("primaryColor")} value={school.primary_color} onChange={(v) => setSchool({ ...school, primary_color: v })} format="hex" />
              <Checkbox.Group label={t("languages")} value={school.languages} onChange={(v) => setSchool({ ...school, languages: v })}>
                <Group mt="xs">
                  {LANGS.map((l) => (
                    <Checkbox key={l.value} value={l.value} label={l.label} />
                  ))}
                </Group>
              </Checkbox.Group>
            </Stack>
          </Card>
        </Stepper.Step>
        <Stepper.Step label={t("stepPolicy")}>
          <Card withBorder>
            <Text size="xs" c="dimmed" mb="sm">
              {t("policyHelp")}
            </Text>
            <SimpleGrid cols={{ base: 1, sm: 2 }}>
              {(["daily_spend_cap", "weekly_spend_cap", "per_transaction_cap", "p2p_daily_cap", "low_balance_threshold"] as const).map((k) => (
                <MoneyInput key={k} label={t(k)} description={t("blankNoLimit")} value={policy[k]} onChange={(v) => setPolicy({ ...policy, [k]: v })} />
              ))}
              <Switch mt="lg" label={t("p2p_enabled")} checked={policy.p2p_enabled} onChange={(e) => setPolicy({ ...policy, p2p_enabled: e.currentTarget.checked })} />
            </SimpleGrid>
          </Card>
        </Stepper.Step>
        <Stepper.Step label={t("stepPos")}>
          <Card withBorder>
            <SimpleGrid cols={{ base: 1, sm: 2 }}>
              <MoneyInput label={t("offline_spend_ceiling")} value={settings.offline_spend_ceiling} onChange={(v) => setSettings({ ...settings, offline_spend_ceiling: v })} allowEmpty={false} />
              <TextInput label={t("pin_lockout_threshold")} type="number" value={settings.pin_lockout_threshold} onChange={(e) => setSettings({ ...settings, pin_lockout_threshold: Number(e.currentTarget.value) || 5 })} />
            </SimpleGrid>
            <Stack mt="sm" gap="xs">
              <Switch label={t("attendance_notify_guardians")} checked={settings.attendance_notify_guardians} onChange={(e) => setSettings({ ...settings, attendance_notify_guardians: e.currentTarget.checked })} />
              <Switch label={t("attendance_on_canteen_devices")} checked={settings.attendance_on_canteen_devices} onChange={(e) => setSettings({ ...settings, attendance_on_canteen_devices: e.currentTarget.checked })} />
            </Stack>
          </Card>
        </Stepper.Step>
        <Stepper.Step label={t("stepAdmin")}>
          <Card withBorder>
            <Stack>
              <Text size="xs" c="dimmed">
                {t("adminHelp")}
              </Text>
              <TextInput label={t("adminName")} value={admin.full_name} onChange={(e) => setAdmin({ ...admin, full_name: e.currentTarget.value })} />
              <TextInput label={t("adminEmail")} type="email" value={admin.email} onChange={(e) => setAdmin({ ...admin, email: e.currentTarget.value })} required data-testid="onboard-admin-email" />
              <TextInput label={t("adminPhone")} value={admin.phone_number} onChange={(e) => setAdmin({ ...admin, phone_number: e.currentTarget.value })} />
              <PasswordInput label={t("adminPassword")} description={t("adminPasswordHelp")} value={admin.password} onChange={(e) => setAdmin({ ...admin, password: e.currentTarget.value })} required data-testid="onboard-admin-password" />
            </Stack>
          </Card>
        </Stepper.Step>
        <Stepper.Completed>
          <Card withBorder>
            <Text fw={600}>{t("review")}</Text>
            <Text size="sm">{t("reviewHelp", { name: school.name, email: admin.email })}</Text>
            <ErrorAlert error={error} />
          </Card>
        </Stepper.Completed>
      </Stepper>
      <Group justify="space-between" mt="md">
        <Button variant="default" onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0 || busy}>
          {t("back")}
        </Button>
        {step < 4 ? (
          <Button onClick={() => setStep((s) => s + 1)} disabled={!valid[step]} data-testid="onboard-next">
            {t("next")}
          </Button>
        ) : (
          <Button onClick={submit} loading={busy} color="green" data-testid="onboard-submit">
            {t("create")}
          </Button>
        )}
      </Group>
    </>
  );
}
