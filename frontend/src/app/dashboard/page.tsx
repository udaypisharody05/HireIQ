import { currentUser } from "@clerk/nextjs/server";
import { AppHeader } from "@/components/AppHeader";
import { LeetCodeDashboard } from "@/components/LeetCodeDashboard";
import { UserSyncStatus } from "@/components/UserSyncStatus";

const sections = ["Practice", "Resume", "Interviews", "Applications"];

export default async function DashboardPage() {
  const user = await currentUser();
  const primaryEmail = user?.emailAddresses.find((email) => email.id === user.primaryEmailAddressId)?.emailAddress;
  const displayName = user?.fullName ?? user?.username ?? primaryEmail ?? "Signed-in user";

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
        <div className="mb-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="text-base font-semibold text-ink">Current user</h2>
          <dl className="mt-4 grid gap-4 text-sm sm:grid-cols-3">
            <div>
              <dt className="font-medium text-slate-500">Name</dt>
              <dd className="mt-1 text-slate-900">{displayName}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Email</dt>
              <dd className="mt-1 text-slate-900">{primaryEmail ?? "No primary email"}</dd>
            </div>
            <div>
              <dt className="font-medium text-slate-500">Clerk ID</dt>
              <dd className="mt-1 break-all text-slate-900">{user?.id}</dd>
            </div>
          </dl>
          <UserSyncStatus />
        </div>
        <LeetCodeDashboard />
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
