import { SignIn } from "@clerk/nextjs";
import { AppHeader } from "@/components/AppHeader";

export default function SignInPage() {
  return (
    <main className="min-h-screen bg-cloud">
      <AppHeader />
      <section className="mx-auto flex min-h-[calc(100vh-73px)] max-w-md items-center justify-center px-6 py-16">
        <SignIn />
      </section>
    </main>
  );
}
