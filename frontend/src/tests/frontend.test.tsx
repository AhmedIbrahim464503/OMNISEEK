import React from 'react';
import { render, screen, act } from '@testing-library/react';
import { useSearchStore } from '../store/useSearchStore';
import ExplainabilityPanel from '../components/ExplainabilityPanel';

// Jest tests for Zustand State Store
describe('Zustand Search State Store', () => {
  beforeEach(() => {
    act(() => {
      useSearchStore.setState({
        searchQuery: '',
        searchMode: 'balanced',
        modality: 'ALL',
        topK: 10,
        minScore: 0.0,
        searchHistory: [],
        theme: 'dark',
        recentAssets: []
      });
    });
  });

  test('should initialize with correct default state settings', () => {
    const state = useSearchStore.getState();
    expect(state.searchQuery).toBe('');
    expect(state.searchMode).toBe('balanced');
    expect(state.modality).toBe('ALL');
    expect(state.topK).toBe(10);
    expect(state.theme).toBe('dark');
  });

  test('should update search query correctly', () => {
    act(() => {
      useSearchStore.getState().setSearchQuery('test query');
    });
    expect(useSearchStore.getState().searchQuery).toBe('test query');
  });

  test('should update search mode correctly', () => {
    act(() => {
      useSearchStore.getState().setSearchMode('accurate');
    });
    expect(useSearchStore.getState().searchMode).toBe('accurate');
  });

  test('should add recent assets correctly', () => {
    act(() => {
      useSearchStore.getState().addRecentAsset({
        id: 'asset-123',
        name: 'video.mp4',
        status: 'Processing',
        timestamp: new Date().toISOString()
      });
    });
    const assets = useSearchStore.getState().recentAssets;
    expect(assets.length).toBe(1);
    expect(assets[0].name).toBe('video.mp4');
    expect(assets[0].status).toBe('Processing');
  });

  test('should update recent asset status correctly', () => {
    act(() => {
      useSearchStore.getState().addRecentAsset({
        id: 'asset-123',
        name: 'video.mp4',
        status: 'Processing',
        timestamp: new Date().toISOString()
      });
      useSearchStore.getState().updateRecentAssetStatus('asset-123', 'Completed', 15);
    });
    const assets = useSearchStore.getState().recentAssets;
    expect(assets[0].status).toBe('Completed');
    expect(assets[0].chunkCount).toBe(15);
  });
});

// Jest tests for Explainability Panel rendering
describe('Explainability Panel Component', () => {
  test('should render empty state when no metrics provided', () => {
    render(<ExplainabilityPanel score={0.8} />);
    expect(screen.getByText(/No semantic query metrics logged/i)).toBeInTheDocument();
  });

  test('should render score breakdowns and match text rationale', () => {
    const mockExplanation = {
      match_type: 'Hybrid Fusion',
      fused_score: 0.85,
      semantic_score: 0.8,
      keyword_score: 0.6,
      reranker_score: 0.9,
      rationale: 'High keyword overlap and semantic similarity matching.'
    };

    render(<ExplainabilityPanel explanation={mockExplanation} score={0.85} />);
    
    expect(screen.getByText(/Explainability Telemetry/i)).toBeInTheDocument();
    expect(screen.getByText(/High keyword overlap and semantic similarity/i)).toBeInTheDocument();
    expect(screen.getByText(/Hybrid Fusion/i)).toBeInTheDocument();
    expect(screen.getByText(/Semantic Distance Score/i)).toBeInTheDocument();
    expect(screen.getByText(/Lexical FTS Rank Score/i)).toBeInTheDocument();
    expect(screen.getByText(/Cross-Encoder Logit Score/i)).toBeInTheDocument();
  });
});
