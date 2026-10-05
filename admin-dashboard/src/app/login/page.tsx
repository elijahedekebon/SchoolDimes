"use client";

import { Alert, Button, Center, Paper, PasswordInput, Stack, Text, TextInput, Title } from "@mantine/core";
import { useForm } from "@mantine/form";
import { useRouter, useSearchParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { Suspense, useEffect, useState } from "react";

function LoginForm() {
  const t = useTranslations("login");
  const router = useRouter();
  const params = useSearchParams();
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const refused = params.get("refused") === "1";
  const expired = params.get("expired") === "1";
  const form = useForm({ initialValues: { email: "", password: "" } });

  useEffect(() => {
    // A refused role or an expired session must not leave cookies behind.
    if (refused || expired) fetch("/api/auth/logout", { method: "POST" }).catch(() => undefined);
  }, [refused, expired]);

  const submit = form.onSubmit(async (values) => {
    setBusy(true);
    setError(null);
    try {
      const r = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(values),
      });
      const data = await r.json().catch(() => ({}));
      if (r.status === 403 && data.code === "role_not_allowed") {
        setError(t(data.role === "parent" ? "refusedParent" : "refusedStaff"));
      } else if (r.status === 429) {
        setError(data.detail || t("throttled"));
      } else if (!r.ok) {
        setError(data.detail || t("invalid"));
      } else {
        const next = params.get("next");
        router.replace(next && next.startsWith(data.home) ? next : data.home);
        router.refresh();
      }
    } finally {
      setBusy(false);
    }
  });

  return (
    <Center mih="100vh" bg="gray.0" p="md">
      <Paper withBorder shadow="sm" p="xl" w={380} maw="100%">
        <form onSubmit={submit}>
          <Stack>
            <Title order={2}>SchoolDimes</Title>
            <Text c="dimmed" size="sm">
              {t("subtitle")}
            </Text>
            {refused && <Alert color="orange">{t("refusedStaff")}</Alert>}
            {expired && <Alert color="yellow">{t("expired")}</Alert>}
            {error && (
              <Alert color="red" data-testid="login-error">
                {error}
              </Alert>
            )}
            <TextInput label={t("email")} type="email" required autoComplete="username" {...form.getInputProps("email")} />
            <PasswordInput label={t("password")} required autoComplete="current-password" {...form.getInputProps("password")} />
            <Button type="submit" loading={busy}>
              {t("submit")}
            </Button>
            <Text size="xs" c="dimmed">
              {t("whoFor")}
            </Text>
          </Stack>
        </form>
      </Paper>
    </Center>
  );
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  );
}
