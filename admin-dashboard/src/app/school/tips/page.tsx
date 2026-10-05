"use client";

import { useTranslations } from "next-intl";

import { TipsManager } from "@/components/TipsManager";
import { PageHeader } from "@/components/ui";

export default function TipsPage() {
  const t = useTranslations("tips");
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <TipsManager />
    </>
  );
}
