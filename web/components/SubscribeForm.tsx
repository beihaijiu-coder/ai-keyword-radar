"use client";

// 这个组件是首页顶部的邮件订阅框，提交后调用本项目自己的 API。
import { FormEvent, useState } from "react";

export function SubscribeForm() {
  const [email, setEmail] = useState("");
  const [statusText, setStatusText] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsSubmitting(true);
    setStatusText("");

    try {
      const response = await fetch("/api/subscribe", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const payload = (await response.json()) as { message?: string };
      setStatusText(payload.message || "Subscription saved.");
      if (response.ok) {
        setEmail("");
      }
    } catch {
      setStatusText("Subscription failed. Please try again.");
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <form className="subscribe-form" onSubmit={handleSubmit}>
      <input
        aria-label="Email address"
        type="email"
        value={email}
        placeholder="you@example.com"
        onChange={(event) => setEmail(event.target.value)}
        required
      />
      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Saving..." : "Subscribe"}
      </button>
      <p className="form-status" aria-live="polite">
        {statusText}
      </p>
    </form>
  );
}
