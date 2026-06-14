'use client';

import React from 'react';
import { 
  Database, 
  Cpu, 
  Layers, 
  FileText, 
  Workflow,
  Sparkles,
  Info
} from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="p-6 max-w-4xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="border-b border-border pb-6">
        <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
          <Info className="w-8 h-8 text-primary" /> About OmniSeek
        </h1>
        <p className="text-muted-foreground mt-1">
          Explore the architectural layers, algorithms, and models powering the Multi-Modal Embedding & Retrieval System.
        </p>
      </div>

      <div className="space-y-8 text-sm leading-relaxed text-muted-foreground">
        
        {/* Core Systems flow diagram block */}
        <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-4">
          <h3 className="font-bold text-base text-foreground flex items-center gap-2 border-b border-border pb-3">
            <Workflow className="w-5 h-5 text-indigo-500" /> Retrieval Pipelines
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
            <div className="p-4 bg-secondary/40 border border-border/40 rounded-lg space-y-2">
              <span className="font-bold text-foreground text-sm flex items-center gap-1.5">
                1. Ingestion Layer
              </span>
              <p>
                Validates inputs and extracts text strings (PyPDF), audio tracks (FFmpeg conversion to WAV), and video keyframes (FFmpeg offset frames).
              </p>
            </div>
            <div className="p-4 bg-secondary/40 border border-border/40 rounded-lg space-y-2">
              <span className="font-bold text-foreground text-sm flex items-center gap-1.5">
                2. AI Models Vectorization
              </span>
              <p>
                Calculates dense 512-dim vectors: BGE-M3 (text/audio transcriptions) and CLIP (video visual features). Truncated and L2-normalized.
              </p>
            </div>
            <div className="p-4 bg-secondary/40 border border-border/40 rounded-lg space-y-2">
              <span className="font-bold text-foreground text-sm flex items-center gap-1.5">
                3. Hybrid Search & Rerank
              </span>
              <p>
                Combines pgvector similarity searches and lexical Full-Text Search. Refines scoring lists using BAAI/bge-reranker-base cross-encoder.
              </p>
            </div>
          </div>
        </div>

        {/* Integration Models Stack details */}
        <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-4">
          <h3 className="font-bold text-base text-foreground flex items-center gap-2 border-b border-border pb-3">
            <Cpu className="w-5 h-5 text-indigo-500" /> Deep Learning Models Stack
          </h3>
          <div className="space-y-4">
            <div className="flex items-start gap-4">
              <div className="p-2.5 bg-primary/10 text-primary rounded-lg shrink-0">
                <Database className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-sm text-foreground">BGE-M3 (BAAI/bge-m3)</h4>
                <p className="mt-1 text-xs">
                  Generates dense semantic vector mappings for text documents and transcribed audio segments. Normalised via L2 validation and sliced to 512 dimensions.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="p-2.5 bg-primary/10 text-primary rounded-lg shrink-0">
                <Sparkles className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-sm text-foreground">CLIP (openai/clip-vit-base-patch32)</h4>
                <p className="mt-1 text-xs">
                  Extracts visual feature vectors from extracted video frame images, enabling direct text-to-video search matching.
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4">
              <div className="p-2.5 bg-primary/10 text-primary rounded-lg shrink-0">
                <Cpu className="w-5 h-5" />
              </div>
              <div>
                <h4 className="font-bold text-sm text-foreground">BAAI/bge-reranker-base</h4>
                <p className="mt-1 text-xs">
                  Local cross-encoder model running thread-safely inside CPU environments. Computes exact relevance scores for query-document candidate lists.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Mathematics section */}
        <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-4">
          <h3 className="font-bold text-base text-foreground flex items-center gap-2 border-b border-border pb-3">
            <Layers className="w-5 h-5 text-indigo-500" /> Retrieval Mathematics
          </h3>
          <div className="space-y-4 text-xs leading-relaxed">
            <div>
              <h4 className="font-bold text-sm text-foreground mb-1">Normalized Lexical Scoring (FTS)</h4>
              <p className="mb-2 text-muted-foreground">
                Raw PostgreSQL `ts_rank` values are unbounded. To fuse them linearly with cosine vectors, FTS ranks are normalized into a strict range:
              </p>
              <pre className="p-3 bg-secondary rounded-lg font-mono text-center font-bold text-foreground">
                Score(keyword) = ts_rank / (ts_rank + 1.0)
              </pre>
            </div>

            <div>
              <h4 className="font-bold text-sm text-foreground mb-1">Score Linear Fusion Formula</h4>
              <p className="mb-2 text-muted-foreground">
                Hybrid retrieval linear combination fuses scores based on client parameter weights (default weight `w = 0.7` for vector models):
              </p>
              <pre className="p-3 bg-secondary rounded-lg font-mono text-center font-bold text-foreground">
                Score(fused) = w * Score(semantic) + (1.0 - w) * Score(keyword)
              </pre>
            </div>

            <div>
              <h4 className="font-bold text-sm text-foreground mb-1">Reranker Sigmoid Normalization</h4>
              <p className="mb-2 text-muted-foreground">
                Cross-encoder output logits are mapped into probability confidence ranges:
              </p>
              <pre className="p-3 bg-secondary rounded-lg font-mono text-center font-bold text-foreground">
                Score(reranked) = 1.0 / (1.0 + e^-logit)
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
