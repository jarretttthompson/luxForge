/** Controlled <select> for audio input or console output parameters. */
export interface ParameterInfo {
  name: string
  display_name: string
}

interface Props {
  value: string
  onChange: (value: string) => void
  params: ParameterInfo[]
  isLoading?: boolean
  placeholder?: string
  id?: string
  disabled?: boolean
  className?: string
}

export function ParameterPicker({
  value,
  onChange,
  params,
  isLoading = false,
  placeholder = 'Select parameter…',
  id,
  disabled,
  className = '',
}: Props) {
  return (
    <select
      id={id}
      value={value}
      disabled={disabled || isLoading}
      onChange={(e) => onChange(e.target.value)}
      className={[
        'w-full rounded-lg border border-gray-700 bg-gray-800 px-3 py-2 text-sm text-gray-100',
        'focus:border-cyan-500/50 focus:outline-none focus:ring-2 focus:ring-cyan-500/30',
        'disabled:cursor-not-allowed disabled:opacity-50',
        className,
      ].join(' ')}
    >
      <option value="" disabled>
        {isLoading ? 'Loading…' : placeholder}
      </option>
      {params.map((p) => (
        <option key={p.name} value={p.name}>
          {p.display_name || p.name}
        </option>
      ))}
    </select>
  )
}
