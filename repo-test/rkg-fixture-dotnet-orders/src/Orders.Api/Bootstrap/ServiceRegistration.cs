using Microsoft.Data.Sqlite;
using Microsoft.EntityFrameworkCore;
using Orders.Api.Application;
using Orders.Api.Integrations;
using Orders.Api.Persistence;

namespace Orders.Api.Bootstrap;

public static class ServiceRegistration
{
    public static IServiceCollection AddOrderApplication(this IServiceCollection services)
    {
        // The connection is opened only when the application explicitly starts.
        services.AddSingleton(_ =>
        {
            var connection = new SqliteConnection("Data Source=:memory:");
            connection.Open();
            return connection;
        });
        services.AddDbContext<OrdersDbContext>((provider, options) =>
            options.UseSqlite(provider.GetRequiredService<SqliteConnection>()));
        services.AddScoped<IOrderRepository, EfOrderRepository>();
        services.AddScoped<OrderService>();
        // Registered, but never contacted by the default CRUD flow.
        services.AddHttpClient<ShippingClient>();
        services.AddControllers();
        return services;
    }
}
