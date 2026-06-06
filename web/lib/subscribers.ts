// 这个文件负责读写 data/subscribers.json，订阅者只保存邮箱和订阅时间。
import fs from "node:fs";

const DEFAULT_SUBSCRIBERS_FILE = "../data/subscribers.json";

export type Subscriber = {
  email: string;
  subscribed_at: string;
};

export function readSubscribers(): Subscriber[] {
  const filePath = getSubscribersFilePath();
  if (!fs.existsSync(filePath)) {
    return [];
  }

  try {
    const payload = JSON.parse(fs.readFileSync(filePath, "utf-8")) as Subscriber[];
    return Array.isArray(payload) ? payload : [];
  } catch {
    return [];
  }
}

export function writeSubscribers(subscribers: Subscriber[]): void {
  const filePath = getSubscribersFilePath();
  fs.mkdirSync(getDirectoryName(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(subscribers, null, 2)}\n`, "utf-8");
}

export function normalizeEmail(email: string): string {
  return email.trim().toLowerCase();
}

export function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

function getSubscribersFilePath(): string {
  const configuredPath = process.env.SUBSCRIBERS_FILE;
  if (configuredPath) {
    return configuredPath;
  }
  return DEFAULT_SUBSCRIBERS_FILE;
}

function getDirectoryName(filePath: string): string {
  const normalizedPath = filePath.replace(/\\/g, "/");
  const lastSlashIndex = normalizedPath.lastIndexOf("/");
  if (lastSlashIndex === -1) {
    return ".";
  }
  return normalizedPath.slice(0, lastSlashIndex);
}
