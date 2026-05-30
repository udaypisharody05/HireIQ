import { AppHeader } from "@/components/AppHeader";

const sections = ["Practice", "Resume", "Interviews", "Applications"];

export default function DashboardPage() {
  return (
    <main className="min-h-screen bg-cloud">
      <AppHeader />
      <section className="mx-auto max-w-6xl px-6 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-semibold tracking-tight text-ink">Dashboard</h1>
          <p className="mt-2 text-sm text-slate-600">
            Core HireIQ modules will appear here as backend services are implemented.
          </p>
        </div>
        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          {sections.map((section) => (
            <div key={section} className="rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
              <h2 className="text-base font-semibold text-ink">{section}</h2>
              <p className="mt-2 text-sm leading-6 text-slate-600">Placeholder module</p>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
