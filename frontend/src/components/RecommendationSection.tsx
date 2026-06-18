"use client";

import { useCallback, useEffect, useState } from "react";
import { useUser } from "@clerk/nextjs";

type RecommendedTopic = {
  topic: string;
  priority_score: number;
  reason: string;
};

type RecommendedProblem = {
  problem_id: string;
  title: string;
  slug: string;
  difficulty: string;
  topics: string[];
  recommendation_reason: string;
};

type RecommendationResponse = {
  recommended_topics: RecommendedTopic[];
  recommended_problems: RecommendedProblem[];
};

type RecommendationState = "loading" | "ready" | "unlinked" | "error";

type RecommendationSectionProps = {
  refreshKey: number;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function difficultyClass(difficulty: string) {
  if (difficulty === "Easy") {
    return "border-emerald-200 bg-emerald-50 text-emerald-700";
  }
  if (difficulty === "Medium") {
    return "border-amber-200 bg-amber-50 text-amber-700";
  }
  if (difficulty === "Hard") {
    return "border-red-200 bg-red-50 text-red-700";
  }
  return "border-slate-200 bg-slate-50 text-slate-700";
}

export function RecommendationSection({ refreshKey }: RecommendationSectionProps) {
  const { isLoaded, isSignedIn, user } = useUser();
  const [state, setState] = useState<RecommendationState>("loading");
  const [recommendations, setRecommendations] = useState<RecommendationResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  const loadRecommendations = useCallback(
    async (signal: AbortSignal) => {
      if (!user) {
        return;
      }

      setState("loading");
      setErrorMessage(null);

      const response = await fetch(`${apiUrl}/recommendations/${encodeURIComponent(user.id)}`, {
        signal,
      });

      if (response.status === 404) {
        setRecommendations(null);
        setState("unlinked");
        return;
      }

      if (!response.ok) {
        throw new Error(`Recommendations request failed with status ${response.status}`);
      }

      setRecommendations((await response.json()) as RecommendationResponse);
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
      setErrorMessage("You must be signed in to view recommendations.");
      return;
    }

    const controller = new AbortController();
    loadRecommendations(controller.signal).catch((error: unknown) => {
      if (error instanceof DOMException && error.name === "AbortError") {
        return;
      }
      setState("error");
      setErrorMessage(error instanceof Error ? error.message : "Unable to load recommendations.");
    });

    return () => controller.abort();
  }, [isLoaded, isSignedIn, user, refreshKey, retryKey, loadRecommendations]);

  if (state === "loading") {
    return (
      <section className="mb-6 space-y-4" aria-busy="true" aria-label="Loading practice recommendations">
        <div className="h-32 animate-pulse rounded-lg border border-slate-200 bg-white shadow-sm" />
        <div className="h-48 animate-pulse rounded-lg border border-slate-200 bg-white shadow-sm" />
      </section>
    );
  }

  if (state === "unlinked") {
    return (
      <section className="mb-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-xl font-semibold text-ink">Practice Recommendations</h2>
        <p className="mt-2 text-sm text-slate-600">
          Link and sync a LeetCode profile to generate practice recommendations.
        </p>
      </section>
    );
  }

  if (state === "error" || !recommendations) {
    return (
      <section className="mb-6 rounded-lg border border-red-200 bg-red-50 p-5 text-red-700 shadow-sm" role="alert">
        <h2 className="text-base font-semibold">Unable to load recommendations</h2>
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

  if (recommendations.recommended_topics.length === 0) {
    return (
      <section className="mb-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h2 className="text-xl font-semibold text-ink">Practice Recommendations</h2>
        <p className="mt-2 text-sm text-slate-600">
          There is not enough synced topic data yet. Solve accepted problems across at least three topics, then sync again.
        </p>
      </section>
    );
  }

  return (
    <section className="mb-6" aria-labelledby="recommendations-heading">
      <div className="mb-4">
        <h2 id="recommendations-heading" className="text-xl font-semibold text-ink">
          Practice Recommendations
        </h2>
        <p className="mt-1 text-sm text-slate-600">
          Deterministic suggestions based on your observed topic mastery and the local problem catalog.
        </p>
      </div>

      <div className="rounded-lg border border-indigo-200 bg-indigo-50 p-5 shadow-sm">
        <h3 className="text-base font-semibold text-indigo-900">Recommended topics</h3>
        <div className="mt-4 grid gap-3 md:grid-cols-3">
          {recommendations.recommended_topics.map((topic) => (
            <article key={topic.topic} className="rounded-md border border-indigo-200 bg-white p-4">
              <div className="flex items-start justify-between gap-3">
                <h4 className="font-semibold text-slate-900">{topic.topic}</h4>
                <span className="whitespace-nowrap rounded-full bg-indigo-100 px-2 py-1 text-xs font-semibold text-indigo-700">
                  Priority {topic.priority_score}
                </span>
              </div>
              <p className="mt-2 text-sm leading-5 text-slate-600">{topic.reason}</p>
            </article>
          ))}
        </div>
      </div>

      <div className="mt-4 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
        <h3 className="text-base font-semibold text-ink">Recommended problems</h3>
        {recommendations.recommended_problems.length === 0 ? (
          <div className="mt-4 rounded-md border border-slate-200 bg-slate-50 p-4">
            <p className="text-sm font-medium text-slate-800">
              No matching unsolved problems found in the local synced catalog yet.
            </p>
            <p className="mt-1 text-xs leading-5 text-slate-500">
              The current catalog is built from synced submissions and may have limited coverage.
            </p>
          </div>
        ) : (
          <div className="mt-4 grid gap-4 lg:grid-cols-2">
            {recommendations.recommended_problems.map((problem) => (
              <article key={problem.problem_id} className="rounded-lg border border-slate-200 p-4">
                <div className="flex items-start justify-between gap-4">
                  <a
                    className="font-semibold text-slate-900 hover:underline"
                    href={`https://leetcode.com/problems/${problem.slug}/`}
                    rel="noreferrer"
                    target="_blank"
                  >
                    {problem.title}
                  </a>
                  <span className={`rounded-full border px-2 py-1 text-xs font-semibold ${difficultyClass(problem.difficulty)}`}>
                    {problem.difficulty}
                  </span>
                </div>
                <div className="mt-3 flex flex-wrap gap-2">
                  {problem.topics.map((topic) => (
                    <span key={topic} className="rounded-full bg-slate-100 px-2 py-1 text-xs text-slate-600">
                      {topic}
                    </span>
                  ))}
                </div>
                <p className="mt-3 text-sm leading-6 text-slate-600">{problem.recommendation_reason}</p>
              </article>
            ))}
          </div>
        )}
      </div>

      <p className="mt-3 text-xs text-slate-500">
        Recommendations use recent accepted submissions and problems already present in HireIQ’s local synced catalog.
      </p>
    </section>
  );
}
