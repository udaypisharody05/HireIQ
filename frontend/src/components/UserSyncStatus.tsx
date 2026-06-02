"use client";

import { useEffect, useRef, useState } from "react";
import { useUser } from "@clerk/nextjs";

type SyncState = "loading" | "syncing" | "synced" | "error";

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function UserSyncStatus() {
  const { isLoaded, isSignedIn, user } = useUser();
  const hasSynced = useRef(false);
  const [syncState, setSyncState] = useState<SyncState>("loading");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoaded) {
      setSyncState("loading");
      return;
    }

    if (!isSignedIn || !user) {
      setSyncState("error");
      setErrorMessage("You must be signed in to sync your profile.");
      return;
    }

    if (hasSynced.current) {
      return;
    }

    hasSynced.current = true;
    setSyncState("syncing");
    setErrorMessage(null);

    const syncUser = async () => {
      const response = await fetch(`${apiUrl}/users/sync`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          clerk_user_id: user.id,
          email: user.primaryEmailAddress?.emailAddress ?? null,
          full_name: user.fullName ?? null,
        }),
      });

      if (!response.ok) {
        throw new Error(`User sync failed with status ${response.status}`);
      }

      setSyncState("synced");
    };

    syncUser().catch((error: unknown) => {
      setSyncState("error");
      setErrorMessage(error instanceof Error ? error.message : "User sync failed.");
    });
  }, [isLoaded, isSignedIn, user]);

  const statusText =
    syncState === "loading"
      ? "Preparing profile sync..."
      : syncState === "syncing"
        ? "Syncing profile..."
        : syncState === "synced"
          ? "Profile synced"
          : "Profile sync failed";

  return (
    <div
      className={`mt-4 rounded-md border px-4 py-3 text-sm ${
        syncState === "error"
          ? "border-red-200 bg-red-50 text-red-700"
          : "border-slate-200 bg-slate-50 text-slate-700"
      }`}
      role={syncState === "error" ? "alert" : "status"}
    >
      <p className="font-medium">{statusText}</p>
      {errorMessage ? <p className="mt-1 text-xs">{errorMessage}</p> : null}
    </div>
  );
}
