// Expected: do not infer a call edge because the binding is reassigned to one of two targets.
const sendPrimary = () => 'primary';
const sendFallback = () => 'fallback';

export function callAmbiguous(useFallback: boolean): string {
  let send = sendPrimary;
  if (useFallback) send = sendFallback;
  return send();
}
