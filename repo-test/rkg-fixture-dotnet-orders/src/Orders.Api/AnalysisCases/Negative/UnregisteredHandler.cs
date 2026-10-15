using Microsoft.AspNetCore.Mvc;
namespace Orders.Api.AnalysisCases.Negative;
[NonController]
public sealed class UnregisteredHandler
{
    [HttpGet("api/ghost-orders")]
    public string Get() => "not-an-endpoint";
}
