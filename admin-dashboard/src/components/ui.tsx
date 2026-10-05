"use client";

import {
  Alert,
  Badge,
  Button,
  type ButtonProps,
  Center,
  Group,
  Loader,
  Modal,
  Pagination,
  ScrollArea,
  Stack,
  Table,
  Text,
  Title,
} from "@mantine/core";
import { notifications } from "@mantine/notifications";
import { useTranslations } from "next-intl";
import { type ReactNode, useState } from "react";

import { ApiError } from "@/lib/api";
import { formatUGX } from "@/lib/money";

export function PageHeader({ title, subtitle, actions }: { title: ReactNode; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <Group justify="space-between" align="flex-start" mb="md" wrap="wrap">
      <div>
        <Title order={2}>{title}</Title>
        {subtitle && (
          <Text c="dimmed" size="sm">
            {subtitle}
          </Text>
        )}
      </div>
      {actions && <Group gap="xs">{actions}</Group>}
    </Group>
  );
}

/** Shows the backend's own (translated) message and its reason code(s). */
export function ErrorAlert({ error, title }: { error: unknown; title?: string }) {
  const t = useTranslations("common");
  if (!error) return null;
  const e = error instanceof ApiError ? error : null;
  return (
    <Alert color="red" title={title ?? t("error")} data-testid="error-alert">
      <Text size="sm">{e ? e.display : String(error)}</Text>
      {e?.code && (
        <Text size="xs" c="dimmed">
          {t("code")}: {[e.code, ...e.violations.filter((v) => v !== e.code)].join(", ")}
        </Text>
      )}
    </Alert>
  );
}

export function Money({ value, size, c }: { value: string | null | undefined; size?: string; c?: string }) {
  return (
    <Text span size={size} c={c} style={{ fontVariantNumeric: "tabular-nums", whiteSpace: "nowrap" }}>
      {formatUGX(value)}
    </Text>
  );
}

const STATUS_COLORS: Record<string, string> = {
  active: "green",
  approved: "green",
  applied: "green",
  confirmed: "green",
  verified: "green",
  completed: "green",
  resolved: "green",
  resolved_refunded: "green",
  redeemed: "green",
  succeeded: "green",
  open: "blue",
  pending: "yellow",
  pending_payment: "yellow",
  in_progress: "yellow",
  under_review: "yellow",
  recovery_pending: "yellow",
  frozen: "cyan",
  shortfall: "orange",
  duplicate: "gray",
  closed: "gray",
  dismissed: "gray",
  reviewed: "gray",
  disbursed: "gray",
  revoked: "red",
  lost: "red",
  failed: "red",
  rejected: "red",
  expired: "red",
  suspended: "red",
  cancelled: "red",
  resolved_denied: "red",
};

export function StatusBadge({ status }: { status: string | null | undefined }) {
  if (!status) return <Text span c="dimmed">—</Text>;
  return (
    <Badge color={STATUS_COLORS[status] ?? "gray"} variant="light" styles={{ root: { overflow: "visible" }, label: { overflow: "visible" } }}>
      {status.replace(/_/g, " ")}
    </Badge>
  );
}

export function Loading() {
  return (
    <Center p="xl">
      <Loader />
    </Center>
  );
}

export type Column<T> = { key: string; header: ReactNode; render?: (row: T) => ReactNode; width?: number | string };

export function DataTable<T extends { id?: number | string }>({
  columns,
  rows,
  loading,
  error,
  page,
  totalPages,
  onPage,
  onRowClick,
  empty,
  rowKey,
  testId,
}: {
  columns: Column<T>[];
  rows: T[] | undefined;
  loading?: boolean;
  error?: unknown;
  page?: number;
  totalPages?: number;
  onPage?: (p: number) => void;
  onRowClick?: (row: T) => void;
  empty?: ReactNode;
  rowKey?: (row: T, i: number) => string | number;
  testId?: string;
}) {
  const t = useTranslations("common");
  if (error) return <ErrorAlert error={error} />;
  return (
    <Stack gap="sm" data-testid={testId}>
      <ScrollArea>
        <Table striped highlightOnHover={!!onRowClick} verticalSpacing="xs" miw={columns.length > 4 ? columns.length * 110 : undefined}>
          <Table.Thead>
            <Table.Tr>
              {columns.map((c) => (
                <Table.Th key={c.key} w={c.width}>
                  {c.header}
                </Table.Th>
              ))}
            </Table.Tr>
          </Table.Thead>
          <Table.Tbody>
            {loading && !rows ? (
              <Table.Tr>
                <Table.Td colSpan={columns.length}>
                  <Loading />
                </Table.Td>
              </Table.Tr>
            ) : rows && rows.length === 0 ? (
              <Table.Tr>
                <Table.Td colSpan={columns.length}>
                  <Text c="dimmed" ta="center" p="md">
                    {empty ?? t("empty")}
                  </Text>
                </Table.Td>
              </Table.Tr>
            ) : (
              rows?.map((row, i) => (
                <Table.Tr
                  key={rowKey ? rowKey(row, i) : (row.id ?? i)}
                  onClick={onRowClick ? () => onRowClick(row) : undefined}
                  className={onRowClick ? "clickable-row" : undefined}
                >
                  {columns.map((c) => (
                    <Table.Td key={c.key}>
                      {c.render ? c.render(row) : String((row as Record<string, unknown>)[c.key] ?? "—")}
                    </Table.Td>
                  ))}
                </Table.Tr>
              ))
            )}
          </Table.Tbody>
        </Table>
      </ScrollArea>
      {onPage && totalPages && totalPages > 1 ? (
        <Group justify="flex-end">
          <Pagination value={page} onChange={onPage} total={totalPages} size="sm" />
        </Group>
      ) : null}
    </Stack>
  );
}

/**
 * A button that opens a confirmation dialog describing exactly what will
 * happen, runs `onConfirm`, and shows the backend's error inside the dialog.
 */
export function ConfirmAction({
  label,
  title,
  description,
  confirmLabel,
  onConfirm,
  onDone,
  color,
  disabled,
  buttonProps,
  children,
  canConfirm = true,
  successMessage,
  testId,
}: {
  label: ReactNode;
  title: ReactNode;
  description: ReactNode;
  confirmLabel?: ReactNode;
  onConfirm: () => Promise<unknown>;
  onDone?: (result: unknown) => void;
  color?: string;
  disabled?: boolean;
  buttonProps?: ButtonProps;
  children?: ReactNode;
  canConfirm?: boolean;
  successMessage?: string;
  testId?: string;
}) {
  const t = useTranslations("common");
  const [open, setOpen] = useState(false);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<unknown>(null);
  const run = async () => {
    setBusy(true);
    setError(null);
    try {
      const result = await onConfirm();
      setOpen(false);
      notifications.show({ color: "green", message: successMessage ?? t("done") });
      onDone?.(result);
    } catch (e) {
      setError(e);
    } finally {
      setBusy(false);
    }
  };
  return (
    <>
      <Button size="xs" variant="light" color={color} disabled={disabled} onClick={() => setOpen(true)} data-testid={testId} {...buttonProps}>
        {label}
      </Button>
      <Modal opened={open} onClose={() => !busy && setOpen(false)} title={title} centered>
        <Stack>
          <div>{description}</div>
          {children}
          <ErrorAlert error={error} />
          <Group justify="flex-end">
            <Button variant="default" onClick={() => setOpen(false)} disabled={busy}>
              {t("cancel")}
            </Button>
            <Button color={color} loading={busy} onClick={run} disabled={!canConfirm} data-testid="confirm-button">
              {confirmLabel ?? t("confirm")}
            </Button>
          </Group>
        </Stack>
      </Modal>
    </>
  );
}

export function Stat({ label, value, hint, href, color }: { label: ReactNode; value: ReactNode; hint?: ReactNode; href?: string; color?: string }) {
  const body = (
    <Stack gap={2}>
      <Text size="xs" c="dimmed" tt="uppercase" fw={600}>
        {label}
      </Text>
      <Text size="xl" fw={700} c={color}>
        {value}
      </Text>
      {hint && (
        <Text size="xs" c="dimmed">
          {hint}
        </Text>
      )}
    </Stack>
  );
  return href ? (
    <a href={href} style={{ textDecoration: "none", color: "inherit" }}>
      {body}
    </a>
  ) : (
    body
  );
}
