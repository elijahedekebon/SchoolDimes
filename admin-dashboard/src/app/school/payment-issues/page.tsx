"use client";

import { useTranslations } from "next-intl";

import { DepositIssues } from "@/components/PaymentIssues";
import { PageHeader } from "@/components/ui";

export default function PaymentIssuesPage() {
  const t = useTranslations("paymentIssues");
  return (
    <>
      <PageHeader title={t("title")} subtitle={t("subtitle")} />
      <DepositIssues />
    </>
  );
}
