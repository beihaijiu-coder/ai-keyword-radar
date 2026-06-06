// 这个文件处理邮件订阅请求，并把邮箱写入 data/subscribers.json。
import { NextResponse } from "next/server";
import { isValidEmail, normalizeEmail, readSubscribers, writeSubscribers } from "../../../lib/subscribers";

export const runtime = "nodejs";

export async function POST(request: Request) {
  const payload = (await request.json().catch(() => null)) as { email?: string } | null;
  const email = normalizeEmail(payload?.email || "");

  if (!isValidEmail(email)) {
    return NextResponse.json({ message: "Please enter a valid email address." }, { status: 400 });
  }

  const subscribers = readSubscribers();
  const alreadySubscribed = subscribers.some((subscriber) => subscriber.email === email);

  if (!alreadySubscribed) {
    subscribers.push({
      email,
      subscribed_at: new Date().toISOString(),
    });
    writeSubscribers(subscribers);
  }

  return NextResponse.json({ message: "Saved. You will receive one weekly brief." });
}
