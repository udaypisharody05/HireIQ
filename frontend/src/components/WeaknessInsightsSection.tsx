"use client";

import { useCallback, useEffect, useState } from "react";
import { useUser } from "@clerk/nextjs";

type StrongTopic = {
  topic: string;
  solved_count: number;
  mastery_score: number;
};

type WeakTopic = StrongTopic & {
  reason: string;
};

type FocusTopic = {
  topic: string;
  reason: string;
};

type WeaknessAnalytics = {
  strongest_topics: StrongTopic[];
  weakest_topics: WeakTopic[];
  recommended_focus_topics: FocusTopic[];
};

type InsightsState = "loading" | "ready" | "unlinked" | "error";

type WeaknessInsightsSectionProps = {
  refreshKey: number;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function MasteryBar({ score }: { score: number }) {
  return (
    <div className="mt-2">
      <div className="mb-1 flex items-center justify-between text-xs text-slate-500">
        <span>Mastery</span>
        <span>{score}/100</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
        <div className="h-full rounded-full bg-indigo-500" style={{ width: `${score}%` }} />
      </div>
    </div>
  );
}

export function WeaknessInsightsSection({ refreshKey }: WeaknessInsightsSectionProps) {
  const { isLoaded, isSignedIn, user } = useUser();
  const [state, setState] = useState<InsightsState>("loading");
  const [insights, setInsights] = useState<WeaknessAnalytics | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  const loadInsights = useCallback(
    async (signal: AbortSignal) => {
      if (!user) {
        return;
      }

      setState("loading");
      setErrorMessage(null);

      const response = await fetch(`${apiUrl}/analytics/weaknesses/${encodeURIComponent(user.id)}`, {
        signal,
      });

      if (response.status === 404) {
        setInsights(null);
        setState("unlinked");
        return;
      }

      if (!response.ok) {
        throw new Error(`Weakness insights request failed with status ${response.status}`);
      }

      setInsights((await response.json()) as WeaknessAnalytics);
      setState("ready");
    },
    [user],
  );

  useEffect(() => {
    if (!isLoaded) {
      setState("loading");
      return;
    }

    if (!isSignedIn || !user) {
      setState("error");
      setErrorMessage("You must be signed in to view weakness insights.");
      return;
    }

    const controller = new AbortController();
    loadInsights(controller.signal).catch((error: unknown) => {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      setState("error");
      setErrorMessage(error instanceof Error ? error.message : "Unable to load weakness insights.");
    });

    return () => controller.abort();
  }, [isLoaded, isSignedIn, user, refreshKey, retryKey, loadInsights]);

  if (state === "loading") {
    return (
      <section className="mb-6" aria-busy="true" aria-label="Loading weakness insights">
        <div className="h-56 animate-pulse rounded-lg border border-slate-200 bg-white shadow-sm" />
      </section>
    );
  }

  if (state === "unlinked") {
    return (
      <section className="mb-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-xl font-semibold text-ink">Weakness Insights</h2>
        <p className="mt-2 text-sm text-slate-600">
          Link and sync a LeetCode profile to identify your strongest and weakest topics.
        </p>
      </section>
    );
  }

  if (state === "error" || !insights) {
    return (
      <section className="mb-6 rounded-lg border border-red-200 bg-red-50 p-5 text-red-700 shadow-sm" role="alert">
        <h2 className="text-base font-semibold">Unable to load weakness insights</h2>
        <p className="mt-2 text-sm">{errorMessage ?? "An unexpected error occurred."}</p>
        <button
          className="mt-4 rounded-md border border-red-300 bg-white px-3 py-2 text-sm font-semibold hover:bg-red-100"
          onClick={() => setRetryKey((value) => value + 1)}
          type="button"
        >
          Retry
        </button>
      </section>
    );
  }

  const hasEnoughData =
    insights.strongest_topics.length > 0 ||
    insights.weakest_topics.length > 0 ||
    insights.recommended_focus_topics.length > 0;

  if (!hasEnoughData) {
    return (
      <section className="mb-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-xl font-semibold text-ink">Weakness Insights</h2>
        <p className="mt-2 text-sm text-slate-600">
          There is not enough synced topic data yet. Solve accepted problems across at least three topics, then sync again.
        </p>
        <p className="mt-3 text-xs text-slate-500">
          Insights use recent accepted submissions stored by HireIQ, not your complete LeetCode history.
        </p>
      </section>
    );
  }

  return (
    <section className="mb-6" aria-labelledby="weakness-insights-heading">
      <div className="mb-4">
        <h2 id="weakness-insights-heading" className="text-xl font-semibold text-ink">
          Weakness Insights
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          Topic mastery based on distinct accepted problems in your recent synced data.
        </p>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-emerald-200 bg-white p-5 shadow-sm">
          <h3 className="text-base font-semibold text-emerald-800">Strongest topics</h3>
          <div className="mt-4 space-y-4">
            {insights.strongest_topics.map((topic) => (
              <div key={topic.topic}>
                <div className="flex items-center justify-between gap-4">
                  <span className="font-medium text-slate-900">{topic.topic}</span>
                  <span className="text-sm text-slate-500">{topic.solved_count} solved</span>
                </div>
                <MasteryBar score={topic.mastery_score} />
              </div>
            ))}
          </div>
        </div>

        <div className="rounded-lg border border-amber-200 bg-white p-5 shadow-sm">
          <h3 className="text-base font-semibold text-amber-800">Weakest topics</h3>
          {insights.weakest_topics.length === 0 ? (
            <p className="mt-4 text-sm text-slate-600">
              No weak topics were detected in your current synced data.
            </p>
          ) : (
            <div className="mt-4 space-y-4">
              {insights.weakest_topics.map((topic) => (
                <div key={topic.topic}>
                  <div className="flex items-center justify-between gap-4">
                    <span className="font-medium text-slate-900">{topic.topic}</span>
                    <span className="text-sm text-slate-500">{topic.solved_count} solved</span>
                  </div>
                  <MasteryBar score={topic.mastery_score} />
                  <p className="mt-2 text-xs leading-5 text-slate-600">{topic.reason}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-indigo-200 bg-indigo-50 p-5 shadow-sm">
        <h3 className="text-base font-semibold text-indigo-900">Recommended focus</h3>
        {insights.recommended_focus_topics.length === 0 ? (
          <p className="mt-2 text-sm text-indigo-800">
            Keep broadening your practice across the topics already represented in your synced data.
          </p>
        ) : (
          <ul className="mt-3 grid gap-3 md:grid-cols-3">
            {insights.recommended_focus_topics.map((topic) => (
              <li key={topic.topic} className="rounded-md border border-indigo-200 bg-white p-4">
                <p className="font-medium text-slate-900">{topic.topic}</p>
                <p className="mt-1 text-sm leading-5 text-slate-600">{topic.reason}</p>
              </li>
            ))}
          </ul>
        )}
      </div>

      <p className="mt-3 text-xs text-slate-500">
        These insights reflect recent accepted submissions synced to HireIQ, not your complete LeetCode history.
      </p>
    </section>
  );
}
