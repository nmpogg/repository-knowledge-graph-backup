namespace Orders.Api.Domain;

public sealed class Order
{
    public Guid Id { get; set; }
    public string CustomerReference { get; set; } = string.Empty;
    public OrderStatus Status { get; set; } = OrderStatus.Pending;
    public List<OrderItem> Items { get; set; } = [];

    // RKG_EXPECT: order-create-reference
    public static Order Create(string customerReference) =>
        new() { Id = Guid.NewGuid(), CustomerReference = customerReference };

    // RKG_EXPECT: order-create-items
    public static Order Create(string customerReference, IEnumerable<OrderItem> items)
    {
        var order = Create(customerReference);
        order.Items = items.ToList();
        return order;
    }
}
