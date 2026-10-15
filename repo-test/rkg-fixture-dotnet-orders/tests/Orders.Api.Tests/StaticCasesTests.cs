using Orders.Api.AnalysisCases.Negative;
using Orders.Api.AnalysisCases.Positive;
using Orders.Api.Domain;
namespace Orders.Api.Tests;

public sealed class StaticCasesTests
{
    [Fact]
    public void Overloads_alias_and_namespace_collisions_keep_their_meaning()
    {
        Assert.Empty(Order.Create("first").Items);
        Assert.Single(Order.Create("second", [new OrderItem { Sku = "sku", Quantity = 1 }]).Items);
        Assert.Equal("fixture-customer", AliasCase.Build().CustomerReference);
        Assert.Equal("sales", new AnalysisCases.Negative.Sales.OrderService().Describe());
        Assert.Equal("audit", new AnalysisCases.Negative.Audit.OrderService().Describe());
        Assert.Equal("card", AmbiguousDispatch.Invoke(new CardGateway()));
        Assert.Equal("wallet", AmbiguousDispatch.Invoke(new WalletGateway()));
    }
}
