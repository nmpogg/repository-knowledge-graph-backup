using Orders.Api.Contracts;
using Orders.Api.Domain;
namespace Orders.Api.Application;

public sealed class OrderService
{
    private readonly IOrderRepository repository;
    public OrderService(IOrderRepository repository) => this.repository = repository;

    // RKG_EXPECT: service-create
    public async Task<Order> CreateAsync(CreateOrderRequest request, CancellationToken token)
    {
        var order = Order.Create(request.CustomerReference, request.Items.Select(item =>
            new OrderItem { Sku = item.Sku, Quantity = item.Quantity }));
        await repository.SaveAsync(order, token);
        return order;
    }
    public Task<Order?> GetAsync(Guid id, CancellationToken token) => repository.FindAsync(id, token);
    public Task<IReadOnlyList<Order>> ListAsync(CancellationToken token) => repository.ListAsync(token);
    public async Task<Order?> UpdateStatusAsync(Guid id, OrderStatus status, CancellationToken token)
    {
        var order = await repository.FindAsync(id, token);
        if (order is null) return null;
        order.Status = status;
        await repository.SaveAsync(order, token);
        return order;
    }
    public async Task<bool> DeleteAsync(Guid id, CancellationToken token)
    {
        var order = await repository.FindAsync(id, token);
        if (order is null) return false;
        await repository.DeleteAsync(order, token);
        return true;
    }
}
