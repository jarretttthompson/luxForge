import { useEffect, useRef, useState } from 'react'

import { useAudioStore } from '../../stores/audioStore'

/** BPM, beat-phase ring, and flash on beat rising edge. */
export function BeatIndicator() {
  const bpm = useAudioStore((s) => s.analysis.bpm)
  const beat = useAudioStore((s) => s.analysis.beat)
  const beatPhase = useAudioStore((s) => s.analysis.beat_phase)
  const onset = useAudioStore((s) => s.analysis.onset)

  const prevBeat = useRef(false)
  const [flash, setFlash] = useState(false)
  const [onsetFlash, setOnsetFlash] = useState(false)

  useEffect(() => {
    if (beat && !prevBeat.current) {
      setFlash(true)
      const t = window.setTimeout(() => setFlash(false), 140)
      prevBeat.current = true
      return () => window.clearTimeout(t)
    }
    if (!beat) {
      prevBeat.current = false
    }
    return undefined
  }, [beat])

  const prevOnset = useRef(false)
  useEffect(() => {
    if (onset && !prevOnset.current) {
      setOnsetFlash(true)
      const t = window.setTimeout(() => setOnsetFlash(false), 90)
      prevOnset.current = true
      return () => window.clearTimeout(t)
    }
    if (!onset) {
      prevOnset.current = false
    }
    return undefined
  }, [onset])

  const phaseDeg = beatPhase * 360

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-950/60 p-4 shadow-inner shadow-black/30">
      <h3 className="mb-4 text-sm font-medium tracking-wide text-gray-300">Beat &amp; tempo</h3>
      <div className="flex flex-col items-center gap-4 sm:flex-row sm:items-center sm:justify-center sm:gap-8">
        <div
          className="relative flex h-28 w-28 items-center justify-center rounded-full border-2 border-gray-700 bg-gray-900/80"
          style={{
            boxShadow: flash
              ? '0 0 32px rgba(34, 211, 238, 0.55), inset 0 0 24px rgba(34, 211, 238, 0.12)'
              : onsetFlash
                ? '0 0 24px rgba(167, 139, 250, 0.45)'
                : undefined,
            transition: 'box-shadow 80ms ease-out',
          }}
          aria-label={`Beat phase ${Math.round(beatPhase * 100)} percent`}
        >
          <div
            className="absolute inset-1 rounded-full"
            style={{
              background: `conic-gradient(from -90deg, rgb(6 182 212) ${phaseDeg}deg, rgb(31 41 55) ${phaseDeg}deg)`,
              mask: 'radial-gradient(farthest-side, transparent calc(100% - 6px), black calc(100% - 6px))',
              WebkitMask:
                'radial-gradient(farthest-side, transparent calc(100% - 6px), black calc(100% - 6px))',
            }}
          />
          <div className="relative z-10 flex flex-col items-center justify-center text-center">
            <span className="text-2xl font-semibold tabular-nums text-gray-100">
              {bpm > 0 ? Math.round(bpm) : '—'}
            </span>
            <span className="text-[10px] font-medium uppercase tracking-wider text-gray-500">BPM</span>
          </div>
        </div>
        <div className="flex flex-col gap-2 text-center sm:text-left">
          <div className="flex flex-wrap items-center justify-center gap-2 sm:justify-start">
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${
                beat ? 'bg-cyan-500/25 text-cyan-300' : 'bg-gray-800 text-gray-500'
              }`}
            >
              Beat
            </span>
            <span
              className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${
                onset ? 'bg-violet-500/25 text-violet-200' : 'bg-gray-800 text-gray-500'
              }`}
            >
              Onset
            </span>
          </div>
          <p className="text-xs text-gray-500">
            Phase ring advances over the inferred beat period. Flash marks a beat event.
          </p>
        </div>
      </div>
    </div>
  )
}
