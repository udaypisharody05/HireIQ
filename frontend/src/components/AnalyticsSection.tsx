"use client";

import { useCallback, useEffect, useState } from "react";
import { useUser } from "@clerk/nextjs";

type TopicStat = {
  topic: string;
  solved_count: number;
};

type RecentSubmission = {
  problem_title: string;
  problem_slug: string;
  difficulty: string;
  status: string;
  submitted_at: string;
};

type AnalyticsSummary = {
  total_solved: number;
  easy_solved: number;
  medium_solved: number;
  hard_solved: number;
  last_synced_at: string | null;
  sync_status: string;
  topic_stats: TopicStat[];
  recent_submissions: RecentSubmission[];
};

type AnalyticsState = "loading" | "ready" | "empty" | "error";

type AnalyticsSectionProps = {
  refreshKey: number;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function formatDate(value: string | null) {
  if (!value) {
    return "Never";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

function difficultyClass(difficulty: string) {
  if (difficulty === "Easy") {
    return "text-emerald-700";
  }
  if (difficulty === "Medium") {
    return "text-amber-700";
  }
  if (difficulty === "Hard") {
    return "text-red-700";
  }
  return "text-slate-700";
}

export function AnalyticsSection({ refreshKey }: AnalyticsSectionProps) {
  const { isLoaded, isSignedIn, user } = useUser();
  const [state, setState] = useState<AnalyticsState>("loading");
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  const loadAnalytics = useCallback(
    async (signal: AbortSignal) => {
      if (!user) {
        return;
      }

      setState("loading");
      setErrorMessage(null);

      const response = await fetch(`${apiUrl}/analytics/summary/${encodeURIComponent(user.id)}`, {
        signal,
      });

      if (response.status === 404) {
        setSummary(null);
        setState("empty");
        return;
      }

      if (!response.ok) {
        throw new Error(`Analytics request failed with status ${response.status}`);
      }

      const data = (await response.json()) as AnalyticsSummary;
      setSummary(data);
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
      setErrorMessage("You must be signed in to view analytics.");
      return;
    }

    const controller = new AbortController();
    loadAnalytics(controller.signal).catch((error: unknown) => {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      setState("error");
      setErrorMessage(error instanceof Error ? error.message : "Unable to load analytics.");
    });

    return () => controller.abort();
  }, [isLoaded, isSignedIn, user, refreshKey, retryKey, loadAnalytics]);

  if (state === "loading") {
    return (
      <section className="mb-6 space-y-4" aria-busy="true" aria-label="Loading LeetCode analytics">
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {[0, 1, 2, 3].map((item) => (
            <div key={item} className="h-24 animate-pulse rounded-lg border border-slate-200 bg-white shadow-sm" />
          ))}
        </div>
        <div className="h-48 animate-pulse rounded-lg border border-slate-200 bg-white shadow-sm" />
      </section>
    );
  }

  if (state === "empty") {
    return (
      <section className="mb-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-base font-semibold text-ink">LeetCode Analytics</h2>
        <p className="mt-2 text-sm text-slate-600">
          Link and sync a LeetCode profile to populate your analytics.
        </p>
      </section>
    );
  }

  if (state === "error" || !summary) {
    return (
      <section className="mb-6 rounded-lg border border-red-200 bg-red-50 p-5 text-red-700 shadow-sm" role="alert">
        <h2 className="text-base font-semibold">Unable to load LeetCode analytics</h2>
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

  const statCards = [
    { label: "Total solved", value: summary.total_solved, className: "text-ink" },
    { label: "Easy", value: summary.easy_solved, className: "text-emerald-700" },
    { label: "Medium", value: summary.medium_solved, className: "text-amber-700" },
    { label: "Hard", value: summary.hard_solved, className: "text-red-700" },
  ];
  const difficultyTotal = summary.easy_solved + summary.medium_solved + summary.hard_solved;
  const difficulties = [
    { label: "Easy", value: summary.easy_solved, barClass: "bg-emerald-500" },
    { label: "Medium", value: summary.medium_solved, barClass: "bg-amber-500" },
    { label: "Hard", value: summary.hard_solved, barClass: "bg-red-500" },
  ];

  return (
    <section className="mb-6" aria-labelledby="analytics-heading">
      <div className="mb-4 flex flex-col gap-1 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 id="analytics-heading" className="text-xl font-semibold text-ink">
            LeetCode Analytics
          </h2>
          <p className="mt-1 text-sm text-slate-600">
            Last synced: {formatDate(summary.last_synced_at)}
          </p>
        </div>
        <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
          Sync status: {summary.sync_status.replaceAll("_", " ")}
        </span>
      </div>

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {statCards.map((stat) => (
          <div key={stat.label} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
            <p className="text-sm font-medium text-slate-500">{stat.label}</p>
            <p className={`mt-2 text-3xl font-semibold ${stat.className}`}>{stat.value}</p>
          </div>
        ))}
      </div>

      <div className="mt-4 grid gap-4 lg:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-base font-semibold text-ink">Difficulty breakdown</h3>
          <div className="mt-5 space-y-4">
            {difficulties.map((difficulty) => {
              const percentage = difficultyTotal > 0 ? (difficulty.value / difficultyTotal) * 100 : 0;
              return (
                <div key={difficulty.label}>
                  <div className="mb-1 flex justify-between text-sm">
                    <span className="font-medium text-slate-700">{difficulty.label}</span>
                    <span className="text-slate-500">{difficulty.value}</span>
                  </div>
                  <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                    <div
                      className={`h-full rounded-full ${difficulty.barClass}`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h3 className="text-base font-semibold text-ink">Topics</h3>
          {summary.topic_stats.length === 0 ? (
            <p className="mt-4 text-sm text-slate-600">No synced topic data yet.</p>
          ) : (
            <div className="mt-4 max-h-64 overflow-auto">
              <table className="w-full text-left text-sm">
                <thead className="text-xs uppercase tracking-wide text-slate-500">
                  <tr>
                    <th className="pb-2 font-medium">Topic</th>
                    <th className="pb-2 text-right font-medium">Solved</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {summary.topic_stats.map((topic) => (
                    <tr key={topic.topic}>
                      <td className="py-2 text-slate-800">{topic.topic}</td>
                      <td className="py-2 text-right font-medium text-slate-900">{topic.solved_count}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-base font-semibold text-ink">Recent submissions</h3>
        {summary.recent_submissions.length === 0 ? (
          <p className="mt-4 text-sm text-slate-600">No synced submissions yet.</p>
        ) : (
          <div className="mt-4 overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-xs uppercase tracking-wide text-slate-500">
                <tr>
                  <th className="pb-3 font-medium">Problem</th>
                  <th className="pb-3 font-medium">Difficulty</th>
                  <th className="pb-3 font-medium">Status</th>
                  <th className="pb-3 text-right font-medium">Submitted</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {summary.recent_submissions.map((submission) => (
                  <tr key={`${submission.problem_slug}-${submission.submitted_at}`}>
                    <td className="py-3 pr-4">
                      <a
                        className="font-medium text-slate-900 hover:underline"
                        href={`https://leetcode.com/problems/${submission.problem_slug}/`}
                        rel="noreferrer"
                        target="_blank"
                      >
                        {submission.problem_title}
                      </a>
                    </td>
                    <td className={`py-3 pr-4 font-medium ${difficultyClass(submission.difficulty)}`}>
                      {submission.difficulty}
                    </td>
                    <td className="py-3 pr-4 text-slate-700">{submission.status}</td>
                    <td className="py-3 text-right text-slate-500">{formatDate(submission.submitted_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  );
}
