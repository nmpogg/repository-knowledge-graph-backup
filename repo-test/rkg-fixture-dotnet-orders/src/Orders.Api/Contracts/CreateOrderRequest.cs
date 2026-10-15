using System.ComponentModel.DataAnnotations;
namespace Orders.Api.Contracts;
public sealed record CreateOrderRequest(
    [Required, MinLength(1)] string CustomerReference,
    [Required, MinLength(1)] List<OrderItemRequest> Items);
public sealed record OrderItemRequest(
    [Required, MinLength(1)] string Sku,
    [Range(1, 100)] int Quantity);
