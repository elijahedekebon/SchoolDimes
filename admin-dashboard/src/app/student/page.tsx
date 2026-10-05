"use client";

import { Alert, Card, Group, Progress, SimpleGrid, Stack, Text, Title } from "@mantine/core";
import { useTranslations } from "next-intl";

import { ErrorAlert, Loading, Money } from "@/components/ui";
import { formatDateTime } from "@/lib/dates";
import { useApi } from "@/lib/hooks";

type Summary = {
  student: { first_name: string; name: string; class_name: string };
  school: { name: string };
  main_balance: string;
  savings_balance: string;
  savings_goals: Array<{ id: number; goal_name: string; target_amount: string; current_amount: string; progress_percent: number; is_reached: boolean }>;
  recent_purchases: Array<{ id: number; when: string; amount: string; place: string; items: Array<{ description: string; quantity: number; line_total: string }> }>;
  tip: { title: string; body: string } | null;
};

/** Read-only, deliberately simple portal for students. */
export default function StudentPortal() {
  const t = useTranslations("portal");
  const { data, error, loading } = useApi<Summary>("/student-portal/me/");
  if (error) return <ErrorAlert error={error} />;
  if (loading || !data) return <Loading />;
  return (
    <Stack maw={720} mx="auto">
      <Title order={2}>{t("hello", { name: data.student.first_name })}</Title>
      <SimpleGrid cols={{ base: 1, sm: 2 }}>
        <Card withBorder bg="teal.0">
          <Text size="sm" c="dimmed">
            {t("spending")}
          </Text>
          <Text size="xl" fw={800} data-testid="portal-balance">
            <Money value={data.main_balance} />
          </Text>
        </Card>
        <Card withBorder bg="yellow.0">
          <Text size="sm" c="dimmed">
            {t("savings")}
          </Text>
          <Text size="xl" fw={800}>
            <Money value={data.savings_balance} />
          </Text>
        </Card>
      </SimpleGrid>
      {data.savings_goals.length > 0 && (
        <Card withBorder>
          <Text fw={600} mb="xs">
            {t("goals")}
          </Text>
          {data.savings_goals.map((g) => (
            <Stack key={g.id} gap={4} mb="sm">
              <Group justify="space-between">
                <Text>
                  {g.goal_name} {g.is_reached ? "🎉" : ""}
                </Text>
                <Text size="sm" c="dimmed">
                  <Money value={g.current_amount} /> / <Money value={g.target_amount} />
                </Text>
              </Group>
              <Progress value={g.progress_percent} size="lg" color={g.is_reached ? "green" : "yellow"} />
            </Stack>
          ))}
        </Card>
      )}
      {data.tip && (
        <Alert color="grape" title={data.tip.title}>
          {data.tip.body}
        </Alert>
      )}
      <Card withBorder>
        <Text fw={600} mb="xs">
          {t("recent")}
        </Text>
        {data.recent_purchases.length === 0 && (
          <Text size="sm" c="dimmed">
            {t("noPurchases")}
          </Text>
        )}
        {data.recent_purchases.map((p) => (
          <Group key={p.id} justify="space-between" py={6} style={{ borderBottom: "1px solid var(--mantine-color-gray-2)" }} wrap="nowrap">
            <div>
              <Text size="sm">{p.items.length ? p.items.map((i) => `${i.quantity}× ${i.description}`).join(", ") : p.place}</Text>
              <Text size="xs" c="dimmed">
                {formatDateTime(p.when)} · {p.place}
              </Text>
            </div>
            <Money value={p.amount} />
          </Group>
        ))}
      </Card>
      <Text size="xs" c="dimmed" ta="center">
        {t("footer", { school: data.school.name })}
      </Text>
    </Stack>
  );
}
