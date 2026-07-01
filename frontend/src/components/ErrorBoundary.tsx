import { Component, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}
interface State {
  hasError: boolean
  message?: string
}

/**
 * Catches render errors in the page below it and shows a friendly fallback
 * instead of a white screen — the sidebar stays mounted and the rest of the
 * app keeps working. Place it around the routed <Outlet/> (see Layout.tsx).
 */
export default class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false }

  static getDerivedStateFromError(error: unknown): State {
    return {
      hasError: true,
      message: error instanceof Error ? error.message : String(error),
    }
  }

  componentDidCatch(error: unknown, info: unknown) {
    // eslint-disable-next-line no-console
    console.error('Page crashed:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="bg-white rounded-xl border border-[#C8BFA8] p-8 text-center">
          <h2 className="text-lg font-semibold text-[#B04030]">Something went wrong</h2>
          <p className="text-sm text-[#8A7A60] mt-2">
            This page hit an error. The rest of the app is still working.
          </p>
          {this.state.message && (
            <pre className="mt-3 text-xs text-left overflow-auto bg-[#F5F0E8] rounded p-3 text-[#5A4E3A] max-h-40">
              {this.state.message}
            </pre>
          )}
          <button
            onClick={() => this.setState({ hasError: false, message: undefined })}
            className="mt-4 px-4 py-2 bg-[#3A7010] text-white rounded-lg text-sm font-medium hover:bg-[#2D6010]"
          >
            Try again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}