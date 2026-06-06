// 这个文件负责读取仓库根目录 data 里的 JSON，供 Next.js 页面使用。
import fs from "node:fs";
import path from "node:path";

export type Term = {
  term: string;
  slug: string;
  first_seen: string;
  sources: string[];
  mention_count_recent: number;
  mention_count_history: number;
  velocity_score: number;
  search_gap_score: number;
  source_diversity_score: number;
  opportunity_score: number;
  trend_note: string;
  example_links: string[];
};

export type LatestTermsPayload = {
  updated_at: string;
  terms: Term[];
};

export function readLatestTerms(): LatestTermsPayload {
  return readJson<LatestTermsPayload>(path.join(getTermsDirectory(), "latest.json"), {
    updated_at: "",
    terms: [],
  });
}

export function readTerm(slug: string): Term | null {
  const safeSlug = slug.replace(/[^a-z0-9-]/g, "");
  const filePath = path.join(getTermsDirectory(), `${safeSlug}.json`);
  if (!fs.existsSync(filePath)) {
    return null;
  }
  return readJson<Term | null>(filePath, null);
}

export function readAllTermSlugs(): string[] {
  const termsDirectory = getTermsDirectory();
  if (!fs.existsSync(termsDirectory)) {
    return [];
  }

  return fs
    .readdirSync(termsDirectory)
    .filter((fileName) => fileName.endsWith(".json") && fileName !== "latest.json")
    .map((fileName) => fileName.replace(/\.json$/, ""));
}

export function formatUpdatedAt(value: string): string {
  if (!value) {
    return "Not generated yet";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return new Intl.DateTimeFormat("en", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(date);
}

export function sourceLabel(source: string): string {
  if (source === "hackernews") {
    return "HN";
  }
  if (source === "producthunt") {
    return "PH";
  }
  if (source === "rss") {
    return "RSS";
  }
  return source.toUpperCase();
}

function getTermsDirectory(): string {
  return path.join(getDataDirectory(), "terms");
}

function getDataDirectory(): string {
  const configuredPath = process.env.DATA_DIR;
  if (configuredPath && fs.existsSync(configuredPath)) {
    return configuredPath;
  }

  // 本地开发通常在 web 目录里运行 Next.js，所以 data 在上一级。
  const parentDataDirectory = path.join(process.cwd(), "..", "data");
  if (fs.existsSync(parentDataDirectory)) {
    return parentDataDirectory;
  }

  return path.join(process.cwd(), "data");
}

function readJson<T>(filePath: string, fallback: T): T {
  try {
    return JSON.parse(fs.readFileSync(filePath, "utf-8")) as T;
  } catch {
    return fallback;
  }
}
