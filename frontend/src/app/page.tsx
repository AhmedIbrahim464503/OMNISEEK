'use client';

import React from 'react';
import Link from 'next/link';
import { useAnalyticsDashboard, useTriggerBenchmark } from '@/lib/api';
import { useSearchStore } from '@/store/useSearchStore';
import { 
  Folder, 
  Database, 
  Search, 
  Zap, 
  ArrowUpRight, 
  Loader2, 
  Play, 
  Upload, 
  RefreshCw,
  FileText,
  Image as ImageIcon,
  Volume2,
  Video
} from 'lucide-react';

export default function DashboardPage() {
  const { data: metrics, isLoading, error, refetch } = useAnalyticsDashboard();
  const triggerBenchmark = useTriggerBenchmark();
  const recentAssets = useSearchStore((state) => state.recentAssets);
  const searchHistory = useSearchStore((state) => state.searchHistory);

  const getModalityIcon = (modality: string) => {
    switch (modality?.toUpperCase()) {
      case 'TEXT': return <FileText className="w-4 h-4 text-blue-500" />;
      case 'IMAGE': return <ImageIcon className="w-4 h-4 text-emerald-500" />;
      case 'AUDIO': return <Volume2 className="w-4 h-4 text-amber-500" />;
      case 'VIDEO': return <Video className="w-4 h-4 text-purple-500" />;
      default: return <FileText className="w-4 h-4 text-muted-foreground" />;
    }
  };

  const formatLatency = (ms: number | undefined) => {
    if (ms === undefined) return '0ms';
    return ms < 1000 ? `${ms.toFixed(0)}ms` : `${(ms / 1000).toFixed(2)}s`;
  };

  const runBenchmark = async () => {
    try {
      await triggerBenchmark.mutateAsync();
      alert('Search Benchmark run triggered and finalized successfully!');
    } catch (e: any) {
      alert(`Benchmark failed: ${e.message}`);
    }
  };

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[80vh] p-6 text-center">
        <div className="max-w-md p-6 bg-card border border-destructive/20 rounded-lg shadow">
          <h2 className="text-xl font-bold text-destructive mb-2">Backend Connectivity Error</h2>
          <p className="text-muted-foreground mb-4">
            Could not connect to the OmniSeek API server. Please ensure the backend container is running and healthy on port 8000.
          </p>
          <button 
            onClick={() => refetch()}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground font-medium rounded-md hover:bg-primary/90 transition"
          >
            <RefreshCw className="w-4 h-4" /> Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto w-full space-y-8">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 border-b border-border pb-6">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">System Overview</h1>
          <p className="text-muted-foreground mt-1">
            Real-time multi-modal vector search and ingestion pipeline telemetry.
          </p>
        </div>
        <div className="flex flex-wrap gap-3">
          <Link 
            href="/search"
            className="inline-flex items-center gap-2 px-4 py-2 border border-border bg-card hover:bg-secondary text-foreground text-sm font-medium rounded-md transition"
          >
            <Search className="w-4 h-4" /> Start Search
          </Link>
          <Link 
            href="/upload"
            className="inline-flex items-center gap-2 px-4 py-2 border border-border bg-card hover:bg-secondary text-foreground text-sm font-medium rounded-md transition"
          >
            <Upload className="w-4 h-4" /> Upload Asset
          </Link>
          <button
            disabled={triggerBenchmark.isPending}
            onClick={runBenchmark}
            className="inline-flex items-center gap-2 px-4 py-2 bg-primary hover:bg-primary/90 text-primary-foreground text-sm font-medium rounded-md transition disabled:opacity-50"
          >
            {triggerBenchmark.isPending ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Play className="w-4 h-4" />
            )}
            Run Benchmark
          </button>
        </div>
      </div>

      {/* KPI Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {/* Total Assets */}
        <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Total Uploaded Assets</span>
            <div className="p-2 rounded-lg bg-blue-500/10 text-blue-500">
              <Folder className="w-5 h-5" />
            </div>
          </div>
          <div>
            <h2 className="text-3xl font-bold tracking-tight">
              {isLoading ? <span className="animate-pulse">...</span> : metrics?.total_assets ?? 0}
            </h2>
            <p className="text-xs text-muted-foreground mt-1">Active files processed</p>
          </div>
        </div>

        {/* Total Chunks */}
        <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Total Vector Chunks</span>
            <div className="p-2 rounded-lg bg-emerald-500/10 text-emerald-500">
              <Database className="w-5 h-5" />
            </div>
          </div>
          <div>
            <h2 className="text-3xl font-bold tracking-tight">
              {isLoading ? <span className="animate-pulse">...</span> : metrics?.total_chunks ?? 0}
            </h2>
            <p className="text-xs text-muted-foreground mt-1">Multi-modal partitions</p>
          </div>
        </div>

        {/* Total Searches */}
        <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Total Engine Queries</span>
            <div className="p-2 rounded-lg bg-purple-500/10 text-purple-500">
              <Search className="w-5 h-5" />
            </div>
          </div>
          <div>
            <h2 className="text-3xl font-bold tracking-tight">
              {isLoading ? <span className="animate-pulse">...</span> : metrics?.total_searches ?? 0}
            </h2>
            <p className="text-xs text-muted-foreground mt-1">Full-text & vector matches</p>
          </div>
        </div>

        {/* Avg Latency */}
        <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <span className="text-sm font-medium text-muted-foreground">Average Latency</span>
            <div className="p-2 rounded-lg bg-amber-500/10 text-amber-500">
              <Zap className="w-5 h-5" />
            </div>
          </div>
          <div>
            <h2 className="text-3xl font-bold tracking-tight">
              {isLoading ? <span className="animate-pulse">...</span> : formatLatency(metrics?.average_latency_ms)}
            </h2>
            <p className="text-xs text-muted-foreground mt-1">End-to-end response time</p>
          </div>
        </div>
      </div>

      {/* Information Retrieval Quality Metrics Grid */}
      <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-4">
        <h3 className="font-bold text-lg">Evaluation Quality Metrics (IR Benchmarks)</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="p-4 bg-secondary/50 rounded-lg text-center">
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">NDCG</div>
            <div className="text-2xl font-bold mt-1 text-primary">
              {isLoading ? '...' : (metrics?.ndcg ?? 0).toFixed(4)}
            </div>
          </div>
          <div className="p-4 bg-secondary/50 rounded-lg text-center">
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">MRR (Reciprocal Rank)</div>
            <div className="text-2xl font-bold mt-1 text-primary">
              {isLoading ? '...' : (metrics?.mrr ?? 0).toFixed(4)}
            </div>
          </div>
          <div className="p-4 bg-secondary/50 rounded-lg text-center">
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Precision</div>
            <div className="text-2xl font-bold mt-1 text-primary">
              {isLoading ? '...' : (metrics?.precision ?? 0).toFixed(4)}
            </div>
          </div>
          <div className="p-4 bg-secondary/50 rounded-lg text-center">
            <div className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Recall</div>
            <div className="text-2xl font-bold mt-1 text-primary">
              {isLoading ? '...' : (metrics?.recall ?? 0).toFixed(4)}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity: Uploads vs Queries */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Uploads Panel */}
        <div className="p-6 bg-card border border-border rounded-xl shadow-sm flex flex-col h-[400px]">
          <div className="flex items-center justify-between border-b border-border pb-4 mb-4">
            <h3 className="font-bold text-lg">Recent Ingestion Queue</h3>
            <Link href="/upload" className="text-sm font-semibold text-primary hover:underline inline-flex items-center gap-1">
              Upload New <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="flex-1 overflow-y-auto space-y-4">
            {recentAssets.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <Folder className="w-12 h-12 stroke-[1] mb-2" />
                <p className="text-sm">No recent uploads registered</p>
              </div>
            ) : (
              <div className="divide-y divide-border">
                {recentAssets.map((asset) => (
                  <div key={asset.id} className="flex items-center justify-between py-3">
                    <div className="flex items-center gap-3 min-w-0">
                      <div className="p-2 bg-secondary rounded-lg shrink-0">
                        {getModalityIcon(asset.status === 'Completed' ? 'TEXT' : 'VIDEO')}
                      </div>
                      <div className="min-w-0">
                        <p className="font-medium text-sm truncate text-foreground">{asset.name}</p>
                        <p className="text-xs text-muted-foreground">
                          {new Date(asset.timestamp).toLocaleTimeString()}
                        </p>
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <span className={`inline-block px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        asset.status === 'Completed' 
                          ? 'bg-emerald-500/10 text-emerald-500' 
                          : asset.status === 'Failed' 
                            ? 'bg-red-500/10 text-red-500' 
                            : 'bg-amber-500/10 text-amber-500 animate-pulse'
                      }`}>
                        {asset.status}
                      </span>
                      {asset.chunkCount !== undefined && (
                        <p className="text-xs text-muted-foreground mt-1">{asset.chunkCount} chunks</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Search History Panel */}
        <div className="p-6 bg-card border border-border rounded-xl shadow-sm flex flex-col h-[400px]">
          <div className="flex items-center justify-between border-b border-border pb-4 mb-4">
            <h3 className="font-bold text-lg">Recent User Queries</h3>
            <Link href="/search" className="text-sm font-semibold text-primary hover:underline inline-flex items-center gap-1">
              Search Console <ArrowUpRight className="w-4 h-4" />
            </Link>
          </div>
          <div className="flex-1 overflow-y-auto space-y-4">
            {searchHistory.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full text-muted-foreground">
                <Search className="w-12 h-12 stroke-[1] mb-2" />
                <p className="text-sm">No recent queries logged</p>
              </div>
            ) : (
              <div className="divide-y divide-border">
                {searchHistory.slice(0, 5).map((history, idx) => (
                  <div key={idx} className="flex items-center justify-between py-3">
                    <div className="min-w-0">
                      <p className="font-medium text-sm text-foreground truncate">&ldquo;{history.query}&rdquo;</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] px-1.5 py-0.25 bg-secondary rounded uppercase font-semibold text-muted-foreground">
                          {history.mode}
                        </span>
                        <span className="text-[10px] text-muted-foreground">
                          {new Date(history.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-sm font-semibold">{history.resultsCount} hits</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
