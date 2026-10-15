using Microsoft.EntityFrameworkCore;
using Orders.Api.Domain;
namespace Orders.Api.Persistence;

public sealed class OrdersDbContext(DbContextOptions<OrdersDbContext> options) : DbContext(options)
{
    public DbSet<Order> Orders => Set<Order>();
    public DbSet<OrderItem> OrderItems => Set<OrderItem>();
    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        // RKG_EXPECT: mapping-orders
        modelBuilder.Entity<Order>().ToTable("orders");
        modelBuilder.Entity<Order>().HasKey(order => order.Id);
        modelBuilder.Entity<Order>().Property(order => order.Status).HasConversion<string>();
        // RKG_EXPECT: mapping-order-items
        modelBuilder.Entity<OrderItem>().ToTable("order_items");
        modelBuilder.Entity<OrderItem>().HasKey(item => item.Id);
        modelBuilder.Entity<Order>().HasMany(order => order.Items).WithOne()
            .HasForeignKey(item => item.OrderId).OnDelete(DeleteBehavior.Cascade);
    }
}
