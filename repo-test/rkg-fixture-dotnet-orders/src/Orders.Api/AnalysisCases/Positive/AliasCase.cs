using PurchaseOrder = Orders.Api.Domain.Order;
namespace Orders.Api.AnalysisCases.Positive;
public static class AliasCase
{
    public static PurchaseOrder Build() => PurchaseOrder.Create("fixture-customer");
}
