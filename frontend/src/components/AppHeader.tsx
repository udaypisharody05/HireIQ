import Link from "next/link";

export function AppHeader() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4">
        <Link href="/" className="text-lg font-semibold tracking-tight text-ink">
          HireIQ
        </Link>
        <div className="flex items-center gap-3 text-sm font-medium text-slate-700">
          <Link href="/login" className="rounded-md px-3 py-2 hover:bg-slate-100">
            Login
          </Link>
          <Link href="/dashboard" className="rounded-md bg-ink px-3 py-2 text-white hover:bg-slate-800">
            Dashboard
          </Link>
        </div>
      </nav>
    </header>
  );
}
