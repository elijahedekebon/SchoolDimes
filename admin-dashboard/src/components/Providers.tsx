"use client";

import { colorsTuple, createTheme, MantineProvider } from "@mantine/core";
import { ModalsProvider } from "@mantine/modals";
import { Notifications } from "@mantine/notifications";
import { useRouter } from "next/navigation";
import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react";

import { setSessionExpiredHandler } from "@/lib/api";

type Branding = { primary_color?: string; logo_url?: string };
const BrandingContext = createContext<(b: Branding | null) => void>(() => undefined);
export const useSetBranding = () => useContext(BrandingContext);

const HEX = /^#[0-9a-fA-F]{6}$/;

export function Providers({ children }: { children: ReactNode }) {
  const router = useRouter();
  const [branding, setBranding] = useState<Branding | null>(null);

  useEffect(() => {
    setSessionExpiredHandler(() => router.push("/login?expired=1"));
  }, [router]);

  const theme = useMemo(() => {
    const color = branding?.primary_color && HEX.test(branding.primary_color) ? branding.primary_color : null;
    return createTheme({
      primaryColor: color ? "brand" : "teal",
      colors: color ? { brand: colorsTuple(color) } : {},
      defaultRadius: "md",
    });
  }, [branding]);

  return (
    <MantineProvider theme={theme} defaultColorScheme="light">
      <BrandingContext.Provider value={setBranding}>
        <ModalsProvider>
          <Notifications position="top-right" />
          {children}
        </ModalsProvider>
      </BrandingContext.Provider>
    </MantineProvider>
  );
}
