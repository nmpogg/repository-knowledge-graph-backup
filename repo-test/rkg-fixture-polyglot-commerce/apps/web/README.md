# Web application
React/TypeScript order UI: list, create, detail and status edit. DTOs, HTTP methods and paths match the Spring contract. `src/main.tsx` is the browser entrypoint; `OrderApi` delegates to an injected client. Importing client modules never performs an HTTP request.

Install `npm ci`, then run `npm run lint`, `npm test`, `npm run typecheck`, `npm run build`. Tests use jsdom and injected/mocked clients, with no backend or network. `package-lock.json` pins dependencies. Malformed root analysis fixtures are outside the app's compiler and lint roots.

`src/analysis-cases` retains dynamic URL, ambiguous binding and shadowed-fetch cases. Dynamic paths are not static endpoint links. Runtime uses relative `/api` requests; deployment must route them to the Spring service. No server is started by verification.
