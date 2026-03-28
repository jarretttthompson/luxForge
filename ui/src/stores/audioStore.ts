import { create } from 'zustand'

import type { AudioAnalysis } from '../types/api'

export type ConnectionState = 'connecting' | 'open' | 'closed'

const initialAudio: AudioAnalysis = {
  fft: [],
  bands: {
    sub: 0,
    low: 0,
    mid: 0,
    hi_mid: 0,
    high: 0,
  },
  rms: 0,
  peak: 0,
  bpm: 0,
  beat: false,
  beat_phase: 0,
  onset: false,
  spectral_centroid: 0,
}

interface AudioStoreState {
  analysis: AudioAnalysis
  connectionState: ConnectionState
  lastUpdated: number | null
  setAnalysis: (analysis: AudioAnalysis) => void
  setConnectionState: (state: ConnectionState) => void
}

export const useAudioStore = create<AudioStoreState>((set) => ({
  analysis: initialAudio,
  connectionState: 'connecting',
  lastUpdated: null,
  setAnalysis: (analysis) =>
    set({
      analysis,
      lastUpdated: Date.now(),
    }),
  setConnectionState: (connectionState) => set({ connectionState }),
}))
