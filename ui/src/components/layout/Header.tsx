import { useAudioStore } from '../../stores/audioStore'
import { useEngineStore } from '../../stores/engineStore'

const connectionStyles = {
  connecting: 'bg-amber-400',
  open: 'bg-emerald-400',
  closed: 'bg-rose-500',
} as const

const connectionLabels = {
  connecting: 'Connecting',
  open: 'Connected',
  closed: 'Offline',
} as const

export function Header() {
  const connectionState = useAudioStore((state) => state.connectionState)
  const engineFps = useEngineStore((s) => s.engine?.fps)
  const engineRunning = useEngineStore((s) => s.engine?.running)

  return (
    <header className="flex min-h-20 flex-col gap-3 border-b border-gray-800 bg-gray-900/90 px-6 py-4 backdrop-blur sm:flex-row sm:items-center sm:justify-between sm:py-0 sm:h-20">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">Lighting Console Thing</p>
        <h1 className="mt-2 text-2xl font-semibold text-gray-100">Live Control Surface</h1>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        {connectionState === 'open' && engineFps != null && (
          <div
            className="hidden items-center gap-2 rounded-full border border-gray-700/80 bg-gray-800/80 px-3 py-1.5 text-xs text-gray-400 sm:flex"
            title={engineRunning ? 'Engine running' : 'Engine idle'}
          >
            <span className={`h-1.5 w-1.5 rounded-full ${engineRunning ? 'bg-emerald-400' : 'bg-gray-500'}`} />
            <span className="tabular-nums">
              <span className="text-gray-500">FPS</span>{' '}
              <span className="font-mono text-gray-200">{engineFps}</span>
            </span>
          </div>
        )}
        <div className="flex items-center gap-3 rounded-full border border-gray-700 bg-gray-800 px-4 py-2 text-sm text-gray-200">
          <span className={`h-2.5 w-2.5 rounded-full ${connectionStyles[connectionState]}`} />
          <span>{connectionLabels[connectionState]}</span>
        </div>
      </div>
    </header>
  )
}
