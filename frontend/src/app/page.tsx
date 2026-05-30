import Link from "next/link";
import { AppHeader } from "@/components/AppHeader";

export default function Home() {
  return (
    <main className="min-h-screen bg-cloud">
      <AppHeader />
      <section className="mx-auto grid min-h-[calc(100vh-73px)] max-w-6xl content-center gap-12 px-6 py-16 lg:grid-cols-[1.1fr_0.9fr] lg:items-center">
        <div>
          <p className="mb-4 text-sm font-semibold uppercase tracking-[0.16em] text-mint">
            Placement intelligence
          </p>
          <h1 className="max-w-3xl text-5xl font-semibold tracking-tight text-ink sm:text-6xl">
            HireIQ
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-8 text-slate-700">
            A focused workspace for placement preparation, resume readiness, coding progress, and interview practice.
          </p>
          <div className="mt-8 flex flex-wrap gap-3">
            <Link href="/dashboard" className="rounded-md bg-ink px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800">
              Open dashboard
            </Link>
            <Link href="/login" className="rounded-md border border-slate-300 bg-white px-5 py-3 text-sm font-semibold text-ink hover:bg-slate-50">
              Login
            </Link>
          </div>
        </div>
        <div className="grid gap-4">
          {[
            ["Coding progress", "Track practice and readiness signals."],
            ["Resume analysis", "Prepare role-focused application material."],
            ["Mock interviews", "Build confidence through structured practice."],
          ].map(([title, description]) => (
            <div key={title} className="rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
              <h2 className="text-base font-semibold text-ink">{title}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">{description}</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
