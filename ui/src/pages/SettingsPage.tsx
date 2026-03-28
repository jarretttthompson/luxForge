import { useCallback, useEffect, useState } from 'react'

import { EngineLiveSummary } from '../components/output/EngineLiveSummary'
import type { AudioConfig, AudioDeviceInfo, SystemHealth } from '../types/api'

export function SettingsPage() {
  const [health, setHealth] = useState<SystemHealth | null>(null)
  const [config, setConfig] = useState<AudioConfig | null>(null)
  const [devices, setDevices] = useState<AudioDeviceInfo[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(async () => {
    setError(null)
    setLoading(true)
    try {
      const [h, c, d] = await Promise.all([
        fetch('/api/system/health').then((r) => {
          if (!r.ok) throw new Error('Health request failed')
          return r.json() as Promise<SystemHealth>
        }),
        fetch('/api/audio/config').then((r) => {
          if (!r.ok) throw new Error('Audio config request failed')
          return r.json() as Promise<AudioConfig>
        }),
        fetch('/api/audio/devices').then((r) => {
          if (!r.ok) throw new Error('Device list request failed')
          return r.json() as Promise<{ devices: AudioDeviceInfo[] }>
        }),
      ])
      setHealth(h)
      setConfig(c)
      setDevices(d.devices ?? [])
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load settings.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const activeDevice =
    config?.device_index != null ? devices.find((d) => d.index === config.device_index) : null

  return (
    <section className="rounded-3xl border border-gray-800 bg-gray-900/70 shadow-2xl shadow-black/20 overflow-hidden">
      <div className="flex flex-col gap-4 border-b border-gray-800 px-8 py-6 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-3xl font-semibold text-gray-100">Settings</h2>
          <p className="mt-1 max-w-xl text-sm text-gray-400">
            System and audio configuration from the engine API. Live values also stream over the
            dashboard WebSocket.
          </p>
        </div>
        <button
          type="button"
          onClick={() => refresh()}
          disabled={loading}
          className="rounded-xl border border-gray-700 bg-gray-800 px-4 py-2 text-sm font-medium text-gray-200 hover:bg-gray-700 disabled:opacity-50"
        >
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      <div className="space-y-6 px-8 py-8">
        <EngineLiveSummary />

        {error && (
          <p className="rounded-xl border border-red-500/25 bg-red-500/10 px-4 py-3 text-sm text-red-300">
            {error}{' '}
            <span className="text-red-400/80">Is the API running on port 8765?</span>
          </p>
        )}

        <div className="grid gap-6 lg:grid-cols-2">
          <div className="rounded-2xl border border-gray-800 bg-gray-950/50 p-5">
            <h3 className="text-sm font-medium text-gray-300">System health</h3>
            {loading && !health ? (
              <p className="mt-3 text-sm text-gray-500">Loading…</p>
            ) : health ? (
              <dl className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500">Status</dt>
                  <dd className="font-medium text-emerald-400">{health.status}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500">Engine</dt>
                  <dd className="text-gray-200">{health.engine_running ? 'Running' : 'Stopped'}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500">FPS</dt>
                  <dd className="font-mono tabular-nums text-gray-200">{health.fps}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500">Tick count</dt>
                  <dd className="font-mono tabular-nums text-gray-200">
                    {health.tick_count.toLocaleString()}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500">Active console</dt>
                  <dd className="truncate text-gray-200" title={health.active_console}>
                    {health.active_console}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500">Active scene</dt>
                  <dd className="text-gray-200">
                    {health.active_scene ?? <span className="text-gray-600">None</span>}
                  </dd>
                </div>
              </dl>
            ) : null}
          </div>

          <div className="rounded-2xl border border-gray-800 bg-gray-950/50 p-5">
            <h3 className="text-sm font-medium text-gray-300">Audio</h3>
            {loading && !config ? (
              <p className="mt-3 text-sm text-gray-500">Loading…</p>
            ) : config ? (
              <dl className="mt-4 space-y-2 text-sm">
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500">Input device</dt>
                  <dd className="max-w-[60%] truncate text-right text-gray-200" title={activeDevice?.name}>
                    {activeDevice?.name ?? (config.device_index == null ? 'Default / simulator' : `#${config.device_index}`)}
                  </dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500">Sample rate</dt>
                  <dd className="font-mono text-gray-200">{config.sample_rate} Hz</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500">Buffer</dt>
                  <dd className="font-mono text-gray-200">{config.buffer_size} samples</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500">Simulator</dt>
                  <dd className="text-gray-200">{config.simulator_enabled ? 'On' : 'Off'}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500">Sim mode</dt>
                  <dd className="truncate text-gray-200">{config.simulator_mode}</dd>
                </div>
                <div className="flex justify-between gap-4">
                  <dt className="text-gray-500">Sim BPM</dt>
                  <dd className="font-mono text-gray-200">{config.simulator_bpm}</dd>
                </div>
              </dl>
            ) : null}
            <p className="mt-4 border-t border-gray-800 pt-3 text-xs text-gray-600">
              Editing audio settings from the UI will arrive in a future session; use the engine
              config file or API extensions for now.
            </p>
          </div>
        </div>

        <div className="rounded-2xl border border-gray-800 bg-gray-950/50 p-5">
          <h3 className="text-sm font-medium text-gray-300">Audio devices ({devices.length})</h3>
          {devices.length === 0 ? (
            <p className="mt-3 text-sm text-gray-500">
              No devices reported — simulator or unavailable audio backend.
            </p>
          ) : (
            <ul className="mt-3 max-h-56 space-y-2 overflow-y-auto text-sm">
              {devices.map((d) => (
                <li
                  key={d.index}
                  className={`rounded-lg border px-3 py-2 ${
                    config?.device_index === d.index
                      ? 'border-cyan-600/40 bg-cyan-950/20'
                      : 'border-gray-800 bg-gray-900/30'
                  }`}
                >
                  <span className="font-mono text-xs text-gray-500">#{d.index}</span>{' '}
                  <span className="text-gray-200">{d.name}</span>
                  <span className="ml-2 text-xs text-gray-500">
                    {d.channels}ch · {Math.round(d.sample_rate)} Hz
                  </span>
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
    </section>
  )
}
