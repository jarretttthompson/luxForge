import { useMemo } from 'react'

import { useEngineStore } from '../../stores/engineStore'

interface Props {
  /** Cap visible rows (remaining count shown in footer). */
  maxRows?: number
  className?: string
}

function clamp01(n: number) {
  return Math.min(1, Math.max(0, n))
}

/** Live mapping output targets and normalized values (from engine WebSocket). */
export function DMXMonitor({ maxRows, className = '' }: Props) {
  const outputs = useEngineStore((s) => s.outputs)

  const sorted = useMemo(
    () => [...outputs].sort((a, b) => a.target.localeCompare(b.target)),
    [outputs],
  )

  const visible = maxRows !== undefined ? sorted.slice(0, maxRows) : sorted
  const hidden = maxRows !== undefined ? Math.max(0, sorted.length - maxRows) : 0

  return (
    <div
      className={`rounded-2xl border border-gray-800 bg-gray-950/60 p-4 shadow-inner shadow-black/30 ${className}`}
    >
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium tracking-wide text-gray-300">Output values</h3>
        <span className="text-xs text-gray-500 tabular-nums">{outputs.length} channels</span>
      </div>

      {outputs.length === 0 ? (
        <p className="py-10 text-center text-sm text-gray-500">
          No mapping outputs yet. Enable rules on the{' '}
          <span className="text-gray-400">Mapping</span> page and run the engine.
        </p>
      ) : (
        <ul className="max-h-[min(420px,55vh)] space-y-2 overflow-y-auto pr-1" aria-label="Output levels">
          {visible.map((o) => {
            const t = clamp01(o.value)
            const pct = Math.round(t * 100)
            const dmx = Math.round(t * 255)
            return (
              <li key={o.target}>
                <div className="mb-0.5 flex items-center justify-between gap-2 text-xs">
                  <span className="min-w-0 truncate font-mono text-gray-300" title={o.target}>
                    {o.target}
                  </span>
                  <span className="flex-shrink-0 tabular-nums text-gray-500">
                    {pct}% <span className="text-gray-600">·</span> DMX {dmx}
                  </span>
                </div>
                <div
                  className="h-2 overflow-hidden rounded-full bg-gray-800/90 ring-1 ring-gray-700/40"
                  role="meter"
                  aria-valuenow={pct}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label={`${o.target} at ${pct} percent`}
                >
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-cyan-600 to-violet-500 transition-[width] duration-100 ease-out"
                    style={{ width: `${pct}%` }}
                  />
                </div>
              </li>
            )
          })}
        </ul>
      )}

      {hidden > 0 && (
        <p className="mt-3 border-t border-gray-800 pt-2 text-center text-xs text-gray-500">
          +{hidden} additional outputs
        </p>
      )}
    </div>
  )
}
