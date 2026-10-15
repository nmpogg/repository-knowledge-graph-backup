namespace Orders.Api.AnalysisCases.Negative;
public interface IPaymentGateway { string Charge(); }
public sealed class CardGateway : IPaymentGateway { public string Charge() => "card"; }
public sealed class WalletGateway : IPaymentGateway { public string Charge() => "wallet"; }
public static class AmbiguousDispatch
{
    // Neither implementation is registered in DI. Keep the interface target.
    public static string Invoke(IPaymentGateway gateway) => gateway.Charge();
}
