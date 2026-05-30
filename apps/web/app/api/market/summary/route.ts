export const dynamic = "force-dynamic";

const serverApiUrl = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export async function GET() {
  const response = await fetch(`${serverApiUrl}/market/summary`, { cache: "no-store" });
  return new Response(response.body, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json",
      "Cache-Control": "no-store",
    },
  });
}
