"use client";

import { useState } from "react";
import { AnalyticsSection } from "@/components/AnalyticsSection";
import { LeetCodeProfileCard } from "@/components/LeetCodeProfileCard";

export function LeetCodeDashboard() {
  const [analyticsRefreshKey, setAnalyticsRefreshKey] = useState(0);

  return (
    <>
      <LeetCodeProfileCard onSyncComplete={() => setAnalyticsRefreshKey((value) => value + 1)} />
      <AnalyticsSection refreshKey={analyticsRefreshKey} />
    </>
  );
}
