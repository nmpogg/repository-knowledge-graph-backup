namespace Orders.Api.AnalysisCases.Negative;
public sealed class DynamicHttpClient(HttpClient http)
{
    // RKG_EXPECT: dynamic-url-unresolved
    public Task<HttpResponseMessage> FetchAsync(Uri runtimeUri, CancellationToken token) =>
        http.GetAsync(runtimeUri, token);
}
