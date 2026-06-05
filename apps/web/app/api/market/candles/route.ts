export const dynamic = "force-dynamic";

const serverApiUrl = process.env.API_URL ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const allowedIntervals = new Set(["1h", "4h", "1d"]);

export async function GET(request: Request) {
  const sourceUrl = new URL(request.url);
  const interval = sourceUrl.searchParams.get("interval") ?? "1h";
  const rawLimit = sourceUrl.searchParams.get("limit") ?? "250";
  const parsedLimit = Number.parseInt(rawLimit, 10);
  const safeLimit = Number.isFinite(parsedLimit) ? Math.min(Math.max(parsedLimit, 1), 500) : 250;
  const safeInterval = allowedIntervals.has(interval) ? interval : "1h";
  const upstreamUrl = new URL(`${serverApiUrl}/market/candles`);
  upstreamUrl.searchParams.set("interval", safeInterval);
  upstreamUrl.searchParams.set("limit", String(safeLimit));

  const response = await fetch(upstreamUrl, { cache: "no-store" });
  return new Response(response.body, {
    status: response.status,
    headers: {
      "Content-Type": response.headers.get("Content-Type") ?? "application/json",
      "Cache-Control": "no-store",
    },
  });
}
