import { useEffect, useState } from 'react'

import { useEngineStore } from '../../stores/engineStore'
import type { ProtocolStatusRow } from '../../types/api'

interface Props {
  className?: string
  /** Also refresh from REST when mounted (fills gaps if WS not yet received protocols). */
  fetchRest?: boolean
}

async function fetchProtocolRows(): Promise<ProtocolStatusRow[]> {
  const res = await fetch('/api/protocols/status')
  if (!res.ok) return []
  const data = (await res.json()) as { protocols: ProtocolStatusRow[] }
  return data.protocols ?? []
}

/** Protocol adapters: live from WebSocket store, optional one-shot REST merge. */
export function ProtocolStatus({ className = '', fetchRest = false }: Props) {
  const liveProtocols = useEngineStore((s) => s.protocols)
  const [restRows, setRestRows] = useState<ProtocolStatusRow[] | null>(null)

  useEffect(() => {
    if (!fetchRest) return
    fetchProtocolRows().then(setRestRows).catch(() => setRestRows([]))
  }, [fetchRest])

  const names = new Set<string>([
    ...Object.keys(liveProtocols),
    ...(restRows?.map((r) => r.name) ?? []),
  ])
  const sortedNames = [...names].sort((a, b) => a.localeCompare(b))

  const rows = sortedNames.map((name) => {
    const live = liveProtocols[name]
    const rest = restRows?.find((r) => r.name === name)
    if (live) {
      return {
        name,
        connected: live.connected,
        dry_run: live.dry_run,
        messages_sent: live.messages_sent,
        source: 'live' as const,
      }
    }
    if (rest) {
      return {
        name: rest.name,
        connected: rest.connected,
        dry_run: rest.dry_run,
        messages_sent: rest.messages_sent,
        source: 'rest' as const,
      }
    }
    return {
      name,
      connected: false,
      dry_run: true,
      messages_sent: 0,
      source: 'unknown' as const,
    }
  })

  return (
    <div
      className={`rounded-2xl border border-gray-800 bg-gray-950/60 p-4 shadow-inner shadow-black/30 ${className}`}
    >
      <h3 className="mb-3 text-sm font-medium tracking-wide text-gray-300">Protocols</h3>

      {rows.length === 0 ? (
        <p className="py-6 text-center text-sm text-gray-500">
          No protocol adapters registered. Start the engine with outputs configured.
        </p>
      ) : (
        <ul className="space-y-2" aria-label="Protocol connection status">
          {rows.map((row) => (
            <li
              key={row.name}
              className="flex items-center justify-between gap-3 rounded-xl border border-gray-800/80 bg-gray-900/40 px-3 py-2.5"
            >
              <div className="min-w-0">
                <p className="truncate text-sm font-medium capitalize text-gray-200">{row.name}</p>
                <p className="text-xs text-gray-500 tabular-nums">
                  {row.messages_sent.toLocaleString()} msgs
                  {row.source === 'rest' && (
                    <span className="ml-1 text-amber-600/80">· snapshot</span>
                  )}
                </p>
              </div>
              <div className="flex flex-shrink-0 flex-wrap items-center justify-end gap-1.5">
                {row.dry_run && (
                  <span className="rounded-md bg-amber-500/15 px-1.5 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-amber-200">
                    Dry run
                  </span>
                )}
                <span
                  className={[
                    'rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide',
                    row.connected
                      ? 'bg-emerald-500/15 text-emerald-300'
                      : 'bg-gray-700/50 text-gray-500',
                  ].join(' ')}
                >
                  {row.connected ? 'Connected' : 'Offline'}
                </span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
