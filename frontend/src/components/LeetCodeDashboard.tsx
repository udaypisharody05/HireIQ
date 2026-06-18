"use client";

import { useState } from "react";
import { AnalyticsSection } from "@/components/AnalyticsSection";
import { CatalogStatus } from "@/components/CatalogStatus";
import { LeetCodeProfileCard } from "@/components/LeetCodeProfileCard";
import { RecommendationSection } from "@/components/RecommendationSection";
import { WeaknessInsightsSection } from "@/components/WeaknessInsightsSection";

export function LeetCodeDashboard() {
  const [analyticsRefreshKey, setAnalyticsRefreshKey] = useState(0);

  return (
    <>
      <LeetCodeProfileCard onSyncComplete={() => setAnalyticsRefreshKey((value) => value + 1)} />
      <AnalyticsSection refreshKey={analyticsRefreshKey} />
      <WeaknessInsightsSection refreshKey={analyticsRefreshKey} />
      <CatalogStatus />
      <RecommendationSection refreshKey={analyticsRefreshKey} />
    </>
  );
}
