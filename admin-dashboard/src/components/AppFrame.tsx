"use client";

import {
  ActionIcon,
  AppShell,
  Avatar,
  Burger,
  Button,
  Group,
  Indicator,
  Menu,
  NavLink,
  Popover,
  ScrollArea,
  Select,
  Stack,
  Text,
  UnstyledButton,
} from "@mantine/core";
import { useDisclosure } from "@mantine/hooks";
import { IconBell, IconLogout } from "@tabler/icons-react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useLocale, useTranslations } from "next-intl";
import { type ReactNode, useEffect, useState } from "react";

import { api, type Paginated } from "@/lib/api";
import { formatDateTime } from "@/lib/dates";
import { useApi } from "@/lib/hooks";

import { useSetBranding } from "./Providers";

export type NavItem = { href: string; key: string; exact?: boolean };

type Me = { id: number; email: string; full_name: string; role: string; preferred_language: string };
type MySchool = { school: { id: number; name: string; branding: { logo_url?: string; primary_color?: string } } | null };
type Notification = { id: number; title: string; body: string; created_at: string; read_at: string | null; event_type: string };

export function AppFrame({ nav, area, children }: { nav: NavItem[]; area: "school" | "platform" | "student"; children: ReactNode }) {
  const t = useTranslations("nav");
  const [opened, { toggle, close }] = useDisclosure();
  const pathname = usePathname();
  const me = useApi<Me>("/me");
  const school = useApi<MySchool>("/my-school/");
  const setBranding = useSetBranding();

  useEffect(() => {
    setBranding(school.data?.school?.branding ?? null);
  }, [school.data, setBranding]);

  const title = area === "platform" ? t("platformTitle") : (school.data?.school?.name ?? "SchoolDimes");
  const logo = school.data?.school?.branding?.logo_url;

  return (
    <AppShell header={{ height: 60 }} navbar={{ width: 250, breakpoint: "sm", collapsed: { mobile: !opened } }} padding="md">
      <AppShell.Header>
        <Group h="100%" px="md" justify="space-between" wrap="nowrap">
          <Group wrap="nowrap" gap="sm">
            <Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" />
            {logo ? <Avatar src={logo} radius="sm" size="sm" /> : null}
            <Text fw={700} truncate data-testid="school-name">
              {title}
            </Text>
          </Group>
          <Group gap="xs" wrap="nowrap">
            <LanguageSwitcher />
            {area !== "student" && <NotificationBell />}
            <UserMenu me={me.data} />
          </Group>
        </Group>
      </AppShell.Header>
      <AppShell.Navbar p="xs">
        <ScrollArea>
          {nav.map((item) => {
            const active = item.exact ? pathname === item.href : pathname === item.href || pathname.startsWith(item.href + "/");
            return (
              <NavLink key={item.href} component={Link} href={item.href} label={t(item.key)} active={active} onClick={close} />
            );
          })}
        </ScrollArea>
      </AppShell.Navbar>
      <AppShell.Main>{children}</AppShell.Main>
    </AppShell>
  );
}

export function LanguageSwitcher() {
  const locale = useLocale();
  const router = useRouter();
  const change = async (value: string | null) => {
    if (!value || value === locale) return;
    await fetch("/api/auth/locale", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ locale: value }),
    });
    // keep the backend's preferred_language in sync (ignored when signed out)
    await api.patch("/me", { preferred_language: value }).catch(() => undefined);
    router.refresh();
  };
  return (
    <Select
      size="xs"
      w={120}
      value={locale}
      onChange={change}
      allowDeselect={false}
      aria-label="Language"
      data={[
        { value: "en", label: "English" },
        { value: "lg", label: "Luganda" },
        { value: "sw", label: "Kiswahili" },
      ]}
    />
  );
}

function NotificationBell() {
  const t = useTranslations("notifications");
  const [open, setOpen] = useState(false);
  const [tick, setTick] = useState(0);
  const list = useApi<Paginated<Notification> & { unread_count: number }>("/notifications/", { page_size: 8, _t: tick });
  useEffect(() => {
    const id = setInterval(() => setTick((x) => x + 1), 60_000);
    return () => clearInterval(id);
  }, []);
  const unread = list.data?.unread_count ?? 0;
  const markAll = async () => {
    await api.post("/notifications/read-all/");
    setTick((x) => x + 1);
  };
  const markOne = async (id: number) => {
    await api.post(`/notifications/${id}/read/`);
    setTick((x) => x + 1);
  };
  return (
    <Popover opened={open} onChange={setOpen} width={360} position="bottom-end" shadow="md">
      <Popover.Target>
        <Indicator label={unread} size={16} disabled={!unread} color="red">
          <ActionIcon variant="subtle" onClick={() => setOpen((o) => !o)} aria-label={t("title")} data-testid="bell">
            <IconBell size={20} />
          </ActionIcon>
        </Indicator>
      </Popover.Target>
      <Popover.Dropdown>
        <Group justify="space-between" mb="xs">
          <Text fw={600}>{t("title")}</Text>
          <Button size="compact-xs" variant="subtle" onClick={markAll} disabled={!unread}>
            {t("readAll")}
          </Button>
        </Group>
        <ScrollArea.Autosize mah={400}>
          <Stack gap="xs">
            {list.data?.results.length === 0 && (
              <Text size="sm" c="dimmed">
                {t("empty")}
              </Text>
            )}
            {list.data?.results.map((n) => (
              <UnstyledButton key={n.id} onClick={() => markOne(n.id)}>
                <Text size="sm" fw={n.read_at ? 400 : 700}>
                  {n.title}
                </Text>
                <Text size="xs" c="dimmed">
                  {n.body}
                </Text>
                <Text size="xs" c="dimmed">
                  {formatDateTime(n.created_at)}
                </Text>
              </UnstyledButton>
            ))}
          </Stack>
        </ScrollArea.Autosize>
      </Popover.Dropdown>
    </Popover>
  );
}

function UserMenu({ me }: { me?: Me }) {
  const t = useTranslations("nav");
  const router = useRouter();
  const logout = async () => {
    await fetch("/api/auth/logout", { method: "POST" });
    router.replace("/login");
    router.refresh();
  };
  return (
    <Menu position="bottom-end">
      <Menu.Target>
        <ActionIcon variant="subtle" aria-label="account">
          <Avatar size="sm" radius="xl">
            {(me?.full_name || me?.email || "?").slice(0, 1).toUpperCase()}
          </Avatar>
        </ActionIcon>
      </Menu.Target>
      <Menu.Dropdown>
        <Menu.Label>{me?.email}</Menu.Label>
        <Menu.Item leftSection={<IconLogout size={14} />} onClick={logout} data-testid="logout">
          {t("logout")}
        </Menu.Item>
      </Menu.Dropdown>
    </Menu>
  );
}
