import { useState } from 'react'

import { MappingEditor } from '../components/mapping/MappingEditor'
import { MappingList } from '../components/mapping/MappingList'
import { useMappingStore } from '../stores/mappingStore'
import type { MappingRule } from '../types/api'

export function MappingPage() {
  const rules = useMappingStore((s) => s.rules)
  const [selectedId, setSelectedId] = useState<string | undefined>(undefined)
  const [isCreating, setIsCreating] = useState(false)

  const selectedRule = rules.find((r) => r.id === selectedId)
  const editorOpen = isCreating || selectedId !== undefined

  function handleNew() {
    setSelectedId(undefined)
    setIsCreating(true)
  }

  function handleSelect(id: string) {
    setIsCreating(false)
    setSelectedId(id)
  }

  function handleClose() {
    setIsCreating(false)
    setSelectedId(undefined)
  }

  function handleSaved(rule: MappingRule) {
    setIsCreating(false)
    setSelectedId(rule.id)
  }

  return (
    <section className="rounded-3xl border border-gray-800 bg-gray-900/70 shadow-2xl shadow-black/20 overflow-hidden">
      <div className="border-b border-gray-800 px-8 py-6">
        <h2 className="text-3xl font-semibold text-gray-100">Mapping</h2>
        <p className="mt-1 text-sm text-gray-400">
          Route audio parameters to lighting console outputs through transform chains.
        </p>
      </div>

      <div className="flex min-h-[540px]">
        {/* List panel */}
        <div
          className={[
            'flex-shrink-0 border-r border-gray-800 transition-all',
            editorOpen ? 'w-72 lg:w-80' : 'w-full',
            editorOpen ? 'hidden sm:flex sm:flex-col' : 'flex flex-col',
          ].join(' ')}
        >
          <MappingList
            selectedId={selectedId}
            onSelect={handleSelect}
            onNew={handleNew}
          />
        </div>

        {/* Editor panel */}
        {editorOpen && (
          <div className="flex flex-1 flex-col min-w-0">
            <MappingEditor
              key={selectedId ?? 'new'}
              rule={selectedRule}
              onClose={handleClose}
              onSaved={handleSaved}
            />
          </div>
        )}

        {/* Empty state when no editor open on wider screens */}
        {!editorOpen && (
          <div className="hidden lg:flex flex-1 items-center justify-center border-l border-gray-800 py-16 text-center">
            <div>
              <p className="text-sm text-gray-500">Select a rule to edit, or create a new one.</p>
            </div>
          </div>
        )}
      </div>
    </section>
  )
}
