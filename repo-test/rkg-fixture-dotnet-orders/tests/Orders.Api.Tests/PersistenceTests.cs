using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Orders.Api.Domain;
using Orders.Api.Persistence;
namespace Orders.Api.Tests;

public sealed class PersistenceTests
{
    [Fact]
    public async Task Repository_roundtrip_uses_tables_and_deletes_items()
    {
        await using var connection = new SqliteConnection("Data Source=:memory:");
        await connection.OpenAsync();
        var options = new DbContextOptionsBuilder<OrdersDbContext>().UseSqlite(connection).Options;
        await using var db = new OrdersDbContext(options);
        await db.Database.EnsureCreatedAsync();
        Assert.Equal("orders", db.Model.FindEntityType(typeof(Order))!.GetTableName());
        Assert.Equal("order_items", db.Model.FindEntityType(typeof(OrderItem))!.GetTableName());
        var repository = new EfOrderRepository(db);
        var order = Order.Create("customer", [new OrderItem { Sku = "SKU-1", Quantity = 2 }]);
        await repository.SaveAsync(order, default);
        db.ChangeTracker.Clear();
        var restored = (await repository.FindAsync(order.Id, default))!;
        Assert.Equal(2, Assert.Single(restored.Items).Quantity);
        await repository.DeleteAsync(restored, default);
        db.ChangeTracker.Clear();
        Assert.Equal(0, await db.Orders.CountAsync());
        Assert.Equal(0, await db.OrderItems.CountAsync());
    }
}
