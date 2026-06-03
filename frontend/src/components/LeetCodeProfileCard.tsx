"use client";

import { FormEvent, useEffect, useState } from "react";
import { useUser } from "@clerk/nextjs";

type ProfileState = "loading" | "idle" | "saving" | "saved" | "error";

type LeetCodeProfile = {
  username: string;
};

const apiUrl = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export function LeetCodeProfileCard() {
  const { isLoaded, isSignedIn, user } = useUser();
  const [profileState, setProfileState] = useState<ProfileState>("loading");
  const [username, setUsername] = useState("");
  const [linkedUsername, setLinkedUsername] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!isLoaded) {
      setProfileState("loading");
      return;
    }

    if (!isSignedIn || !user) {
      setProfileState("error");
      setMessage("You must be signed in to link a LeetCode profile.");
      return;
    }

    const loadProfile = async () => {
      setProfileState("loading");
      setMessage(null);

      const response = await fetch(`${apiUrl}/leetcode/profile/${encodeURIComponent(user.id)}`);

      if (response.status === 404) {
        setLinkedUsername(null);
        setUsername("");
        setProfileState("idle");
        return;
      }

      if (!response.ok) {
        throw new Error(`Profile lookup failed with status ${response.status}`);
      }

      const profile = (await response.json()) as LeetCodeProfile;
      setLinkedUsername(profile.username);
      setUsername(profile.username);
      setProfileState("idle");
    };

    loadProfile().catch((error: unknown) => {
      setProfileState("error");
      setMessage(error instanceof Error ? error.message : "Unable to load LeetCode profile.");
    });
  }, [isLoaded, isSignedIn, user]);

  const saveProfile = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    if (!user) {
      setProfileState("error");
      setMessage("You must be signed in to link a LeetCode profile.");
      return;
    }

    const trimmedUsername = username.trim();
    if (!trimmedUsername) {
      setProfileState("error");
      setMessage("Enter a LeetCode username before saving.");
      return;
    }

    setProfileState("saving");
    setMessage(null);

    try {
      const response = await fetch(`${apiUrl}/leetcode/profile`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          clerk_user_id: user.id,
          leetcode_username: trimmedUsername,
        }),
      });

      if (!response.ok) {
        throw new Error(`Profile save failed with status ${response.status}`);
      }

      const profile = (await response.json()) as LeetCodeProfile;
      setLinkedUsername(profile.username);
      setUsername(profile.username);
      setProfileState("saved");
      setMessage("LeetCode profile saved.");
    } catch (error: unknown) {
      setProfileState("error");
      setMessage(error instanceof Error ? error.message : "Unable to save LeetCode profile.");
    }
  };

  const isBusy = profileState === "loading" || profileState === "saving";
  const statusClass =
    profileState === "error"
      ? "border-red-200 bg-red-50 text-red-700"
      : profileState === "saved"
        ? "border-emerald-200 bg-emerald-50 text-emerald-700"
        : "border-slate-200 bg-slate-50 text-slate-700";

  return (
    <section className="mb-6 rounded-lg border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-1 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h2 className="text-base font-semibold text-ink">LeetCode Profile</h2>
          <p className="mt-1 text-sm text-slate-600">
            {linkedUsername ? (
              <>
                Linked username: <span className="font-medium text-slate-900">{linkedUsername}</span>
              </>
            ) : (
              "No LeetCode profile linked yet."
            )}
          </p>
        </div>
        {isBusy ? <span className="text-sm text-slate-500">{profileState === "saving" ? "Saving..." : "Loading..."}</span> : null}
      </div>

      <form className="mt-4 flex flex-col gap-3 sm:flex-row" onSubmit={saveProfile}>
        <label className="flex-1">
          <span className="sr-only">LeetCode username</span>
          <input
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm text-slate-900 outline-none focus:border-ink focus:ring-2 focus:ring-slate-200"
            disabled={isBusy || !isSignedIn}
            onChange={(event) => setUsername(event.target.value)}
            placeholder="LeetCode username"
            type="text"
            value={username}
          />
        </label>
        <button
          className="rounded-md bg-ink px-4 py-2 text-sm font-semibold text-white hover:bg-slate-800 disabled:cursor-not-allowed disabled:bg-slate-400"
          disabled={isBusy || !isSignedIn}
          type="submit"
        >
          Save
        </button>
      </form>

      {message || profileState === "loading" ? (
        <div className={`mt-4 rounded-md border px-4 py-3 text-sm ${statusClass}`} role={profileState === "error" ? "alert" : "status"}>
          {message ?? "Loading LeetCode profile..."}
        </div>
      ) : null}
    </section>
  );
}
