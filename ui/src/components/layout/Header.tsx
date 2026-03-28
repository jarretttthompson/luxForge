import { useAudioStore } from '../../stores/audioStore'

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

  return (
    <header className="flex h-20 items-center justify-between border-b border-gray-800 bg-gray-900/90 px-6 backdrop-blur">
      <div>
        <p className="text-xs uppercase tracking-[0.3em] text-cyan-300">Lighting Console Thing</p>
        <h1 className="mt-2 text-2xl font-semibold text-gray-100">Live Control Surface</h1>
      </div>

      <div className="flex items-center gap-3 rounded-full border border-gray-700 bg-gray-800 px-4 py-2 text-sm text-gray-200">
        <span className={`h-2.5 w-2.5 rounded-full ${connectionStyles[connectionState]}`} />
        <span>{connectionLabels[connectionState]}</span>
      </div>
    </header>
  )
}
