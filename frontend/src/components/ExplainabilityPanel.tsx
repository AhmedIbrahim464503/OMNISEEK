'use client';

import React from 'react';
import { SearchExplanation } from '@/lib/api';
import { Sparkles, Brain, Cpu, Database, ChevronRight } from 'lucide-react';

interface Props {
  explanation?: SearchExplanation;
  score: number;
}

export default function ExplainabilityPanel({ explanation, score }: Props) {
  if (!explanation) {
    return (
      <div className="p-4 bg-secondary/35 rounded-lg border border-border text-center text-xs text-muted-foreground">
        No semantic query metrics logged for this chunk.
      </div>
    );
  }

  const { match_type, fused_score, semantic_score, keyword_score, reranker_score, rationale } = explanation;

  const percentFormat = (val?: number) => {
    if (val === undefined) return 'N/A';
    return `${(val * 100).toFixed(1)}%`;
  };

  return (
    <div className="bg-card border border-border rounded-xl p-5 shadow-sm space-y-5">
      {/* Panel Header */}
      <div className="flex items-center gap-2 border-b border-border pb-3">
        <Brain className="w-4 h-4 text-primary" />
        <h4 className="font-bold text-sm">Explainability Telemetry</h4>
      </div>

      {/* Rationale Text */}
      <div className="p-3.5 bg-secondary/50 rounded-lg border border-border text-xs leading-relaxed text-muted-foreground italic">
        &ldquo;{rationale || 'Match found through lexical index and semantic query mapping.'}&rdquo;
      </div>

      {/* Score Grid Metric Rows */}
      <div className="space-y-3">
        {/* Match Type Badge */}
        <div className="flex items-center justify-between text-xs">
          <span className="text-muted-foreground">Retrieval Match Type</span>
          <span className="px-2 py-0.5 bg-primary/10 text-primary rounded font-bold uppercase tracking-wider text-[10px]">
            {match_type || 'Semantic Vector'}
          </span>
        </div>

        {/* Fused Score */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs font-semibold">
            <span className="flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-indigo-500" /> Fused Match Strength
            </span>
            <span>{percentFormat(score)}</span>
          </div>
          <div className="w-full bg-secondary h-1.5 rounded-full overflow-hidden">
            <div 
              className="bg-indigo-500 h-1.5 rounded-full" 
              style={{ width: `${(score * 100).toFixed(0)}%` }}
            />
          </div>
        </div>

        {/* Semantic Score */}
        <div className="space-y-1.5">
          <div className="flex justify-between text-xs">
            <span className="flex items-center gap-1.5 text-muted-foreground">
              <Database className="w-3.5 h-3.5 text-blue-500" /> Semantic Distance Score
            </span>
            <span className="font-medium">{percentFormat(semantic_score)}</span>
          </div>
          <div className="w-full bg-secondary h-1.25 rounded-full overflow-hidden">
            <div 
              className="bg-blue-500 h-1.25 rounded-full" 
              style={{ width: `${(semantic_score * 100).toFixed(0)}%` }}
            />
          </div>
        </div>

        {/* Keyword Score (FTS) */}
        {keyword_score !== undefined && (
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <Cpu className="w-3.5 h-3.5 text-emerald-500" /> Lexical FTS Rank Score
              </span>
              <span className="font-medium">{percentFormat(keyword_score)}</span>
            </div>
            <div className="w-full bg-secondary h-1.25 rounded-full overflow-hidden">
              <div 
                className="bg-emerald-500 h-1.25 rounded-full" 
                style={{ width: `${(keyword_score * 100).toFixed(0)}%` }}
              />
            </div>
          </div>
        )}

        {/* Reranker Score */}
        {reranker_score !== undefined && (
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="flex items-center gap-1.5 text-muted-foreground">
                <Brain className="w-3.5 h-3.5 text-purple-500" /> Cross-Encoder Logit Score
              </span>
              <span className="font-medium">{percentFormat(reranker_score)}</span>
            </div>
            <div className="w-full bg-secondary h-1.25 rounded-full overflow-hidden">
              <div 
                className="bg-purple-500 h-1.25 rounded-full" 
                style={{ width: `${(reranker_score * 100).toFixed(0)}%` }}
              />
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
