import { Component, type ErrorInfo, type ReactNode } from 'react';
import { RouterProvider } from 'react-router-dom';
import { router } from './router';

interface BoundaryState { failed: boolean }

export class AppErrorBoundary extends Component<{ children: ReactNode }, BoundaryState> {
  state: BoundaryState = { failed: false };
  static getDerivedStateFromError(): BoundaryState { return { failed: true }; }
  componentDidCatch(error: Error, info: ErrorInfo) { console.error('Application render failed', error.name, info.componentStack); }
  render() { return this.state.failed ? <p role="alert">Something went wrong.</p> : this.props.children; }
}

export default function App() {
  return <AppErrorBoundary><RouterProvider router={router} /></AppErrorBoundary>;
}
