namespace Orders.Api.Integrations;
public sealed class ShippingClient(HttpClient http)
{
    // RKG_EXPECT: shipping-static-url
    public Task<HttpResponseMessage> GetReadinessAsync(CancellationToken token) =>
        http.GetAsync("https://shipping.example.invalid/health", token);
}
