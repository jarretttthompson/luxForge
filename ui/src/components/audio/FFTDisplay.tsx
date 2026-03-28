import { useEffect, useRef } from 'react'

import { useAudioStore } from '../../stores/audioStore'

/** Bar spectrum of downsampled FFT magnitudes from the engine WebSocket snapshot. */
export function FFTDisplay() {
  const fft = useAudioStore((s) => s.analysis.fft)
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    const draw = () => {
      const ctx = canvas.getContext('2d')
      if (!ctx) return

      const dpr = window.devicePixelRatio || 1
      const w = canvas.offsetWidth
      const h = canvas.offsetHeight
      if (w < 2 || h < 2) return

      canvas.width = Math.floor(w * dpr)
      canvas.height = Math.floor(h * dpr)
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

      ctx.fillStyle = '#030712'
      ctx.fillRect(0, 0, w, h)

      const bins = fft.length > 0 ? fft : [0]
      const maxVal = Math.max(...bins, 1e-9)
      const n = bins.length
      const gap = 1
      const barW = (w - gap * (n - 1)) / n

      for (let i = 0; i < n; i++) {
        const amp = Math.min(1, bins[i]! / maxVal)
        const bh = amp * h * 0.94
        const x = i * (barW + gap)
        const gradient = ctx.createLinearGradient(0, h, 0, h - bh)
        gradient.addColorStop(0, '#06b6d4')
        gradient.addColorStop(0.55, '#8b5cf6')
        gradient.addColorStop(1, '#c4b5fd')
        ctx.fillStyle = gradient
        ctx.fillRect(x, h - bh, Math.max(1, barW), bh)
      }
    }

    draw()

    const ro = new ResizeObserver(() => draw())
    ro.observe(canvas)
    return () => ro.disconnect()
  }, [fft])

  return (
    <div className="rounded-2xl border border-gray-800 bg-gray-950/60 p-4 shadow-inner shadow-black/30">
      <div className="mb-3 flex items-center justify-between">
        <h3 className="text-sm font-medium tracking-wide text-gray-300">Spectrum (FFT)</h3>
        <span className="text-xs text-gray-500">{fft.length} bins</span>
      </div>
      <canvas
        ref={canvasRef}
        className="h-36 w-full rounded-lg bg-gray-950"
        aria-label="FFT spectrum display"
        role="img"
      />
    </div>
  )
}
