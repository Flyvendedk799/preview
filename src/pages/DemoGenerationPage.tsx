/**
 * MyMetaView 6.0 — Demo generation page (API-wired)
 *
 * Integrates DemoGenerationExperience with batch API.
 * Optimized: two-tier polling, fast batch completion, resilient error handling.
 * Route: /demo-generation
 */

import React, { useCallback, useRef } from "react";
import {
  DemoGenerationExperience,
  type DemoItem,
} from "../components/DemoGenerationExperience";
import {
  submitBatchJob,
  getBatchJobStatus,
  getBatchPages,
  getBatchResults,
  DEFAULT_API_BASE,
  type BatchResultItem,
} from "../api/demo-batch-api";
import { getApiBaseUrl } from "../api/client";

function mapBackendStatusToItem(
  status: string
): "pending" | "generating" | "success" | "error" {
  switch (status) {
    case "completed":
      return "success";
    case "failed":
      return "error";
    case "running":
      return "generating";
    default:
      return "pending";
  }
}

function mapResultToDemoItem(
  r: { url: string; status: string; preview_url?: string | null; error?: string | null },
  index: number
): DemoItem {
  return {
    id: `${r.url}-${index}`,
    url: r.url,
    status: mapBackendStatusToItem(r.status),
    thumbnailUrl: r.preview_url ?? undefined,
    errorMessage: r.error ?? undefined,
  };
}

function mapBatchResultToDemoItem(r: BatchResultItem, index: number): DemoItem {
  // Prefer composited_preview_image_url (spec §5); backend maps it to preview_image_url
  const imageUrl = r.composited_preview_image_url ?? r.preview_image_url ?? r.screenshot_url;
  const itemStatus = r.error ? "failed" : imageUrl ? "completed" : "running";
  return {
    id: `${r.url}-${index}`,
    url: r.url,
    status: mapBackendStatusToItem(itemStatus),
    thumbnailUrl: imageUrl ?? undefined,
    errorMessage: r.error ?? undefined,
  };
}

/** Merge partial results with full URL list so all slots render during rapid parallel completion. */
function mergeResultsWithUrls(
  urls: string[],
  results: BatchResultItem[],
  jobId: string
): DemoItem[] {
  const byUrl = new Map<string, BatchResultItem>();
  for (const r of results) byUrl.set(r.url, r);

  return urls.map((url, i) => {
    const r = byUrl.get(url);
    if (r) {
      return mapBatchResultToDemoItem(r, i);
    }
    return {
      id: `${jobId}-${i}`,
      url,
      status: "generating" as const,
    };
  });
}

async function fetchFullItems(
  jobId: string,
  urls: string[],
  options: { apiBase?: string; apiKey?: string }
): Promise<DemoItem[]> {
  const { apiBase, apiKey } = options;

  // 6.0: Unified status+results in one poll (most efficient)
  try {
    const statusRes = await getBatchJobStatus(jobId, { apiBase, apiKey });
    if (statusRes.results && statusRes.results.length > 0) {
      return mergeResultsWithUrls(urls, statusRes.results, jobId);
    }
    // Job exists but no results yet — show all slots as generating
    if (statusRes.total != null && statusRes.total > 0) {
      return urls.map((url, i) => ({
        id: `${jobId}-${i}`,
        url,
        status: "generating" as const,
      }));
    }
  } catch {
    // Fall through to fallbacks
  }

  // Fallback: /pages for per-URL progress
  const pagesRes = await getBatchPages(jobId, { apiBase, apiKey });
  if (pagesRes?.pages && pagesRes.pages.length > 0) {
    const byUrl = new Map(
      pagesRes.pages.map((p) => [p.url, p])
    );
    return urls.map((url, i) => {
      const p = byUrl.get(url);
      if (p) {
        return mapResultToDemoItem(
          { url: p.url, status: p.status, preview_url: p.preview_url, error: p.error },
          i
        );
      }
      return { id: `${jobId}-${i}`, url, status: "generating" as const };
    });
  }

  // Fallback: /results (backend returns "results" array)
  const resultsRes = await getBatchResults(jobId, { apiBase, apiKey });
  const results = resultsRes.results ?? [];
  if (results.length > 0) {
    return mergeResultsWithUrls(urls, results, jobId);
  }

  return urls.map((url, i) => ({
    id: `${jobId}-${i}`,
    url,
    status: "generating" as const,
  }));
}

export interface DemoGenerationPageProps {
  apiBase?: string;
  apiKey?: string;
  qualityMode?: "fast" | "balanced" | "ultra" | "auto";
  pollIntervalMs?: number;
}

export const DemoGenerationPage: React.FC<DemoGenerationPageProps> = ({
  apiBase = getApiBaseUrl() || DEFAULT_API_BASE,
  apiKey,
  qualityMode = "balanced",
  pollIntervalMs = 800,
}) => {
  const jobIdRef = useRef<string | null>(null);
  const urlsRef = useRef<string[]>([]);

  const onCreateJob = useCallback(
    async (urls: string[]) => {
      urlsRef.current = urls;
      const res = await submitBatchJob(urls, {
        apiBase,
        apiKey,
        qualityMode,
      });
      jobIdRef.current = res.job_id;
    },
    [apiBase, apiKey, qualityMode]
  );

  const onPollJob = useCallback(async (): Promise<DemoItem[]> => {
    const jobId = jobIdRef.current;
    const urls = urlsRef.current;
    if (!jobId) return [];
    return fetchFullItems(jobId, urls, { apiBase, apiKey });
  }, [apiBase, apiKey]);

  return (
    <div className="min-h-screen bg-slate-950">
      <DemoGenerationExperience
        onCreateJob={onCreateJob}
        onPollJob={onPollJob}
        pollIntervalMs={pollIntervalMs}
      />
    </div>
  );
};

export default DemoGenerationPage;
