using Orders.Api.Domain;
namespace Orders.Api.Contracts;
public sealed record OrderResponse(Guid Id, string CustomerReference, OrderStatus Status,
    IReadOnlyList<OrderItemResponse> Items)
{
    public static OrderResponse From(Order order) => new(order.Id, order.CustomerReference,
        order.Status, order.Items.Select(item =>
            new OrderItemResponse(item.Sku, item.Quantity)).ToList());
}
public sealed record OrderItemResponse(string Sku, int Quantity);
