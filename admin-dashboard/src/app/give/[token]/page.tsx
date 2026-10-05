"use client";

import {
  Alert,
  Badge,
  Box,
  Button,
  Card,
  Center,
  Container,
  Group,
  Loader,
  SegmentedControl,
  Stack,
  Text,
  TextInput,
  Textarea,
  Title,
} from "@mantine/core";
import { useParams } from "next/navigation";
import { useTranslations } from "next-intl";
import { useEffect, useRef, useState } from "react";

import { LanguageSwitcher } from "@/components/AppFrame";
import { ErrorAlert, Money } from "@/components/ui";
import { ApiError, apiFetch, newIdempotencyKey } from "@/lib/api";
import { formatUGX, isValidAmount } from "@/lib/money";

type LinkInfo = { student_first_name: string; school_name: string };
type Instructions =
  | { type: "momo_prompt"; phone_number: string; message: string }
  | { type: "ussd"; ussd_code: string; message: string }
  | { type: "bank_transfer"; bank_name: string; account_name: string; account_number: string; narration: string; message: string };
type PublicDeposit = { reference: string; amount: string; channel: string; status: string; instructions: Instructions; failure_reason: string; confirmed_at: string | null };

const pub = <T,>(path: string, opts: { method?: string; body?: unknown } = {}) => apiFetch<T>(path, { ...opts, base: "direct" });
const MIN_FILL_MS = 3000;

/**
 * Public contributor page (no login, no app). Shows only what the public
 * endpoint returns: the student's first name and the school's name.
 */
export default function GivePage() {
  const t = useTranslations("give");
  const { token } = useParams<{ token: string }>();
  const [info, setInfo] = useState<LinkInfo | null>(null);
  const [linkError, setLinkError] = useState<ApiError | null>(null);
  const [deposit, setDeposit] = useState<PublicDeposit | null>(null);

  useEffect(() => {
    pub<LinkInfo>(`/public/topup-links/${encodeURIComponent(token)}/`)
      .then(setInfo)
      .catch((e) => setLinkError(e instanceof ApiError ? e : new ApiError(0, {})));
  }, [token]);

  return (
    <Box bg="gray.0" mih="100vh" py="xl">
      <Container size={480} px="md">
        <Group justify="space-between" mb="md">
          <Text fw={800} c="teal.8">
            SchoolDimes
          </Text>
          <LanguageSwitcher />
        </Group>
        {!info && !linkError && (
          <Center p="xl">
            <Loader />
          </Center>
        )}
        {linkError && (
          <Alert color={linkError.status === 429 ? "yellow" : "red"} title={linkError.status === 429 ? t("busyTitle") : t("invalidTitle")} data-testid="link-invalid">
            {linkError.status === 429 ? t("busy") : t("invalid")}
          </Alert>
        )}
        {info && !deposit && <GiveForm token={token} info={info} onCreated={setDeposit} />}
        {info && deposit && <PaymentStatus token={token} info={info} initial={deposit} onAgain={() => setDeposit(null)} />}
        <Text size="xs" c="dimmed" ta="center" mt="xl">
          {t("privacy")}
        </Text>
      </Container>
    </Box>
  );
}

function GiveForm({ token, info, onCreated }: { token: string; info: LinkInfo; onCreated: (d: PublicDeposit) => void }) {
  const t = useTranslations("give");
  const [kind, setKind] = useState<"topup" | "gift">("topup");
  const [v, setV] = useState({ name: "", phone_number: "", email: "", relationship_label: "", amount: "", channel: "momo", payer_phone: "", message: "" });
  const [honeypot, setHoneypot] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const shownAt = useRef(0);
  // one key per attempt; a retry after a network error reuses it, so it can never pay twice
  const key = useRef(newIdempotencyKey());

  useEffect(() => {
    shownAt.current = Date.now();
  }, []);

  const valid = v.name.trim() && (v.phone_number.trim() || v.email.trim()) && isValidAmount(v.amount) && (v.channel === "bank" || (v.payer_phone || v.phone_number).trim());
  const submit = async () => {
    if (honeypot || Date.now() - shownAt.current < MIN_FILL_MS) {
      setError(t("tooFast"));
      return;
    }
    setBusy(true);
    setError(null);
    const body = {
      contributor: { name: v.name.trim(), phone_number: v.phone_number.trim(), email: v.email.trim(), relationship_label: v.relationship_label.trim() },
      amount: v.amount,
      channel: v.channel,
      payer_phone: (v.payer_phone || v.phone_number).trim(),
      idempotency_key: key.current,
      ...(kind === "gift" ? { message: v.message } : {}),
    };
    try {
      if (kind === "gift") {
        const r = await pub<{ deposit: PublicDeposit }>(`/public/topup-links/${encodeURIComponent(token)}/gift-vouchers/`, { method: "POST", body });
        onCreated(r.deposit);
      } else {
        onCreated(await pub<PublicDeposit>(`/public/topup-links/${encodeURIComponent(token)}/deposits/`, { method: "POST", body }));
      }
      key.current = newIdempotencyKey();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <Card withBorder shadow="sm" p="lg">
      <Stack>
        <Title order={3}>{t("title", { name: info.student_first_name })}</Title>
        <Text size="sm" c="dimmed">
          {t("subtitle", { name: info.student_first_name, school: info.school_name })}
        </Text>
        <SegmentedControl
          fullWidth
          value={kind}
          onChange={(x) => setKind(x as "topup" | "gift")}
          data={[
            { value: "topup", label: t("topup") },
            { value: "gift", label: t("gift") },
          ]}
        />
        <TextInput label={t("yourName")} value={v.name} onChange={(e) => setV({ ...v, name: e.currentTarget.value })} required data-testid="give-name" />
        <TextInput label={t("relationship")} placeholder={t("relationshipPlaceholder")} value={v.relationship_label} onChange={(e) => setV({ ...v, relationship_label: e.currentTarget.value })} />
        <Group grow>
          <TextInput label={t("phone")} placeholder="0772 000 111" value={v.phone_number} onChange={(e) => setV({ ...v, phone_number: e.currentTarget.value })} data-testid="give-phone" />
          <TextInput label={t("email")} type="email" value={v.email} onChange={(e) => setV({ ...v, email: e.currentTarget.value })} />
        </Group>
        <Text size="xs" c="dimmed" mt={-8}>
          {t("phoneOrEmail")}
        </Text>
        <TextInput
          label={t("amount")}
          inputMode="decimal"
          leftSection={<span style={{ fontSize: 11 }}>UGX</span>}
          leftSectionWidth={44}
          value={v.amount}
          onChange={(e) => setV({ ...v, amount: e.currentTarget.value.trim() })}
          error={v.amount && !isValidAmount(v.amount) ? t("amountInvalid") : undefined}
          required
          data-testid="give-amount"
        />
        {kind === "gift" && <Textarea label={t("message")} maxLength={280} placeholder={t("messagePlaceholder")} value={v.message} onChange={(e) => setV({ ...v, message: e.currentTarget.value })} />}
        <SegmentedControl
          fullWidth
          value={v.channel}
          onChange={(x) => setV({ ...v, channel: x })}
          data={[
            { value: "momo", label: t("momo") },
            { value: "ussd", label: t("ussd") },
            { value: "bank", label: t("bank") },
          ]}
        />
        {v.channel !== "bank" && (
          <TextInput label={t("payerPhone")} description={t("payerPhoneHelp")} placeholder={v.phone_number} value={v.payer_phone} onChange={(e) => setV({ ...v, payer_phone: e.currentTarget.value })} />
        )}
        {/* bot trap: humans never see or fill this */}
        <input type="text" name="website" tabIndex={-1} autoComplete="off" value={honeypot} onChange={(e) => setHoneypot(e.target.value)} style={{ position: "absolute", left: "-10000px", width: 1, height: 1 }} aria-hidden="true" />
        {typeof error === "string" ? <Alert color="yellow">{error}</Alert> : <ErrorAlert error={error} />}
        <Button size="md" onClick={submit} loading={busy} disabled={!valid} data-testid="give-submit">
          {t("continue", { amount: isValidAmount(v.amount) ? formatUGX(v.amount) : "" })}
        </Button>
      </Stack>
    </Card>
  );
}

function PaymentStatus({ token, info, initial, onAgain }: { token: string; info: LinkInfo; initial: PublicDeposit; onAgain: () => void }) {
  const t = useTranslations("give");
  const [d, setD] = useState(initial);
  const [polls, setPolls] = useState(0);
  const pending = d.status === "pending";
  const giveUp = polls >= 60; // ~3 minutes

  useEffect(() => {
    if (!pending || giveUp) return;
    const id = setTimeout(async () => {
      try {
        setD(await pub<PublicDeposit>(`/public/topup-links/${encodeURIComponent(token)}/deposits/${encodeURIComponent(d.reference)}/`));
      } catch {
        /* keep polling through a flaky connection */
      }
      setPolls((p) => p + 1);
    }, 3000);
    return () => clearTimeout(id);
  }, [pending, giveUp, polls, token, d.reference]);

  const ins = d.instructions;
  return (
    <Card withBorder shadow="sm" p="lg">
      <Stack>
        <Group justify="space-between">
          <Title order={4}>
            <Money value={d.amount} /> → {info.student_first_name}
          </Title>
          <Badge size="lg" color={d.status === "confirmed" ? "green" : pending ? "yellow" : "red"} data-testid="give-status">
            {t(`status_${d.status}`)}
          </Badge>
        </Group>
        {pending && ins && (
          <Alert color="blue" title={t("howToPay")}>
            <Stack gap={4}>
              <Text size="sm">{ins.message}</Text>
              {ins.type === "ussd" && (
                <Text size="lg" fw={800} className="mono">
                  {ins.ussd_code}
                </Text>
              )}
              {ins.type === "bank_transfer" && (
                <Text size="sm">
                  {ins.bank_name} · {ins.account_name} · <b className="mono">{ins.account_number}</b> · {t("narration")}: <b className="mono">{ins.narration}</b>
                </Text>
              )}
            </Stack>
          </Alert>
        )}
        {pending && !giveUp && (
          <Group gap="xs">
            <Loader size="xs" />
            <Text size="sm" c="dimmed">
              {t("waiting")}
            </Text>
          </Group>
        )}
        {pending && giveUp && <Alert color="yellow">{t("stillPending")}</Alert>}
        {d.status === "confirmed" && (
          <Alert color="green" title={t("thanksTitle")}>
            {t("thanks", { name: info.student_first_name })}
          </Alert>
        )}
        {(d.status === "failed" || d.status === "expired") && <Alert color="red">{t("failed", { reason: d.failure_reason || d.status })}</Alert>}
        <Text size="xs" c="dimmed">
          {t("reference")}: <span className="mono">{d.reference}</span>
        </Text>
        {!pending && (
          <Button variant="light" onClick={onAgain}>
            {t("again")}
          </Button>
        )}
      </Stack>
    </Card>
  );
}
