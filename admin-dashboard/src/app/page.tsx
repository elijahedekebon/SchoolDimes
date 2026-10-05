import { redirect } from "next/navigation";

// The proxy sends signed-in users to their home; this is the fallback.
export default function Home() {
  redirect("/login");
}
