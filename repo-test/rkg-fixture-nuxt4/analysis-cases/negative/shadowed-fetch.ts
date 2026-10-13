export async function shadowedFetch() {
  const $fetch = (value: string) => Promise.resolve(`local:${value}`)
  return $fetch('/api/not-an-http-call')
}
