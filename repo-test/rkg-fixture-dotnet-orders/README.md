# rkg-fixture-dotnet-orders

Standalone C# fixture for demonstrating a **new language** in Repository Knowledge
Graph: C# language extraction, ASP.NET Core route extraction, then EF Core data
access extraction. This directory can be copied out as an independent repository.
It contains no RKG implementation. C# is not currently registered in RKG's built-in
adapters; `expected/` defines future demo targets, not current supported behavior.
The normative product requirements remain in the parent project's `.aide/`.

## Stack and commands

- .NET 10 / C# 14; `global.json` allows installed .NET 10 SDK feature bands.
- EF Core SQLite and ASP.NET Core test host: `10.0.12`.
- xUnit `2.9.3`, VSTest adapter `3.1.4`, test SDK `17.14.1`.
- Direct and transitive dependencies are pinned in both `packages.lock.json` files.
- Python 3.10+ is needed only for the source-only inventory validator.

From this directory, after installing .NET 10 SDK and Python:

```sh
./scripts/verify.sh
```

PowerShell equivalent:

```powershell
./scripts/verify.ps1
```

The scripts validate source pins, restore in locked mode, build Release with
warnings treated as errors, and run tests. First restore needs NuGet access;
subsequent runs can use the package cache. Tests use an in-process ASP.NET TestServer,
an in-memory SQLite database, and fake HTTP transports. They need no Docker,
external database, broker, listening application server, or outbound service access.
The VSTest runner itself needs permission to open its local communication socket.

Individual commands:

```sh
python3 scripts/validate-inventory.py
dotnet restore Orders.slnx --locked-mode
dotnet build Orders.slnx --no-restore --configuration Release
dotnet test Orders.slnx --no-build --no-restore --configuration Release
```

Optional explicit local startup, separate from indexing:

```sh
dotnet run --project src/Orders.Api --no-launch-profile
```

The application defaults to `http://127.0.0.1:5080`, creates an empty in-memory
database, and loses data on exit. It clears logging providers so it does not log
request payloads, configuration values, or raw database errors. The shipping client
is registered but is never invoked by the CRUD flow.

## Architecture

```text
OrdersController -> OrderService -> IOrderRepository
                                       ^ implements
                                 EfOrderRepository -> OrdersDbContext
                                                         | orders
                                                         | order_items

ShippingClient -> https://shipping.example.invalid/health  (separate unused integration)
```

Constructor dependencies are distinct from call sites. A call through
`IOrderRepository` targets the interface member in the required language inventory.
The concrete registration in `Bootstrap/ServiceRegistration.cs` is additional DI
evidence; it does not authorize guessing arbitrary concrete dispatch targets.

```text
src/Orders.Api/
  Program.cs                 explicit startup
  Bootstrap/                 dependency registration
  Controllers/               six REST endpoints
  Contracts/                 request/response records and validation
  Application/               service and repository interface
  Domain/                    order, items, status and factory overloads
  Persistence/               EF mapping and repository
  Integrations/              literal outbound HTTP call
  AnalysisCases/             valid positive and negative C# samples
analysis-cases/negative/      inert malformed source, sentinel, unknown extension
tests/Orders.Api.Tests/       CRUD, validation, persistence and fake-HTTP tests
expected/                    source-backed target subset and demo questions
scripts/                     verification and inventory validation
```

## Endpoints

| Method | Attribute template | Canonical demo path | Handler |
|---|---|---|---|
| POST | `api/orders` | `/api/orders` | `OrdersController.Create` |
| GET | `api/orders/{id:guid}` | `/api/orders/{id}` | `OrdersController.Get` |
| GET | `api/orders` | `/api/orders` | `OrdersController.List` |
| PATCH | `api/orders/{id:guid}/status` | `/api/orders/{id}/status` | `OrdersController.UpdateStatus` |
| DELETE | `api/orders/{id:guid}` | `/api/orders/{id}` | `OrdersController.Delete` |
| GET | `api/orders/readiness` | `/api/orders/readiness` | `OrdersController.Readiness` |

POST returns 201 and a Location header; missing orders return 404; successful DELETE
returns 204. Validation rejects empty customer/SKU/items, quantities outside 1–100,
and unknown enum values. Route constraints must remain available as metadata even
when canonical path normalization removes `:guid`. Method is part of endpoint identity.

`OrdersDbContext.OnModelCreating` explicitly maps `Order` to `orders` and `OrderItem`
to `order_items`. The resource context is this application and DbContext, not just
the unqualified table name. SQLite does not provide separate relational schemas.
`Include(order => order.Items)` is explicit read evidence for both resources.
Item writes via graph-add and cascade-delete are **optional** until an adapter
implements and reviews those EF rules; `SaveChangesAsync` alone does not prove
access to every mapped table.

## Demo sequence

1. **Baseline:** register the fixture directory in RKG and index using only existing
   adapters. Capture actual unsupported-file/capability behavior. Do not claim C#
   types, routes or database facts were extracted. Baseline indexing has not been
   executed as part of creating this fixture.
2. **C# language:** add a parser-backed language adapter through RKG's adapter
   contract/registry. Check types, signature-qualified methods, interfaces,
   `implements`, aliases, and statically resolvable calls in the language subset.
3. **ASP.NET Core:** add framework extraction for controller attributes, route
   composition, route constraints, handler links, constructor dependencies and the
   explicit literal HTTP dependency.
4. **EF Core:** add mapping and reads/writes for the reviewed explicit patterns.
5. Compare graph output with the relevant `stage` in `expected/`. Ask the ten
   questions in `expected/questions.json`, including ambiguity and absence cases.

The analyzer must only read source: no `dotnet restore`, build, import, test, or
application execution as part of indexing. Native verification commands above are
explicit fixture-author checks run separately. Ignore `**/bin/**`, `**/obj/**` and
`**/TestResults/**` in the RKG scan as well as Git; they contain generated C# and
large dependency trees after a local build. For the application-only demo use
`src/Orders.Api` as the source root. For negative-file diagnostics, scan the whole
fixture with those ignores and report test code as a separate source scope.

## Negative cases

- Three `OrderService` types in different namespaces must remain distinct.
- `Order.Create(string)` and `Order.Create(string, IEnumerable<OrderItem>)` must
  retain signature identity. The alias sample calls only the first overload.
- `IPaymentGateway` has two implementations, neither registered in DI. Preserve
  the interface call in `AmbiguousDispatch.Invoke`; no unique concrete target.
- `DynamicHttpClient` accepts a runtime URI. Do not invent a host or endpoint link.
- `[NonController] UnregisteredHandler` has an HTTP attribute but exposes no route.
- `syntax-error.cs.fixture` is inert and excluded from build. In a disposable copy,
  rename only that file to `.cs` to test parser recovery; normal source still parses.
- `unsupported.rkgunknown` has no language adapter.
- The fake secret sentinel in the inert text fixture must not appear in graph,
  analyzer reports, or logs. Only the literal URL in `ShippingClient` is a static
  external target; fake HTTP URLs in tests must not be mixed into the app inventory.

## Expected inventory and maintenance

See `expected/README.md`. The subset contains 44 target entities, 36 required edges,
two optional cascade edges, and ten manual chatbot questions. It intentionally does
not enumerate every source unit, constructor, framework method or test helper.

`validate-inventory.py` checks semantic references, endpoint identities, evidence
line hashes, source/build file hashes and dependency pins. It reads source only.
Passing it proves consistency with pinned files, not that RKG supports C# or that
an independent reviewer has approved the semantic expectations.

After an intentional fixture change, review facts/questions and evidence locations
first, then update `expected/source-manifest.json` using SHA-256 of file bytes.
Do not update hashes to conceal an unexpected semantic change. Fixtures and this
expected inventory are non-normative and do not promote an adapter support status.
