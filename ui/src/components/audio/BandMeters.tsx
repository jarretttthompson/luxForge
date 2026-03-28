import { useAudioStore } from '../../stores/audioStore'

const BAND_CONFIG = [
  { key: 'sub' as const, label: 'Sub', className: 'bg-violet-500' },
  { key: 'low' as const, label: 'Low', className: 'bg-fuchsia-500' },
  { key: 'mid' as const, label: 'Mid', className: 'bg-cyan-500' },
  { key: 'hi_mid' as const, label: 'Hi-mid', className: 'bg-sky-500' },
  { key: 'high' as const, label: 'High', className: 'bg-emerald-400' },
]

/** Five frequency-band energy meters from analysis. */
export function BandMeters() {
  const bands = useAudioStore((s) => s.analysis.bands)

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-950/60 p-4 shadow-inner shadow-black/30">
      <h3 className="mb-4 text-sm font-medium tracking-wide text-gray-300">Band energy</h3>
      <ul className="space-y-3" aria-label="Frequency band levels">
        {BAND_CONFIG.map(({ key, label, className }) => {
          const v = Math.min(1, Math.max(0, bands[key]))
          const pct = Math.round(v * 100)
          return (
            <li key={key}>
              <div className="mb-1 flex items-center justify-between text-xs text-gray-400">
                <span className="font-medium text-gray-300">{label}</span>
                <span className="tabular-nums text-gray-500">{pct}%</span>
              </div>
              <div
                className="h-2.5 overflow-hidden rounded-full bg-gray-800/90 ring-1 ring-gray-700/50"
                role="meter"
                aria-valuenow={pct}
                aria-valuemin={0}
                aria-valuemax={100}
                aria-label={`${label} band level`}
              >
                <div
                  className={`h-full rounded-full transition-[width] duration-75 ease-out ${className}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
