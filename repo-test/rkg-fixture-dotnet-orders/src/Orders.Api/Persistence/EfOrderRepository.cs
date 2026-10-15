using Microsoft.EntityFrameworkCore;
using Orders.Api.Application;
using Orders.Api.Domain;
namespace Orders.Api.Persistence;

public sealed class EfOrderRepository(OrdersDbContext db) : IOrderRepository
{
    // RKG_EXPECT: repository-find
    public Task<Order?> FindAsync(Guid id, CancellationToken token) =>
        db.Orders.Include(order => order.Items).SingleOrDefaultAsync(order => order.Id == id, token);
    public async Task<IReadOnlyList<Order>> ListAsync(CancellationToken token) =>
        await db.Orders.Include(order => order.Items).OrderBy(order => order.CustomerReference).ToListAsync(token);
    // RKG_EXPECT: repository-save
    public async Task SaveAsync(Order order, CancellationToken token)
    {
        if (db.Entry(order).State == EntityState.Detached) db.Orders.Add(order);
        await db.SaveChangesAsync(token);
    }
    public async Task DeleteAsync(Order order, CancellationToken token)
    {
        db.Orders.Remove(order);
        await db.SaveChangesAsync(token);
    }
}
