// 这个文件是首页榜单页，读取 latest.json 并展示每日更新的新词榜。
import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { SubscribeForm } from "../components/SubscribeForm";
import { formatUpdatedAt, readLatestTerms, sourceLabel } from "../lib/data";

export const revalidate = 3600;

export const metadata: Metadata = {
  title: "Rising AI Tool Terms Radar | Low-Competition AI Keywords",
  description:
    "Discover rising AI tool terms, emerging AI concepts, and low-competition AI keywords before search demand becomes crowded.",
};

export default function HomePage() {
  const latestTerms = readLatestTerms();

  return (
    <main className="page-shell">
      <section className="dashboard-top" aria-label="Radar overview">
        <div className="radar-summary">
          <div>
            <p className="eyebrow">Daily AI keyword radar</p>
            <h1>Rising AI terms with early search gaps.</h1>
            <p className="summary-copy">
              A compact daily leaderboard for SEO builders, indie hackers, and tool-site operators watching new AI concepts before search competition fills in.
            </p>
            <p className="last-updated">Last updated: {formatUpdatedAt(latestTerms.updated_at)} UTC</p>
          </div>
          <Image
            className="radar-image"
            src="/images/radar-signal.png"
            alt="Abstract radar rings for emerging AI terms"
            width={440}
            height={440}
            priority
          />
        </div>

        <aside className="subscribe-panel" aria-label="Weekly email subscription">
          <h2>Weekly brief</h2>
          <p>Get the highest-opportunity terms once a week. Every email includes one-click unsubscribe.</p>
          <SubscribeForm />
        </aside>
      </section>

      <div className="ad-slot" aria-hidden="true" />

      <section className="terms-section" aria-label="Latest rising AI terms">
        <div className="section-header">
          <div>
            <h2>Latest leaderboard</h2>
            <p>Ranked by velocity, search gap, and source diversity.</p>
          </div>
        </div>

        {latestTerms.terms.length > 0 ? (
          <div className="terms-list">
            {latestTerms.terms.map((term) => (
              <article className="term-row" key={term.slug}>
                <div>
                  <Link className="term-name" href={`/term/${term.slug}`}>
                    {term.term}
                  </Link>
                  <div className="source-tags" aria-label="Sources">
                    {term.sources.map((source) => (
                      <span className="source-tag" key={source}>
                        {sourceLabel(source)}
                      </span>
                    ))}
                  </div>
                </div>
                <p className="trend-note">{term.trend_note}</p>
                <div className="score-cell" aria-label={`Opportunity score ${term.opportunity_score}`}>
                  <span className="score-number">{term.opportunity_score}</span>
                  <div className="score-bar">
                    <span style={{ width: `${term.opportunity_score}%` }} />
                  </div>
                </div>
              </article>
            ))}
          </div>
        ) : (
          <p className="empty-state">No qualifying rising terms were found in the latest run.</p>
        )}
      </section>
    </main>
  );
}
