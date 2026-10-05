"use client";

import { createTheme, type MantineColorsTuple, MantineProvider } from "@mantine/core";
import { ModalsProvider } from "@mantine/modals";
import { Notifications } from "@mantine/notifications";
import { useRouter } from "next/navigation";
import { createContext, type ReactNode, useContext, useEffect, useMemo, useState } from "react";

import { setSessionExpiredHandler } from "@/lib/api";

type Branding = { primary_color?: string; logo_url?: string };
const BrandingContext = createContext<(b: Branding | null) => void>(() => undefined);
export const useSetBranding = () => useContext(BrandingContext);

const HEX = /^#[0-9a-fA-F]{6}$/;

/** 10 shades (light -> dark) around the school's brand colour at index 6. */
export function brandShades(hex: string): MantineColorsTuple {
  const n = parseInt(hex.slice(1), 16);
  const rgb = [(n >> 16) & 255, (n >> 8) & 255, n & 255];
  const mix = (target: number, w: number) =>
    "#" + rgb.map((c) => Math.round(c + (target - c) * w).toString(16).padStart(2, "0")).join("");
  return [mix(255, 0.92), mix(255, 0.8), mix(255, 0.62), mix(255, 0.45), mix(255, 0.28), mix(255, 0.12), hex, mix(0, 0.12), mix(0, 0.24), mix(0, 0.36)] as unknown as MantineColorsTuple;
}

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
      colors: color ? { brand: brandShades(color) } : {},
      primaryShade: 6,
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
