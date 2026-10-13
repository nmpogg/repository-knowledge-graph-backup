type Fetcher = (url: string) => Promise<unknown>

export function fetchDynamicURL(fetcher: Fetcher, origin: string, resource: string) {
  return fetcher(`${origin}/${resource}`)
}
