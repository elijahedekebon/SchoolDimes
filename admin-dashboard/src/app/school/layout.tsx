import { AppFrame, type NavItem } from "@/components/AppFrame";

const NAV: NavItem[] = [
  { href: "/school", key: "overview", exact: true },
  { href: "/school/sales", key: "sales" },
  { href: "/school/reconciliation", key: "reconciliation" },
  { href: "/school/shortfalls", key: "shortfalls" },
  { href: "/school/analytics", key: "analytics" },
  { href: "/school/students", key: "students" },
  { href: "/school/guardians", key: "guardians" },
  { href: "/school/cards", key: "cards" },
  { href: "/school/devices", key: "devices" },
  { href: "/school/merchants", key: "merchants" },
  { href: "/school/products", key: "products" },
  { href: "/school/policy", key: "policy" },
  { href: "/school/staff", key: "staff" },
  { href: "/school/fees", key: "fees" },
  { href: "/school/attendance", key: "attendance" },
  { href: "/school/pooled-funds", key: "pooledFunds" },
  { href: "/school/disputes", key: "disputes" },
  { href: "/school/p2p-alerts", key: "p2pAlerts" },
  { href: "/school/privacy", key: "privacy" },
  { href: "/school/tips", key: "tips" },
  { href: "/school/payment-issues", key: "paymentIssues" },
];

export default function SchoolLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppFrame nav={NAV} area="school">
      {children}
    </AppFrame>
  );
}
