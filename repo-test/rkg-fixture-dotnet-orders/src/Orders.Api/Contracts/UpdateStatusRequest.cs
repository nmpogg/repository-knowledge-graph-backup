using System.ComponentModel.DataAnnotations;
using Orders.Api.Domain;
namespace Orders.Api.Contracts;
public sealed record UpdateStatusRequest(
    [EnumDataType(typeof(OrderStatus))] OrderStatus Status);
