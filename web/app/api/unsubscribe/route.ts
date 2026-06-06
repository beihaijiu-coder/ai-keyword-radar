// 这个文件处理一键退订链接，并立即从 data/subscribers.json 删除邮箱。
import { NextResponse } from "next/server";
import { normalizeEmail, readSubscribers, writeSubscribers } from "../../../lib/subscribers";

export const runtime = "nodejs";

export async function GET(request: Request) {
  const url = new URL(request.url);
  const email = normalizeEmail(url.searchParams.get("email") || "");

  if (!email) {
    return new Response("Missing email.", { status: 400 });
  }

  const subscribers = readSubscribers();
  const remainingSubscribers = subscribers.filter((subscriber) => subscriber.email !== email);
  writeSubscribers(remainingSubscribers);

  return new Response("You have been unsubscribed.", {
    status: 200,
    headers: { "Content-Type": "text/plain; charset=utf-8" },
  });
}

export async function POST(request: Request) {
  const payload = (await request.json().catch(() => null)) as { email?: string } | null;
  const email = normalizeEmail(payload?.email || "");

  if (!email) {
    return NextResponse.json({ message: "Missing email." }, { status: 400 });
  }

  const subscribers = readSubscribers();
  writeSubscribers(subscribers.filter((subscriber) => subscriber.email !== email));
  return NextResponse.json({ message: "Unsubscribed." });
}
