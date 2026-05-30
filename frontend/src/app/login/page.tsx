import { AppHeader } from "@/components/AppHeader";

export default function LoginPage() {
  return (
    <main className="min-h-screen bg-cloud">
      <AppHeader />
      <section className="mx-auto flex min-h-[calc(100vh-73px)] max-w-md flex-col justify-center px-6 py-16">
        <div className="rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
          <h1 className="text-2xl font-semibold tracking-tight text-ink">Login</h1>
          <p className="mt-3 text-sm leading-6 text-slate-600">
            Authentication will be connected in a future implementation phase.
          </p>
          <div className="mt-8 space-y-4">
            <div>
              <label className="text-sm font-medium text-slate-700" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                disabled
                className="mt-2 w-full rounded-md border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-500"
                placeholder="name@example.com"
              />
            </div>
            <div>
              <label className="text-sm font-medium text-slate-700" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                disabled
                type="password"
                className="mt-2 w-full rounded-md border border-slate-300 bg-slate-50 px-3 py-2 text-sm text-slate-500"
                placeholder="Not available yet"
              />
            </div>
            <button disabled className="w-full rounded-md bg-slate-300 px-4 py-2 text-sm font-semibold text-slate-600">
              Login unavailable
            </button>
          </div>
        </div>
      </section>
    </main>
  );
}
