using System.Net;
using System.Net.Http.Json;
using Microsoft.AspNetCore.Mvc.Testing;
using Orders.Api.Contracts;
using Orders.Api.Domain;

namespace Orders.Api.Tests;

public sealed class OrdersApiTests
{
    private static CreateOrderRequest Request() => new("fixture-customer", [new("SKU-1", 2)]);

    [Fact]
    public async Task Crud_flow_persists_items_updates_status_and_cascades_delete()
    {
        await using var factory = new WebApplicationFactory<Program>();
        using var client = factory.CreateClient();
        using var created = await client.PostAsJsonAsync("/api/orders", Request());
        Assert.Equal(HttpStatusCode.Created, created.StatusCode);
        var order = (await created.Content.ReadFromJsonAsync<OrderResponse>())!;
        Assert.NotEqual(Guid.Empty, order.Id);
        Assert.Equal("SKU-1", Assert.Single(order.Items).Sku);
        Assert.Equal(2, order.Items[0].Quantity);
        Assert.Equal($"/api/orders/{order.Id}", created.Headers.Location!.AbsolutePath);
        var read = (await client.GetFromJsonAsync<OrderResponse>($"/api/orders/{order.Id}"))!;
        Assert.Equal(OrderStatus.Pending, read.Status);
        var list = (await client.GetFromJsonAsync<List<OrderResponse>>("/api/orders"))!;
        Assert.Equal(order.Id, Assert.Single(list).Id);
        using var patched = await client.PatchAsJsonAsync($"/api/orders/{order.Id}/status",
            new UpdateStatusRequest(OrderStatus.Confirmed));
        Assert.Equal(HttpStatusCode.OK, patched.StatusCode);
        var updated = (await client.GetFromJsonAsync<OrderResponse>($"/api/orders/{order.Id}"))!;
        Assert.Equal(OrderStatus.Confirmed, updated.Status);
        using var deleted = await client.DeleteAsync($"/api/orders/{order.Id}");
        Assert.Equal(HttpStatusCode.NoContent, deleted.StatusCode);
        using var missing = await client.GetAsync($"/api/orders/{order.Id}");
        Assert.Equal(HttpStatusCode.NotFound, missing.StatusCode);
        Assert.Empty((await client.GetFromJsonAsync<List<OrderResponse>>("/api/orders"))!);
    }

    [Fact]
    public async Task Unknown_order_returns_not_found_for_read_update_and_delete()
    {
        await using var factory = new WebApplicationFactory<Program>();
        using var client = factory.CreateClient();
        var path = $"/api/orders/{Guid.Empty}";
        using var read = await client.GetAsync(path);
        using var update = await client.PatchAsJsonAsync(path + "/status", new UpdateStatusRequest(OrderStatus.Confirmed));
        using var delete = await client.DeleteAsync(path);
        Assert.Equal(HttpStatusCode.NotFound, read.StatusCode);
        Assert.Equal(HttpStatusCode.NotFound, update.StatusCode);
        Assert.Equal(HttpStatusCode.NotFound, delete.StatusCode);
    }

    [Theory]
    [InlineData("", "SKU-1", 1)]
    [InlineData("customer", "", 1)]
    [InlineData("customer", "SKU-1", 0)]
    [InlineData("customer", "SKU-1", 101)]
    public async Task Invalid_input_is_rejected(string customer, string sku, int quantity)
    {
        await using var factory = new WebApplicationFactory<Program>();
        using var client = factory.CreateClient();
        using var response = await client.PostAsJsonAsync("/api/orders",
            new CreateOrderRequest(customer, [new(sku, quantity)]));
        Assert.Equal(HttpStatusCode.BadRequest, response.StatusCode);
        Assert.Empty((await client.GetFromJsonAsync<List<OrderResponse>>("/api/orders"))!);
    }

    [Fact]
    public async Task Empty_items_and_invalid_status_are_rejected()
    {
        await using var factory = new WebApplicationFactory<Program>();
        using var client = factory.CreateClient();
        using var invalid = await client.PostAsJsonAsync("/api/orders", new CreateOrderRequest("customer", []));
        Assert.Equal(HttpStatusCode.BadRequest, invalid.StatusCode);
        using var created = await client.PostAsJsonAsync("/api/orders", Request());
        var order = (await created.Content.ReadFromJsonAsync<OrderResponse>())!;
        using var update = await client.PatchAsJsonAsync($"/api/orders/{order.Id}/status",
            new UpdateStatusRequest((OrderStatus)999));
        Assert.Equal(HttpStatusCode.BadRequest, update.StatusCode);
    }

    [Fact]
    public async Task Readiness_is_literal_route_and_noncontroller_is_not_exposed()
    {
        await using var factory = new WebApplicationFactory<Program>();
        using var client = factory.CreateClient();
        using var readiness = await client.GetAsync("/api/orders/readiness");
        using var ghost = await client.GetAsync("/api/ghost-orders");
        Assert.Equal(HttpStatusCode.OK, readiness.StatusCode);
        Assert.Equal(HttpStatusCode.NotFound, ghost.StatusCode);
    }
}
