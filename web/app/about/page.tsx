// 这个文件是关于和方法论页面，说明数据来源、评分方法、更新时间和隐私政策。
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Methodology and Privacy | AI Tool New Terms Radar",
  description:
    "How AI Tool New Terms Radar finds rising AI terms, calculates opportunity scores, updates daily, and handles subscriber privacy.",
};

export default function AboutPage() {
  return (
    <main className="page-shell">
      <section className="method-layout">
        <article className="method-section">
          <p className="eyebrow">Methodology</p>
          <h1>How the radar finds rising AI terms.</h1>
          <p>
            The site scans public, free sources every day: Hacker News, Product Hunt, and selected vendor RSS feeds. It extracts candidate product names and AI-related noun phrases, then keeps terms that are warming up recently while staying mostly absent from the previous history window.
          </p>
        </article>

        <article className="method-section">
          <h2>Opportunity Score</h2>
          <p>The 0-100 score combines three signals:</p>
          <ul>
            <li>Velocity Score: recent mentions compared with historical mentions.</li>
            <li>Search Gap Score: Google Trends interest reversed, so lower search volume means a higher gap score.</li>
            <li>Source Diversity Score: how many independent sources mention the term.</li>
          </ul>
          <p>The default weights are 40% velocity, 40% search gap, and 20% source diversity.</p>
        </article>

        <article className="method-section">
          <h2>Update Schedule</h2>
          <p>
            Data refresh runs daily at UTC 23:00, which is 07:00 in Beijing, Hong Kong, and Singapore time. The weekly email digest runs every Monday at UTC 23:00, which arrives Tuesday morning in UTC+8.
          </p>
        </article>

        <article className="method-section">
          <h2>Privacy Policy</h2>
          <p>
            The site only stores email addresses that users voluntarily submit for the weekly digest. Subscriber records contain an email address and subscription time only. Every digest includes a one-click unsubscribe link, and unsubscribe requests remove the email from the subscriber list.
          </p>
          <p>
            The radar processes public product and technology trend information. It does not collect user accounts, payment data, behavioral profiles, or private personal data beyond the subscription email list.
          </p>
        </article>
      </section>
    </main>
  );
}
