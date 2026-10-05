import type { NextConfig } from "next";
import createNextIntlPlugin from "next-intl/plugin";

const withNextIntl = createNextIntlPlugin("./src/i18n/request.ts");

const nextConfig: NextConfig = {
  // The backend's Part 1 routes need their trailing slash; keep /api/proxy/x/
  // exactly as the client wrote it instead of redirecting to /api/proxy/x.
  skipTrailingSlashRedirect: true,
  experimental: {
    optimizePackageImports: ["@mantine/core", "@mantine/hooks", "@tabler/icons-react"],
  },
};

export default withNextIntl(nextConfig);
