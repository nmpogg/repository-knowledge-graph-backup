// Expected: do not infer an external origin from a URL assembled from runtime input.
export async function loadTenantResource(host: string): Promise<Response> {
  return fetch(`https://${host}/tenant-resource`);
}
