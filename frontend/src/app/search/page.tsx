'use client';

import React, { useState, useEffect } from 'react';
import { useSearch, SearchResultChunk } from '@/lib/api';
import { useSearchStore, SearchMode, ModalityType } from '@/store/useSearchStore';
import { VideoPlayer, AudioPlayer, DocumentViewer } from '@/components/MediaViewer';
import ExplainabilityPanel from '@/components/ExplainabilityPanel';
import { 
  Search, 
  Sliders, 
  Cpu, 
  Zap, 
  Clock, 
  Eye, 
  FileText, 
  Volume2, 
  Video, 
  HelpCircle,
  X,
  Play,
  Settings2,
  FileCode,
  CornerDownRight,
  Loader2
} from 'lucide-react';

export default function SearchPage() {
  // Global Store State
  const { 
    searchQuery, 
    setSearchQuery,
    searchMode, 
    setSearchMode,
    modality, 
    setModality,
    topK, 
    setTopK,
    minScore, 
    setMinScore,
    addHistoryItem
  } = useSearchStore();

  // Local state
  const [inputValue, setInputValue] = useState(searchQuery);
  const [triggerQuery, setTriggerQuery] = useState(searchQuery);
  const [selectedResult, setSelectedResult] = useState<SearchResultChunk | null>(null);
  const [showExplainChunk, setShowExplainChunk] = useState<SearchResultChunk | null>(null);
  const [showFilters, setShowFilters] = useState(false);

  // Search API fetch hook
  const { data: searchResponse, isLoading, error } = useSearch({
    q: triggerQuery,
    modality,
    mode: searchMode,
    topK,
    minScore
  });

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputValue.trim()) return;
    setTriggerQuery(inputValue);
    setSearchQuery(inputValue);
    setSelectedResult(null);
  };

  useEffect(() => {
    if (searchResponse && triggerQuery) {
      addHistoryItem({
        query: triggerQuery,
        mode: searchMode,
        modality: modality,
        resultsCount: searchResponse.results.length
      });
    }
  }, [searchResponse, triggerQuery, searchMode, modality, addHistoryItem]);

  const getModalityIcon = (mod: string) => {
    switch (mod.toUpperCase()) {
      case 'TEXT': return <FileText className="w-4 h-4 text-blue-500" />;
      case 'AUDIO': return <Volume2 className="w-4 h-4 text-amber-500" />;
      case 'VIDEO': return <Video className="w-4 h-4 text-purple-500" />;
      default: return <FileText className="w-4 h-4 text-muted-foreground" />;
    }
  };

  const getModeIcon = (mode: string) => {
    switch (mode) {
      case 'fast': return <Zap className="w-3.5 h-3.5 text-amber-500" />;
      case 'balanced': return <Sliders className="w-3.5 h-3.5 text-blue-500" />;
      case 'accurate': return <Cpu className="w-3.5 h-3.5 text-purple-500" />;
      default: return <Sliders className="w-3.5 h-3.5 text-muted-foreground" />;
    }
  };

  const formatTemporalMarker = (sec?: number) => {
    if (sec === undefined) return '';
    const m = Math.floor(sec / 60);
    const s = Math.floor(sec % 60);
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  return (
    <div className="p-6 max-w-7xl mx-auto w-full space-y-6">
      {/* Header */}
      <div className="border-b border-border pb-6 flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-extrabold tracking-tight">Search Center</h1>
          <p className="text-muted-foreground mt-1">
            Perform cross-modal semantic searches across text documents, audio recordings, and video frames.
          </p>
        </div>
      </div>

      {/* Main Search Controls Console */}
      <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
        <form onSubmit={handleSearchSubmit} className="flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3.5 top-3 w-5 h-5 text-muted-foreground" />
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Query system (e.g. 'discussion about coding pipelines' or 'milk'...)"
              className="w-full pl-11 pr-4 py-2.5 rounded-lg bg-secondary text-foreground border border-border focus:ring-2 focus:ring-primary focus:border-primary placeholder-muted-foreground text-sm font-medium transition"
            />
          </div>
          <button
            type="submit"
            disabled={isLoading || !inputValue.trim()}
            className="px-6 py-2.5 bg-primary text-primary-foreground font-semibold text-sm rounded-lg hover:bg-primary/90 transition shadow disabled:opacity-50 flex items-center gap-2"
          >
            {isLoading ? 'Searching...' : 'Execute'}
          </button>
          <button
            type="button"
            onClick={() => setShowFilters(!showFilters)}
            className={`p-2.5 border rounded-lg hover:bg-secondary transition-colors ${showFilters ? 'bg-secondary border-primary' : 'border-border bg-card'}`}
            title="Search Tuning Settings"
          >
            <Settings2 className="w-5 h-5 text-foreground" />
          </button>
        </form>

        {/* Dynamic Modality Tabs */}
        <div className="flex flex-wrap gap-2 border-b border-border pb-3">
          {(['ALL', 'TEXT', 'AUDIO', 'VIDEO'] as const).map((mod) => (
            <button
              key={mod}
              onClick={() => setModality(mod)}
              className={`
                px-4 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1.5 border transition
                ${modality === mod
                  ? 'bg-foreground text-background border-foreground'
                  : 'bg-card border-border text-muted-foreground hover:text-foreground hover:bg-secondary'
                }
              `}
            >
              {mod === 'ALL' && <Sliders className="w-3.5 h-3.5" />}
              {mod === 'TEXT' && <FileText className="w-3.5 h-3.5" />}
              {mod === 'AUDIO' && <Volume2 className="w-3.5 h-3.5" />}
              {mod === 'VIDEO' && <Video className="w-3.5 h-3.5" />}
              {mod}
            </button>
          ))}
        </div>

        {/* Expandable Advanced Tuning Filters */}
        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2 text-xs border-t border-border mt-3">
            {/* Search mode */}
            <div className="space-y-2">
              <label className="font-semibold text-muted-foreground flex items-center gap-1">
                Search Strategy Profile
              </label>
              <div className="grid grid-cols-3 gap-2">
                {(['fast', 'balanced', 'accurate'] as const).map((mode) => (
                  <button
                    key={mode}
                    type="button"
                    onClick={() => setSearchMode(mode)}
                    className={`
                      py-2 px-3 rounded-lg border text-center font-semibold capitalize flex flex-col items-center justify-center gap-1.5 transition
                      ${searchMode === mode
                        ? 'border-primary bg-primary/5 text-primary'
                        : 'border-border bg-card text-muted-foreground hover:text-foreground hover:bg-secondary'
                      }
                    `}
                  >
                    {getModeIcon(mode)}
                    <span>{mode}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Top K */}
            <div className="space-y-2">
              <div className="flex justify-between font-semibold">
                <span className="text-muted-foreground">Candidate Limit (Top-K)</span>
                <span>{topK} results</span>
              </div>
              <input
                type="range"
                min="5"
                max="50"
                step="5"
                value={topK}
                onChange={(e) => setTopK(parseInt(e.target.value))}
                className="w-full accent-primary bg-secondary h-1.5 rounded"
              />
              <span className="text-[10px] text-muted-foreground">Controls maximum retrieved documents returned.</span>
            </div>

            {/* Threshold */}
            <div className="space-y-2">
              <div className="flex justify-between font-semibold">
                <span className="text-muted-foreground">Minimum Similarity Score</span>
                <span>{(minScore * 100).toFixed(0)}%</span>
              </div>
              <input
                type="range"
                min="0.0"
                max="0.9"
                step="0.1"
                value={minScore}
                onChange={(e) => setMinScore(parseFloat(e.target.value))}
                className="w-full accent-primary bg-secondary h-1.5 rounded"
              />
              <span className="text-[10px] text-muted-foreground">Prunes noisy results failing to meet semantic alignment.</span>
            </div>
          </div>
        )}
      </div>

      {/* Latency and Query Stats Banner */}
      {searchResponse && triggerQuery && (
        <div className="flex flex-wrap items-center justify-between gap-4 p-4 bg-secondary/40 border border-border rounded-xl text-xs">
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-muted-foreground" />
            <span className="text-muted-foreground">Strategy:</span>
            <span className="font-semibold text-foreground">{searchResponse.strategy}</span>
            <span className="mx-1">•</span>
            <span className="text-muted-foreground">Results:</span>
            <span className="font-semibold text-foreground">{searchResponse.results.length} found</span>
          </div>
          
          <div className="flex items-center gap-4 text-muted-foreground">
            {searchResponse.latency.retrieval_ms > 0 && (
              <span>Retrieval: <strong className="text-foreground">{searchResponse.latency.retrieval_ms.toFixed(1)}ms</strong></span>
            )}
            {searchResponse.latency.rerank_ms > 0 && (
              <span>Rerank: <strong className="text-foreground">{searchResponse.latency.rerank_ms.toFixed(1)}ms</strong></span>
            )}
            <span>Total: <strong className="text-primary font-bold">{searchResponse.latency.total_ms.toFixed(1)}ms</strong></span>
          </div>
        </div>
      )}

      {/* Main Results area grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 items-start">
        {/* Results List */}
        <div className="lg:col-span-2 space-y-4">
          {isLoading ? (
            <div className="text-center py-20 bg-card border border-border rounded-xl flex flex-col items-center justify-center">
              <Loader2 className="w-8 h-8 text-primary animate-spin mb-3" />
              <p className="text-sm font-semibold text-muted-foreground">Executing multi-modal retrieval query...</p>
            </div>
          ) : error ? (
            <div className="p-6 text-center bg-card border border-destructive/20 rounded-xl">
              <X className="w-8 h-8 text-destructive mx-auto mb-2" />
              <p className="font-bold text-destructive">Search execution failed</p>
              <p className="text-xs text-muted-foreground mt-1">Please ensure the backend is connected and configured.</p>
            </div>
          ) : !triggerQuery ? (
            <div className="text-center py-24 bg-card border border-border rounded-xl text-muted-foreground flex flex-col items-center justify-center">
              <Search className="w-12 h-12 stroke-[1] mb-2 text-muted-foreground/60" />
              <p className="text-sm font-medium">Input a search query in the search bar above to begin.</p>
            </div>
          ) : searchResponse?.results.length === 0 ? (
            <div className="text-center py-24 bg-card border border-border rounded-xl text-muted-foreground flex flex-col items-center justify-center">
              <Sliders className="w-12 h-12 stroke-[1] mb-2 text-muted-foreground/60" />
              <p className="text-sm font-medium">No chunks matching the query were found.</p>
              <p className="text-xs text-muted-foreground/80 mt-1">Try lowering the similarity threshold or switching to Accurate mode.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {searchResponse?.results.map((result) => (
                <div
                  key={result.chunk_id}
                  className={`
                    p-5 bg-card border rounded-xl shadow-sm transition-all duration-200 flex flex-col space-y-4 hover:scale-[1.005] hover:shadow-md
                    ${selectedResult?.chunk_id === result.chunk_id ? 'ring-2 ring-primary border-primary bg-primary/2' : 'border-border'}
                  `}
                >
                  {/* Top: Metadata */}
                  <div className="flex items-center justify-between flex-wrap gap-2 text-xs">
                    <div className="flex items-center gap-2">
                      {getModalityIcon(result.modality)}
                      <span className="font-semibold text-foreground truncate max-w-[180px] sm:max-w-[280px]">
                        {result.asset_name}
                      </span>
                      {result.start_time !== undefined && (
                        <span className="bg-secondary text-muted-foreground px-2 py-0.5 rounded flex items-center gap-1 font-semibold text-[10px]">
                          <Clock className="w-3 h-3" />
                          {formatTemporalMarker(result.start_time)}
                          {result.end_time !== undefined && ` - ${formatTemporalMarker(result.end_time)}`}
                        </span>
                      )}
                    </div>
                    
                    <div className="flex items-center gap-2 shrink-0">
                      <span className="text-[10px] uppercase font-bold text-muted-foreground bg-secondary px-1.5 py-0.5 rounded">
                        {result.explanation?.match_type || 'Lexical'}
                      </span>
                      <span className="font-bold text-primary bg-primary/10 px-2 py-0.5 rounded text-xs">
                        {(result.score * 100).toFixed(0)}% Match
                      </span>
                    </div>
                  </div>

                  {/* Body text snippet */}
                  <div className="text-sm text-muted-foreground leading-relaxed">
                    &ldquo;{result.content}&rdquo;
                  </div>

                  {/* Footer actions */}
                  <div className="flex items-center justify-between border-t border-border/60 pt-3.5 text-xs">
                    <button
                      onClick={() => setShowExplainChunk(showExplainChunk?.chunk_id === result.chunk_id ? null : result)}
                      className="text-muted-foreground hover:text-foreground inline-flex items-center gap-1.5 font-semibold transition"
                    >
                      <Eye className="w-3.5 h-3.5" /> Explain Match
                    </button>
                    
                    <button
                      onClick={() => {
                        setSelectedResult(result);
                        // Clear scroll position and load window
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                      }}
                      className="inline-flex items-center gap-1.5 bg-primary text-primary-foreground font-semibold px-3.5 py-1.5 rounded-lg hover:bg-primary/90 transition shadow-sm"
                    >
                      <Play className="w-3.5 h-3.5" /> Launch Media
                    </button>
                  </div>

                  {/* Inline Explain details */}
                  {showExplainChunk?.chunk_id === result.chunk_id && (
                    <div className="pt-3 border-t border-border/40">
                      <ExplainabilityPanel explanation={result.explanation} score={result.score} />
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right Panel: Media playback and explainability */}
        <div className="space-y-6">
          {/* Active Media Player */}
          {selectedResult ? (
            <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-4">
              <div className="flex items-center justify-between border-b border-border pb-3">
                <h3 className="font-bold text-sm flex items-center gap-2">
                  <Play className="w-4 h-4 text-primary" /> Temporal Viewer
                </h3>
                <button
                  onClick={() => setSelectedResult(null)}
                  className="p-1 rounded hover:bg-secondary text-muted-foreground hover:text-foreground"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Render dynamic players based on modality */}
              {selectedResult.modality.toUpperCase() === 'VIDEO' && (
                <VideoPlayer
                  src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/storage/assets/${selectedResult.asset_id}/raw/${selectedResult.asset_name}`}
                  startTime={selectedResult.start_time}
                />
              )}

              {selectedResult.modality.toUpperCase() === 'AUDIO' && (
                <AudioPlayer
                  src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/storage/assets/${selectedResult.asset_id}/raw/${selectedResult.asset_name}`}
                  startTime={selectedResult.start_time}
                />
              )}

              {selectedResult.modality.toUpperCase() === 'TEXT' && (
                <DocumentViewer
                  assetName={selectedResult.asset_name}
                  content={selectedResult.chunk_metadata?.full_text || selectedResult.content}
                  highlightText={selectedResult.content}
                />
              )}
              
              <div className="text-xs text-muted-foreground leading-relaxed flex items-start gap-1">
                <CornerDownRight className="w-4.5 h-4.5 text-primary shrink-0 mt-0.5" />
                <span>
                  The player automatically initiated playback and mapped parameters to seek straight to the starting offset marker.
                </span>
              </div>
            </div>
          ) : (
            <div className="bg-card border border-border rounded-xl p-6 shadow-sm text-center text-muted-foreground py-12">
              <HelpCircle className="w-10 h-10 mx-auto stroke-[1] mb-2 text-muted-foreground/60" />
              <h4 className="font-bold text-sm text-foreground">Launch Preview</h4>
              <p className="text-xs mt-1">Select &ldquo;Launch Media&rdquo; on any result to load text highlights or timestamp offsets.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
