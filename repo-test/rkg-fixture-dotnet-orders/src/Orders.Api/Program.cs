using Orders.Api.Bootstrap;
using Orders.Api.Persistence;

var builder = WebApplication.CreateBuilder(args);
builder.WebHost.UseUrls("http://127.0.0.1:5080");
builder.Logging.ClearProviders();
builder.Services.AddOrderApplication();
var app = builder.Build();
using (var scope = app.Services.CreateScope())
{
    scope.ServiceProvider.GetRequiredService<OrdersDbContext>().Database.EnsureCreated();
}
app.MapControllers();
app.Run();

public partial class Program { }
