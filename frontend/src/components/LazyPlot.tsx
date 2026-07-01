import { lazy, Suspense } from 'react'

// Lazy-load react-plotly.js (and its plotly.js dependency) so the ~3.5 MB
// charting bundle is fetched only when a chart actually renders, instead of
// being eagerly bundled into every page. Combined with route-level
// React.lazy() and the vite manualChunks split, this keeps the initial
// bundle small and makes plotly a dedicated, cacheable on-demand chunk.
const Plot = lazy(() => import('react-plotly.js'))

export default function LazyPlot(props: Record<string, any>) {
  const { style, ...rest } = props
  return (
    <Suspense
      fallback={
        <div
          className="h-full w-full animate-pulse rounded bg-gray-100"
          style={style}
          aria-label="Loading chart…"
        />
      }
    >
      <Plot {...(rest as any)} style={style} />
    </Suspense>
  )
}