'use client';

import React, { useRef, useEffect } from 'react';
import { Play, Pause, RotateCcw, Volume2, Maximize } from 'lucide-react';

interface PlayerProps {
  src: string;
  startTime?: number; // in seconds
  onClose?: () => void;
}

export function VideoPlayer({ src, startTime = 0 }: PlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null);

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.currentTime = startTime;
      videoRef.current.play().catch(() => {});
    }
  }, [src, startTime]);

  return (
    <div className="flex flex-col bg-black rounded-lg overflow-hidden shadow-lg border border-border">
      <div className="relative aspect-video w-full bg-neutral-950">
        <video
          ref={videoRef}
          src={src}
          controls
          className="w-full h-full"
          preload="auto"
        />
      </div>
      <div className="p-3 bg-secondary/80 flex items-center justify-between text-xs text-muted-foreground">
        <span>Timeline Jump Position: {startTime}s</span>
        <span className="text-[10px] bg-primary/10 text-primary px-2 py-0.5 rounded font-semibold">HTML5 Player Active</span>
      </div>
    </div>
  );
}

export function AudioPlayer({ src, startTime = 0 }: PlayerProps) {
  const audioRef = useRef<HTMLAudioElement>(null);

  useEffect(() => {
    if (audioRef.current) {
      audioRef.current.currentTime = startTime;
      audioRef.current.play().catch(() => {});
    }
  }, [src, startTime]);

  return (
    <div className="flex flex-col bg-card border border-border rounded-lg p-4 shadow-sm space-y-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-muted-foreground">Audio Segment Playback</span>
        <span className="text-[10px] bg-amber-500/10 text-amber-600 px-2 py-0.5 rounded font-semibold">
          Jump: {startTime}s
        </span>
      </div>
      <audio
        ref={audioRef}
        src={src}
        controls
        className="w-full"
        preload="auto"
      />
    </div>
  );
}

interface DocProps {
  assetName: string;
  content: string;
  highlightText?: string;
}

export function DocumentViewer({ assetName, content, highlightText }: DocProps) {
  const highlightContent = (fullText: string, searchPhrase?: string) => {
    if (!searchPhrase) return <span>{fullText}</span>;
    
    const index = fullText.toLowerCase().indexOf(searchPhrase.toLowerCase());
    if (index === -1) {
      return <span>{fullText}</span>;
    }
    
    const start = fullText.slice(0, index);
    const match = fullText.slice(index, index + searchPhrase.length);
    const end = fullText.slice(index + searchPhrase.length);
    
    return (
      <>
        {start}
        <mark className="bg-yellow-500/30 text-foreground font-semibold px-1 py-0.5 rounded border-b-2 border-yellow-500 animate-pulse">
          {match}
        </mark>
        {end}
      </>
    );
  };

  return (
    <div className="flex flex-col bg-card border border-border rounded-lg overflow-hidden shadow-sm h-[320px]">
      <div className="px-4 py-3 bg-secondary/50 border-b border-border flex items-center justify-between">
        <span className="text-sm font-semibold truncate text-foreground">{assetName}</span>
        <span className="text-[10px] bg-blue-500/10 text-blue-500 px-2 py-0.5 rounded font-semibold">Document Node</span>
      </div>
      <div className="p-4 overflow-y-auto text-sm leading-relaxed text-muted-foreground whitespace-pre-wrap flex-1 bg-card">
        {highlightContent(content, highlightText)}
      </div>
    </div>
  );
}
