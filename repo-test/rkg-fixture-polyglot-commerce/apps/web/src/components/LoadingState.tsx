interface LoadingStateProps { label?: string }

export default function LoadingState({ label = 'Loading' }: LoadingStateProps) {
  return <p role="status">{label}…</p>;
}
