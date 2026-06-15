import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface SearchExplanation {
  match_type: string;
  fused_score: number;
  semantic_score: number;
  keyword_score?: number;
  reranker_score?: number;
  rationale: string;
}

export interface SearchResultChunk {
  chunk_id: string;
  asset_id: string;
  asset_name: string;
  modality: string;
  chunk_index: number;
  content: string;
  score: number;
  start_time?: number;
  end_time?: number;
  chunk_metadata: Record<string, any>;
  explanation?: SearchExplanation;
}

export interface SearchLatencyBreakdown {
  retrieval_ms: number;
  rerank_ms: number;
  total_ms: number;
}

export interface SearchResponse {
  query: string;
  mode: string;
  limit: number;
  results: SearchResultChunk[];
  latency: SearchLatencyBreakdown;
  strategy: string;
  synthesis?: string;
}

export interface AnalyticsDashboard {
  average_latency_ms: number;
  precision: number;
  recall: number;
  ndcg: number;
  mrr: number;
  total_searches: number;
  total_assets: number;
  total_chunks: number;
  recent_uploads: any[];
  top_queries: Array<{ query: string; count: number }>;
  performance_breakdowns: Array<{
    mode: string;
    avg_retrieval_ms: number;
    avg_rerank_ms: number;
    avg_total_ms: number;
    count: number;
  }>;
}

export interface UploadResponse {
  message: string;
  asset_id: string;
  asset_name: string;
  file_size: number;
  modality: string;
  storage_path: string;
  chunk_count?: number;
}

// 1. Search Hook
export function useSearch(params: {
  q: string;
  modality?: string;
  mode?: string;
  topK?: number;
  minScore?: number;
}) {
  return useQuery<SearchResponse>({
    queryKey: ['search', params],
    queryFn: async () => {
      if (!params.q) {
        return {
          query: '',
          mode: 'balanced',
          limit: 10,
          results: [],
          latency: { retrieval_ms: 0, rerank_ms: 0, total_ms: 0 },
          strategy: 'None',
        };
      }
      
      const url = new URL(`${API_BASE}/api/search`);
      url.searchParams.append('q', params.q);
      if (params.modality && params.modality !== 'ALL') {
        url.searchParams.append('modality', params.modality);
      }
      if (params.mode) {
        url.searchParams.append('mode', params.mode);
      }
      if (params.topK) {
        url.searchParams.append('top_k', params.topK.toString());
      }
      if (params.minScore !== undefined) {
        url.searchParams.append('minimum_score', params.minScore.toString());
      }

      const res = await fetch(url.toString());
      if (!res.ok) {
        throw new Error(`Search failed: ${res.statusText}`);
      }
      return res.json();
    },
    enabled: !!params.q,
    staleTime: 5000,
    retry: 1,
  });
}

// 2. Upload Hook
export function useUploadAsset() {
  const queryClient = useQueryClient();
  return useMutation<UploadResponse, Error, File>({
    mutationFn: async (file: File) => {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch(`${API_BASE}/api/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({}));
        throw new Error(errorData.detail || `Upload failed: ${res.statusText}`);
      }

      return res.json();
    },
    onSuccess: () => {
      // Invalidate dashboard and analytics cache so stats are updated
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}

// 3. Dashboard Analytics Hook
export function useAnalyticsDashboard() {
  return useQuery<AnalyticsDashboard>({
    queryKey: ['dashboard'],
    queryFn: async () => {
      const res = await fetch(`${API_BASE}/api/search/dashboard`);
      if (!res.ok) {
        throw new Error(`Failed to fetch dashboard metrics: ${res.statusText}`);
      }
      return res.json();
    },
    refetchInterval: 10000, // Poll every 10s for live telemetry updates
  });
}

// 4. Benchmark Trigger Hook
export function useTriggerBenchmark() {
  const queryClient = useQueryClient();
  return useMutation<any, Error, void>({
    mutationFn: async () => {
      const res = await fetch(`${API_BASE}/api/search/benchmark`, {
        method: 'POST',
      });
      if (!res.ok) {
        throw new Error(`Failed to trigger benchmark: ${res.statusText}`);
      }
      return res.json();
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
}
