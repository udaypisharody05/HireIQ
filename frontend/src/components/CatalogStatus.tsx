"use client";

import { useEffect, useState } from "react";

type CatalogStatusResponse = {
  catalog_size: number;
  active_topic_count: number;
  last_refreshed_at: string | null;
  sync_status: string;
  reported_total: number | null;
  skipped_count: number;
};

type CatalogState = "loading" | "ready" | "error";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function formatDate(value: string | null) {
  if (!value) {
    return "Not refreshed yet";
  }

  return new Intl.DateTimeFormat(undefined, {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function CatalogStatus() {
  const [state, setState] = useState<CatalogState>("loading");
  const [status, setStatus] = useState<CatalogStatusResponse | null>(null);
  const [retryKey, setRetryKey] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setState("loading");

    fetch(`${apiUrl}/catalog/status`, { signal: controller.signal })
      .then((response) => {
        if (!response.ok) {
          throw new Error(`Catalog status request failed with status ${response.status}`);
        }
        return response.json() as Promise<CatalogStatusResponse>;
      })
      .then((data) => {
        setStatus(data);
        setState("ready");
      })
      .catch((error: unknown) => {
        if (error instanceof DOMException && error.name === "AbortError") {
          return;
        }
        setState("error");
      });

    return () => controller.abort();
  }, [retryKey]);

  if (state === "loading") {
    return (
      <section className="mb-6" aria-busy="true" aria-label="Loading catalog status">
        <div className="h-28 animate-pulse rounded-lg border border-slate-200 bg-white shadow-sm" />
      </section>
    );
  }

  if (state === "error" || !status) {
    return (
      <section className="mb-6 rounded-lg border border-red-200 bg-red-50 p-5 text-red-700 shadow-sm" role="alert">
        <h2 className="text-base font-semibold">Problem catalog status unavailable</h2>
        <button
          className="mt-3 rounded-md border border-red-300 bg-white px-3 py-2 text-sm font-semibold hover:bg-red-100"
          onClick={() => setRetryKey((value) => value + 1)}
          type="button"
        >
          Retry
        </button>
      </section>
    );
  }

  return (
    <section className="mb-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-ink">Global Problem Catalog</h2>
          <p className="mt-1 text-sm text-slate-600">
            Free LeetCode problems available to the recommendation engine.
          </p>
        </div>
        <span className="text-xs font-medium uppercase tracking-wide text-slate-500">
          {status.sync_status.replaceAll("_", " ")}
        </span>
      </div>

      <dl className="mt-4 grid gap-4 text-sm sm:grid-cols-3">
        <div>
          <dt className="font-medium text-slate-500">Active problems</dt>
          <dd className="mt-1 text-2xl font-semibold text-slate-900">
            {status.catalog_size.toLocaleString()}
          </dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500">Topics covered</dt>
          <dd className="mt-1 text-2xl font-semibold text-slate-900">
            {status.active_topic_count.toLocaleString()}
          </dd>
        </div>
        <div>
          <dt className="font-medium text-slate-500">Last refreshed</dt>
          <dd className="mt-1 text-slate-900">{formatDate(status.last_refreshed_at)}</dd>
        </div>
      </dl>

      {status.sync_status === "failed" ? (
        <p className="mt-4 text-xs text-red-600">
          The last refresh failed. Existing catalog data remains available.
        </p>
      ) : null}
    </section>
  );
}
