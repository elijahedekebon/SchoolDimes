import type { NextRequest } from "next/server";

import { forward } from "@/lib/server/forward";

// Unauthenticated pass-through to /api/v1/public/* (contributor page).
const handler = (req: NextRequest) => forward(req, "/api/public");

export { handler as GET, handler as POST };
