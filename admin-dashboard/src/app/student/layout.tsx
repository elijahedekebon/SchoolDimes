import { AppFrame } from "@/components/AppFrame";

export default function StudentLayout({ children }: { children: React.ReactNode }) {
  return (
    <AppFrame nav={[{ href: "/student", key: "myPortal", exact: true }]} area="student">
      {children}
    </AppFrame>
  );
}
