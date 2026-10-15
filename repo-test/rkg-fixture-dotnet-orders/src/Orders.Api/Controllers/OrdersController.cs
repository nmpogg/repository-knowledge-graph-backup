using Microsoft.AspNetCore.Mvc;
using Orders.Api.Application;
using Orders.Api.Contracts;
namespace Orders.Api.Controllers;

[ApiController]
[Route("api/orders")]
public sealed class OrdersController(OrderService service) : ControllerBase
{
    // RKG_EXPECT: endpoint-create
    [HttpPost]
    public async Task<ActionResult<OrderResponse>> Create(CreateOrderRequest request, CancellationToken token)
    {
        var order = await service.CreateAsync(request, token);
        return CreatedAtAction(nameof(Get), new { id = order.Id }, OrderResponse.From(order));
    }
    // RKG_EXPECT: endpoint-get
    [HttpGet("{id:guid}")]
    public async Task<ActionResult<OrderResponse>> Get(Guid id, CancellationToken token)
    {
        var order = await service.GetAsync(id, token);
        if (order is null) return NotFound();
        return OrderResponse.From(order);
    }
    // RKG_EXPECT: endpoint-list
    [HttpGet]
    public async Task<ActionResult<IReadOnlyList<OrderResponse>>> List(CancellationToken token) =>
        Ok((await service.ListAsync(token)).Select(OrderResponse.From).ToList());
    // RKG_EXPECT: endpoint-status
    [HttpPatch("{id:guid}/status")]
    public async Task<ActionResult<OrderResponse>> UpdateStatus(Guid id, UpdateStatusRequest request, CancellationToken token)
    {
        var order = await service.UpdateStatusAsync(id, request.Status, token);
        if (order is null) return NotFound();
        return OrderResponse.From(order);
    }
    // RKG_EXPECT: endpoint-delete
    [HttpDelete("{id:guid}")]
    public async Task<IActionResult> Delete(Guid id, CancellationToken token) =>
        await service.DeleteAsync(id, token) ? NoContent() : NotFound();
    // RKG_EXPECT: endpoint-readiness
    [HttpGet("readiness")]
    public IActionResult Readiness() => Ok();
}
