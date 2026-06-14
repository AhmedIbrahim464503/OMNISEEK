import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export type SearchMode = 'fast' | 'balanced' | 'accurate';
export type ModalityType = 'ALL' | 'TEXT' | 'IMAGE' | 'AUDIO' | 'VIDEO';

export interface HistoryItem {
  query: string;
  timestamp: string;
  mode: SearchMode;
  modality: ModalityType;
  resultsCount: number;
}

export interface RecentAsset {
  id: string;
  name: string;
  status: string;
  timestamp: string;
  chunkCount?: number;
}

interface SearchStore {
  searchQuery: string;
  searchMode: SearchMode;
  modality: ModalityType;
  topK: number;
  minScore: number;
  searchHistory: HistoryItem[];
  theme: 'dark' | 'light';
  recentAssets: RecentAsset[];
  
  setSearchQuery: (query: string) => void;
  setSearchMode: (mode: SearchMode) => void;
  setModality: (modality: ModalityType) => void;
  setTopK: (k: number) => void;
  setMinScore: (score: number) => void;
  addHistoryItem: (item: Omit<HistoryItem, 'timestamp'>) => void;
  clearHistory: () => void;
  toggleTheme: () => void;
  setTheme: (theme: 'dark' | 'light') => void;
  addRecentAsset: (asset: RecentAsset) => void;
  updateRecentAssetStatus: (id: string, status: string, chunkCount?: number) => void;
}

export const useSearchStore = create<SearchStore>()(
  persist(
    (set) => ({
      searchQuery: '',
      searchMode: 'balanced',
      modality: 'ALL',
      topK: 10,
      minScore: 0.0,
      searchHistory: [],
      theme: 'dark',
      recentAssets: [],

      setSearchQuery: (query) => set({ searchQuery: query }),
      setSearchMode: (mode) => set({ searchMode: mode }),
      setModality: (modality) => set({ modality }),
      setTopK: (k) => set({ topK: k }),
      setMinScore: (score) => set({ minScore: score }),
      addHistoryItem: (item) =>
        set((state) => {
          const newItem = { ...item, timestamp: new Date().toISOString() };
          const filtered = state.searchHistory.filter(
            (h) => h.query.toLowerCase() !== item.query.toLowerCase()
          );
          return { searchHistory: [newItem, ...filtered].slice(0, 50) };
        }),
      clearHistory: () => set({ searchHistory: [] }),
      toggleTheme: () =>
        set((state) => ({ theme: state.theme === 'dark' ? 'light' : 'dark' })),
      setTheme: (theme) => set({ theme }),
      addRecentAsset: (asset) =>
        set((state) => {
          const filtered = state.recentAssets.filter((a) => a.id !== asset.id);
          return { recentAssets: [asset, ...filtered].slice(0, 10) };
        }),
      updateRecentAssetStatus: (id, status, chunkCount) =>
        set((state) => ({
          recentAssets: state.recentAssets.map((a) =>
            a.id === id ? { ...a, status, chunkCount: chunkCount ?? a.chunkCount } : a
          ),
        })),
    }),
    {
      name: 'omniseek-settings-store',
    }
  )
);
