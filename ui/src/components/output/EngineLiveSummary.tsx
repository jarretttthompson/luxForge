import { useEngineStore } from '../../stores/engineStore'
import { useAudioStore } from '../../stores/audioStore'

interface Props {
  className?: string
}

/** Compact live engine line: uses WebSocket-fed store when connected. */
export function EngineLiveSummary({ className = '' }: Props) {
  const connectionState = useAudioStore((s) => s.connectionState)
  const engine = useEngineStore((s) => s.engine)
  const consoleName = useEngineStore((s) => s.consoleName)
  const sceneName = useEngineStore((s) => s.sceneName)

  const live = connectionState === 'open' && engine !== null

  return (
    <div
      className={`flex flex-wrap items-center gap-x-4 gap-y-2 rounded-xl border border-gray-800 bg-gray-950/50 px-4 py-3 text-sm ${className}`}
    >
      <div className="flex items-center gap-2">
        <span
          className={`h-2 w-2 rounded-full ${live && engine?.running ? 'bg-emerald-400' : 'bg-gray-600'}`}
          aria-hidden
        />
        <span className="text-gray-400">Engine</span>
        <span className="font-medium text-gray-200">
          {live ? (engine?.running ? 'Running' : 'Idle') : '—'}
        </span>
      </div>
      {live && (
        <>
          <span className="hidden h-4 w-px bg-gray-800 sm:block" aria-hidden />
          <span className="text-gray-500">
            FPS{' '}
            <span className="font-mono tabular-nums text-gray-300">{engine?.fps ?? '—'}</span>
          </span>
          <span className="text-gray-500">
            Ticks{' '}
            <span className="font-mono tabular-nums text-gray-300">
              {(engine?.tick_count ?? 0).toLocaleString()}
            </span>
          </span>
          <span className="text-gray-500">
            Console{' '}
            <span className="text-gray-300">{consoleName}</span>
          </span>
          {sceneName != null && sceneName !== '' && (
            <span className="text-gray-500">
              Scene <span className="text-violet-300">{sceneName}</span>
            </span>
          )}
        </>
      )}
      {!live && (
        <span className="text-xs text-gray-600">Connect WebSocket to stream engine stats.</span>
      )}
    </div>
  )
}
