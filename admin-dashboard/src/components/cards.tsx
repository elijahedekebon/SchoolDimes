"use client";

import { Alert, Button, Group, Modal, PasswordInput, Stack, Text, TextInput } from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useTranslations } from "next-intl";
import { useState } from "react";

import { api } from "@/lib/api";
import type { Card } from "@/lib/types";

import { ConfirmAction, ErrorAlert } from "./ui";

/** Mirrors backend cards.services.normalize_card_uid (lowercase hex, no separators). */
export function normalizeUid(raw: string): string | null {
  const uid = raw.trim().replace(/[\s:-]/g, "").toLowerCase();
  return /^[0-9a-f]{8,64}$/.test(uid) && uid.length % 2 === 0 ? uid : null;
}

const PIN_RE = /^\d{4,6}$/;

function PinFields({ pin, setPin, pin2, setPin2 }: { pin: string; setPin: (v: string) => void; pin2: string; setPin2: (v: string) => void }) {
  const t = useTranslations("cards");
  return (
    <>
      <PasswordInput label={t("pin")} description={t("pinHelp")} value={pin} onChange={(e) => setPin(e.currentTarget.value)} inputMode="numeric" maxLength={6} />
      <PasswordInput
        label={t("pinRepeat")}
        value={pin2}
        onChange={(e) => setPin2(e.currentTarget.value)}
        inputMode="numeric"
        maxLength={6}
        error={pin2 && pin !== pin2 ? t("pinMismatch") : undefined}
      />
    </>
  );
}

function UidField({ uid, setUid }: { uid: string; setUid: (v: string) => void }) {
  const t = useTranslations("cards");
  const normalized = uid ? normalizeUid(uid) : null;
  return (
    <TextInput
      label={t("uid")}
      description={t("uidHelp")}
      placeholder="04:A2:2B:7C:91:3E:80"
      value={uid}
      onChange={(e) => setUid(e.currentTarget.value)}
      error={uid && !normalized ? t("uidInvalid") : undefined}
      data-testid="card-uid-input"
      autoFocus
    />
  );
}

/** Issue a first card (POST /cards/issue/) or replace one (POST /cards/{id}/reissue/). */
export function IssueCardButton({
  studentId,
  studentName,
  replace,
  onDone,
}: {
  studentId: number;
  studentName: string;
  replace?: Card;
  onDone: () => void;
}) {
  const t = useTranslations("cards");
  const tc = useTranslations("common");
  const [open, setOpen] = useState(false);
  const [uid, setUid] = useState("");
  const [pin, setPin] = useState("");
  const [pin2, setPin2] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const normalized = uid ? normalizeUid(uid) : null;
  const valid = PIN_RE.test(pin) && pin === pin2 && (!uid || !!normalized);

  const submit = async () => {
    setBusy(true);
    setError(null);
    try {
      const body: Record<string, unknown> = { pin, ...(normalized ? { card_uid: normalized } : {}) };
      if (replace) await api.post(`/cards/${replace.id}/reissue/`, body);
      else await api.post("/cards/issue/", { ...body, student: studentId });
      notifications.show({ color: "green", message: t("issued") });
      setOpen(false);
      setUid("");
      setPin("");
      setPin2("");
      onDone();
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };

  return (
    <>
      <Button size="xs" color={replace ? "orange" : undefined} variant={replace ? "light" : "filled"} onClick={() => setOpen(true)} data-testid={replace ? "reissue-card" : "issue-card"}>
        {replace ? t("reissue") : t("issue")}
      </Button>
      <Modal opened={open} onClose={() => !busy && setOpen(false)} title={replace ? t("reissueTitle", { name: studentName }) : t("issueTitle", { name: studentName })} centered>
        <Stack>
          {replace && (
            <Alert color="orange" variant="light">
              {t("reissueWarning", { uid: replace.card_uid })}
            </Alert>
          )}
          <UidField uid={uid} setUid={setUid} />
          {normalized && (
            <Text size="xs" c="dimmed">
              {t("uidStoredAs")} <span className="mono">{normalized}</span>
            </Text>
          )}
          {!uid && (
            <Text size="xs" c="dimmed">
              {t("uidBlank")}
            </Text>
          )}
          <PinFields pin={pin} setPin={setPin} pin2={pin2} setPin2={setPin2} />
          <ErrorAlert error={error} />
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setOpen(false)} disabled={busy}>
              {tc("cancel")}
            </Button>
            <Button onClick={submit} loading={busy} disabled={!valid} data-testid="confirm-issue">
              {replace ? t("reissue") : t("issue")}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}

/** Freeze / unfreeze / report lost / reset PIN for one card. */
export function CardActions({ card, studentName, onDone }: { card: Card; studentName: string; onDone: () => void }) {
  const t = useTranslations("cards");
  const [pin, setPin] = useState("");
  const [pin2, setPin2] = useState("");
  if (card.status === "lost") {
    return <IssueCardButton studentId={card.student} studentName={studentName} replace={card} onDone={onDone} />;
  }
  return (
    <Group gap="xs">
      {card.status === "active" ? (
        <ConfirmAction
          label={t("freeze")}
          color="cyan"
          title={t("freezeTitle")}
          description={t("freezeHelp", { name: studentName })}
          onConfirm={() => api.post(`/cards/${card.id}/freeze/`)}
          onDone={onDone}
          testId="freeze-card"
        />
      ) : (
        <ConfirmAction
          label={t("unfreeze")}
          color="green"
          title={t("unfreezeTitle")}
          description={t("unfreezeHelp", { name: studentName })}
          onConfirm={() => api.post(`/cards/${card.id}/unfreeze/`)}
          onDone={onDone}
        />
      )}
      <ConfirmAction
        label={t("resetPin")}
        title={t("resetPinTitle")}
        description={t("resetPinHelp")}
        canConfirm={PIN_RE.test(pin) && pin === pin2}
        onConfirm={() => api.post(`/cards/${card.id}/reset-pin/`, { pin })}
        onDone={() => {
          setPin("");
          setPin2("");
          onDone();
        }}
      >
        <PinFields pin={pin} setPin={setPin} pin2={pin2} setPin2={setPin2} />
      </ConfirmAction>
      <ConfirmAction
        label={t("markLost")}
        color="red"
        title={t("markLostTitle")}
        description={t("markLostHelp", { name: studentName })}
        onConfirm={() => api.post(`/cards/${card.id}/report-lost/`)}
        onDone={onDone}
      />
    </Group>
  );
}
