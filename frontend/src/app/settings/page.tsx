'use client';

import React from 'react';
import { useSearchStore, SearchMode } from '@/store/useSearchStore';
import { 
  Sliders, 
  Settings, 
  Sun, 
  Moon, 
  Info,
  CheckCircle,
  TrendingUp,
  Filter
} from 'lucide-react';

export default function SettingsPage() {
  const { 
    searchMode, 
    setSearchMode, 
    topK, 
    setTopK, 
    minScore, 
    setMinScore, 
    theme, 
    setTheme 
  } = useSearchStore();

  const handleModeChange = (mode: SearchMode) => {
    setSearchMode(mode);
  };

  const handleThemeChange = (selectedTheme: 'dark' | 'light') => {
    setTheme(selectedTheme);
  };

  return (
    <div className="p-6 max-w-3xl mx-auto w-full space-y-8">
      {/* Header */}
      <div className="border-b border-border pb-6">
        <h1 className="text-3xl font-extrabold tracking-tight flex items-center gap-2">
          <Settings className="w-8 h-8 text-primary" /> Settings
        </h1>
        <p className="text-muted-foreground mt-1">
          Configure default retrieval configurations, confidence levels, and user interface preferences.
        </p>
      </div>

      <div className="space-y-6">
        {/* Search Preferences */}
        <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-6">
          <div className="flex items-center gap-2 border-b border-border pb-3">
            <Sliders className="w-5 h-5 text-indigo-500" />
            <h3 className="font-bold text-base text-foreground">Default Engine Behavior</h3>
          </div>

          {/* Default Search Mode */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-foreground">Default Search Profile</label>
            <div className="grid grid-cols-3 gap-3">
              {(['fast', 'balanced', 'accurate'] as const).map((mode) => (
                <button
                  key={mode}
                  type="button"
                  onClick={() => handleModeChange(mode)}
                  className={`
                    py-3 px-4 rounded-xl border text-center font-semibold text-xs capitalize transition flex flex-col items-center gap-1.5
                    ${searchMode === mode
                      ? 'border-primary bg-primary/5 text-primary'
                      : 'border-border bg-card text-muted-foreground hover:text-foreground hover:bg-secondary'
                    }
                  `}
                >
                  <span className="font-bold">{mode}</span>
                  <span className="text-[10px] text-muted-foreground font-normal">
                    {mode === 'fast' && 'Vector only'}
                    {mode === 'balanced' && 'FTS + Vector'}
                    {mode === 'accurate' && 'Hybrid + Rerank'}
                  </span>
                </button>
              ))}
            </div>
          </div>

          {/* Default Top-K limit */}
          <div className="space-y-3">
            <div className="flex justify-between text-sm font-semibold text-foreground">
              <span>Default Results Count (Top-K)</span>
              <span className="text-primary">{topK} results</span>
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
            <p className="text-[10px] text-muted-foreground leading-normal">
              Determines how many chunks are initially retrieved from database vectors. Highly accurate searches benefit from larger values (e.g. 15-20 chunks) prior to reranking.
            </p>
          </div>

          {/* Default min score threshold */}
          <div className="space-y-3">
            <div className="flex justify-between text-sm font-semibold text-foreground">
              <span>Minimum Confidence Threshold</span>
              <span className="text-primary">{(minScore * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.0"
              max="0.8"
              step="0.1"
              value={minScore}
              onChange={(e) => setMinScore(parseFloat(e.target.value))}
              className="w-full accent-primary bg-secondary h-1.5 rounded"
            />
            <p className="text-[10px] text-muted-foreground leading-normal">
              Filters out results that fail to align closely with the search topic. Raising this prevents false positive matches from cluttering outputs.
            </p>
          </div>
        </div>

        {/* Display preferences */}
        <div className="p-6 bg-card border border-border rounded-xl shadow-sm space-y-6">
          <div className="flex items-center gap-2 border-b border-border pb-3">
            <Filter className="w-5 h-5 text-indigo-500" />
            <h3 className="font-bold text-base text-foreground">Appearance Preference</h3>
          </div>

          {/* Theme Settings */}
          <div className="space-y-2">
            <label className="text-sm font-semibold text-foreground">Color Scheme</label>
            <div className="grid grid-cols-2 gap-4">
              <button
                type="button"
                onClick={() => handleThemeChange('light')}
                className={`
                  flex items-center justify-center gap-2 p-3.5 rounded-xl border text-sm font-semibold transition
                  ${theme === 'light'
                    ? 'border-primary bg-primary/5 text-primary'
                    : 'border-border bg-card text-muted-foreground hover:text-foreground hover:bg-secondary'
                  }
                `}
              >
                <Sun className="w-4.5 h-4.5" /> Light Mode
              </button>
              <button
                type="button"
                onClick={() => handleThemeChange('dark')}
                className={`
                  flex items-center justify-center gap-2 p-3.5 rounded-xl border text-sm font-semibold transition
                  ${theme === 'dark'
                    ? 'border-primary bg-primary/5 text-primary'
                    : 'border-border bg-card text-muted-foreground hover:text-foreground hover:bg-secondary'
                  }
                `}
              >
                <Moon className="w-4.5 h-4.5" /> Dark Mode
              </button>
            </div>
          </div>
        </div>

        {/* Saved indicator */}
        <div className="p-4 bg-emerald-500/10 border border-emerald-500/20 rounded-xl text-emerald-500 text-xs flex items-center gap-2">
          <CheckCircle className="w-4 h-4 shrink-0" />
          <span>Configuration is fully synced and saved to persistent Local Storage. All search actions update in real time.</span>
        </div>
      </div>
    </div>
  );
}
