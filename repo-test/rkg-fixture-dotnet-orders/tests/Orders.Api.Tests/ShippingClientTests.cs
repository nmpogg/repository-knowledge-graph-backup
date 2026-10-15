using System.Net;
using Orders.Api.AnalysisCases.Negative;
using Orders.Api.Integrations;
namespace Orders.Api.Tests;

public sealed class ShippingClientTests
{
    private sealed class RecordingHandler : HttpMessageHandler
    {
        public Uri? Seen { get; private set; }
        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken token)
        {
            Seen = request.RequestUri;
            return Task.FromResult(new HttpResponseMessage(HttpStatusCode.OK));
        }
    }
    [Fact]
    public async Task Static_outbound_call_uses_fake_transport()
    {
        using var handler = new RecordingHandler();
        using var http = new HttpClient(handler);
        using var result = await new ShippingClient(http).GetReadinessAsync(default);
        Assert.Equal("https://shipping.example.invalid/health", handler.Seen!.AbsoluteUri);
        Assert.Equal(HttpStatusCode.OK, result.StatusCode);
    }
    [Fact]
    public async Task Dynamic_case_preserves_runtime_url_without_network()
    {
        using var handler = new RecordingHandler();
        using var http = new HttpClient(handler);
        var runtimeUri = new Uri("https://runtime.example.invalid/health");
        using var result = await new DynamicHttpClient(http).FetchAsync(runtimeUri, default);
        Assert.Equal(runtimeUri, handler.Seen);
    }
}
