import { useEffect, useState } from 'react'

import { DMXMonitor } from '../components/output/DMXMonitor'
import { EngineLiveSummary } from '../components/output/EngineLiveSummary'
import { ProtocolStatus } from '../components/output/ProtocolStatus'

interface ProfileStub {
  id?: string
  name?: string
}

export function FixturesPage() {
  const [profiles, setProfiles] = useState<ProfileStub[]>([])
  const [patchCount, setPatchCount] = useState<number | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false
    Promise.all([
      fetch('/api/fixtures/profiles').then((r) => r.json() as Promise<{ profiles: ProfileStub[] }>),
      fetch('/api/fixtures/patch').then((r) => r.json() as Promise<{ entries: unknown[] }>),
    ])
      .then(([prof, patch]) => {
        if (cancelled) return
        setLoadError(null)
        setProfiles(Array.isArray(prof.profiles) ? prof.profiles : [])
        setPatchCount(Array.isArray(patch.entries) ? patch.entries.length : 0)
      })
      .catch(() => {
        if (!cancelled) setLoadError('Could not load fixture API.')
      })
    return () => {
      cancelled = true
    }
  }, [])

  return (
    <section className="rounded-3xl border border-gray-800 bg-gray-900/70 shadow-2xl shadow-black/20 overflow-hidden">
      <div className="border-b border-gray-800 px-8 py-6">
        <h2 className="text-3xl font-semibold text-gray-100">Fixtures &amp; output</h2>
        <p className="mt-1 max-w-2xl text-sm text-gray-400">
          Monitor live DMX-style output levels from mapping rules, protocol adapters, and fixture
          patch status. Fixture profiles and patch editing arrive in a later release.
        </p>
      </div>

      <div className="space-y-6 px-8 py-8">
        <EngineLiveSummary />

        <div className="grid gap-6 lg:grid-cols-2">
          <ProtocolStatus fetchRest />
          <DMXMonitor />
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          <div className="rounded-2xl border border-gray-800 bg-gray-950/40 p-5">
            <h3 className="text-sm font-medium text-gray-300">Fixture profiles</h3>
            {loadError && (
              <p className="mt-2 text-xs text-amber-400/90">{loadError}</p>
            )}
            {!loadError && profiles.length === 0 && (
              <p className="mt-3 text-sm text-gray-500">
                No profiles yet. Session 14 will add fixture definitions and channel layouts.
              </p>
            )}
            {!loadError && profiles.length > 0 && (
              <ul className="mt-3 space-y-1 text-sm text-gray-300">
                {profiles.map((p, i) => (
                  <li key={p.id ?? i} className="font-mono text-xs">
                    {p.name ?? p.id ?? 'Unnamed'}
                  </li>
                ))}
              </ul>
            )}
          </div>

          <div className="rounded-2xl border border-gray-800 bg-gray-950/40 p-5">
            <h3 className="text-sm font-medium text-gray-300">Patch</h3>
            <p className="mt-3 text-sm text-gray-500">
              {patchCount === null && !loadError && 'Loading…'}
              {patchCount !== null && (
                <>
                  <span className="font-mono text-gray-300">{patchCount}</span> entr
                  {patchCount === 1 ? 'y' : 'ies'} in the patch table.
                </>
              )}
            </p>
            <p className="mt-2 text-xs text-gray-600">
              Universe and address assignment will be editable here once patching ships.
            </p>
          </div>
        </div>
      </div>
    </section>
  )
}
