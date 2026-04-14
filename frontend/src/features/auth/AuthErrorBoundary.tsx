import React from 'react'

import AuthErrorMessage from './AuthErrorMessage'
import { getAuthErrorDescriptor } from './authErrorHandler'

interface AuthErrorBoundaryProps {
  children: React.ReactNode
}

interface AuthErrorBoundaryState {
  error: Error | null
}

export default class AuthErrorBoundary extends React.Component<
  AuthErrorBoundaryProps,
  AuthErrorBoundaryState
> {
  state: AuthErrorBoundaryState = {
    error: null,
  }

  static getDerivedStateFromError(error: Error): AuthErrorBoundaryState {
    return { error }
  }

  componentDidCatch(error: Error) {
    console.error('AuthErrorBoundary caught an auth-related render error', error)
  }

  private readonly handleRetry = () => {
    this.setState({ error: null })
  }

  render() {
    if (this.state.error) {
      return (
        <div style={{ padding: 24 }}>
          <AuthErrorMessage
            descriptor={getAuthErrorDescriptor(this.state.error)}
            onRetry={this.handleRetry}
            testId="auth-error-boundary"
          />
        </div>
      )
    }

    return this.props.children
  }
}
