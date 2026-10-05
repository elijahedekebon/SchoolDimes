import { AppFrame, type NavItem } from "@/components/AppFrame";

const NAV: NavItem[] = [
  { href: "/platform", key: "schools", exact: true },
  { href: "/platform/onboard", key: "onboard" },
  { href: "/platform/referrals", key: "referrals" },
  { href: "/platform/support", key: "support" },
  { href: "/platform/payment-issues", key: "paymentIssues" },
  { href: "/platform/audit-log", key: "auditLog" },
  { href: "/platform/tips", key: "tips" },
];

export default function PlatformLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppFrame nav={NAV} area="platform">
      {children}
    </AppFrame>
  );
}
