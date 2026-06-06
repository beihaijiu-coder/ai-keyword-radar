// 这个文件是新词详情页，每个 slug 一个独立 URL，用于承接长尾搜索流量。
import type { Metadata } from "next";
import Link from "next/link";
import { notFound } from "next/navigation";
import { readAllTermSlugs, readTerm, sourceLabel } from "../../../lib/data";

type TermPageProps = {
  params: Promise<{
    slug: string;
  }>;
};

export const revalidate = 3600;

export async function generateStaticParams() {
  return readAllTermSlugs().map((slug) => ({ slug }));
}

export async function generateMetadata({ params }: TermPageProps): Promise<Metadata> {
  const { slug } = await params;
  const term = readTerm(slug);
  if (!term) {
    return {
      title: "AI Term Not Found | AI Tool New Terms Radar",
    };
  }

  return {
    title: `${term.term} — Trending AI Term | AI Tool New Terms Radar`,
    description: `${term.term} has an opportunity score of ${term.opportunity_score}. Track its AI keyword velocity, search gap, and source diversity.`,
  };
}

export default async function TermPage({ params }: TermPageProps) {
  const { slug } = await params;
  const term = readTerm(slug);

  if (!term) {
    notFound();
  }

  return (
    <main className="page-shell">
      <section className="detail-grid">
        <article className="detail-main">
          <p className="eyebrow">Trending AI term</p>
          <h1>{term.term}</h1>
          <p className="summary-copy">{term.trend_note}</p>

          <ul className="meta-list">
            <li>
              <span>First seen</span>
              <strong>{term.first_seen}</strong>
            </li>
            <li>
              <span>Recent mentions</span>
              <strong>{term.mention_count_recent}</strong>
            </li>
            <li>
              <span>Historical mentions</span>
              <strong>{term.mention_count_history}</strong>
            </li>
            <li>
              <span>Sources</span>
              <strong>{term.sources.map(sourceLabel).join(", ")}</strong>
            </li>
          </ul>

          <h2>Example links</h2>
          {term.example_links.length > 0 ? (
            <ul className="links-list">
              {term.example_links.map((url) => (
                <li key={url}>
                  <a href={url} target="_blank" rel="noreferrer">
                    {url}
                  </a>
                </li>
              ))}
            </ul>
          ) : (
            <p className="trend-note">No example links were saved for this run.</p>
          )}

          <Link className="back-link" href="/">
            Back to radar
          </Link>
        </article>

        <aside className="score-stack" aria-label="Opportunity score breakdown">
          <ScoreLine label="Opportunity Score" value={term.opportunity_score} />
          <ScoreLine label="Velocity Score" value={term.velocity_score} />
          <ScoreLine label="Search Gap Score" value={term.search_gap_score} />
          <ScoreLine label="Source Diversity Score" value={term.source_diversity_score} />
        </aside>
      </section>
    </main>
  );
}

function ScoreLine({ label, value }: { label: string; value: number }) {
  return (
    <div className="score-line">
      <header>
        <span>{label}</span>
        <strong>{value}</strong>
      </header>
      <div className="score-bar">
        <span style={{ width: `${value}%` }} />
      </div>
    </div>
  );
}
