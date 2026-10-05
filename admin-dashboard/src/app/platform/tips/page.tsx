"use client";

import { useTranslations } from "next-intl";

import { TipsManager } from "@/components/TipsManager";
import { PageHeader } from "@/components/ui";

export default function PlatformTipsPage() {
  const t = useTranslations("tips");
  return (
    <>
      <PageHeader title={t("platformTitle")} subtitle={t("platformSubtitle")} />
      <TipsManager global />
    </>
  );
}
