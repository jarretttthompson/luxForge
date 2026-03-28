import { Link } from 'react-router-dom'

import { BandMeters } from '../components/audio/BandMeters'
import { BeatIndicator } from '../components/audio/BeatIndicator'
import { FFTDisplay } from '../components/audio/FFTDisplay'
import { WaveformDisplay } from '../components/audio/WaveformDisplay'
import { DMXMonitor } from '../components/output/DMXMonitor'
import { EngineLiveSummary } from '../components/output/EngineLiveSummary'
import { ProtocolStatus } from '../components/output/ProtocolStatus'
import { useAudioStore } from '../stores/audioStore'

export function DashboardPage() {
  const connectionState = useAudioStore((s) => s.connectionState)

  const statusLabel =
    connectionState === 'open'
      ? 'Live'
      : connectionState === 'connecting'
        ? 'Connecting…'
        : 'Disconnected'

  const statusClass =
    connectionState === 'open'
      ? 'bg-emerald-500/15 text-emerald-300 ring-emerald-500/30'
      : connectionState === 'connecting'
        ? 'bg-amber-500/15 text-amber-200 ring-amber-500/25'
        : 'bg-red-500/10 text-red-300 ring-red-500/20'

  return (
    <section className="rounded-3xl border border-gray-800 bg-gray-900/70 p-8 shadow-2xl shadow-black/20">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-3xl font-semibold text-gray-100">Dashboard</h2>
          <p className="mt-1 max-w-xl text-sm text-gray-400">
            Live audio analysis from the engine. Connect the app WebSocket (port 8765) to stream
            FFT, bands, level, and beat data.
          </p>
        </div>
        <span
          className={`inline-flex w-fit items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-wide ring-1 ${statusClass}`}
        >
          {statusLabel}
        </span>
      </div>

      <div className="mt-6">
        <EngineLiveSummary />
      </div>

      <div className="mt-8 grid gap-6 lg:grid-cols-2">
        <div className="lg:col-span-2">
          <FFTDisplay />
        </div>
        <WaveformDisplay />
        <BeatIndicator />
        <div className="lg:col-span-2">
          <BandMeters />
        </div>
        <div className="lg:col-span-2">
          <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-gray-500">
            Live output
          </h3>
          <div className="grid gap-6 lg:grid-cols-2">
            <ProtocolStatus />
            <DMXMonitor maxRows={8} />
          </div>
          <p className="mt-3 text-center text-xs text-gray-600">
            Full channel list and fixture patch on the{' '}
            <Link to="/fixtures" className="text-cyan-500/90 hover:text-cyan-400">
              Fixtures
            </Link>{' '}
            page.
          </p>
        </div>
      </div>
    </section>
  )
}
