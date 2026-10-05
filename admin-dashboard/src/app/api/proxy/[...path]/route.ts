import type { NextRequest } from "next/server";

import { forward } from "@/lib/server/forward";

const handler = (req: NextRequest) => forward(req, "/api/proxy");

export { handler as DELETE, handler as GET, handler as PATCH, handler as POST, handler as PUT };
