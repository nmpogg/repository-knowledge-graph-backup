import type {
  DependencyItem,
  DiagnosticItem,
  EntityDetail,
  EntitySummary,
  GraphEdge,
  GraphNode,
  IndexJob,
  Repository,
  Snapshot,
  TechnologyDetection,
} from '../../types/api'

/** Sample local FastAPI-ish service a new teammate can explore immediately. */
export const DEMO_REPO_ID = 'repo-orders-demo'
export const DEMO_SNAPSHOT_ID = 'snap-orders-001'
export const DEMO_JOB_ID = 'job-orders-001'

/** Mock conversation pins — drives `snapshot_in_use` / `repository_in_use` guards. */
export const seedConversationSnapshotRefs = new Set<string>(['snap-orders-000'])

export const seedRepositories: Repository[] = [
  {
    repository_id: DEMO_REPO_ID,
    revision: 3,
    display_name: 'API đơn hàng (demo)',
    source_type: 'local',
    source_locator_redacted: '~/projects/orders-api',
    source_root: '.',
    app_module: 'app.main',
    app_symbol: 'app',
    scan_defaults: {
      include_globs: ['**/*.py'],
      exclude_globs: ['**/tests/**', '**/.venv/**'],
      max_files: 5000,
    },
    active_snapshot_id: DEMO_SNAPSHOT_ID,
    created_at: '2026-09-20T08:00:00Z',
    updated_at: '2026-09-23T14:30:00Z',
  },
]

export const seedSnapshots: Snapshot[] = [
  {
    snapshot_id: DEMO_SNAPSHOT_ID,
    repository_id: DEMO_REPO_ID,
    source_revision: 'manifest:a1b2c3d4e5f6789012345678abcdef0123456789abcdef0123456789abcd',
    manifest_hash: 'sha256:deadbeefcafe00112233445566778899aabbccddeeff0011223344556677',
    scan_config_digest: 'sha256:scancfg00112233445566778899aabbcc',
    analyzer_version: '0.1.0-m0',
    schema_version: 'graph-1',
    adapter_versions: {
      fastapi: '0.1.0',
      sqlalchemy: '0.1.0',
      aiokafka: '0.1.0',
    },
    status: 'ready',
    metrics: {
      entity_count: 12,
      edge_count: 14,
      warning_count: 1,
    },
    capabilities: {
      technologies: ['fastapi', 'sqlalchemy', 'aiokafka'],
      graph_ready: true,
    },
    created_at: '2026-09-23T14:28:00Z',
    is_active: true,
  },
  {
    snapshot_id: 'snap-orders-000',
    repository_id: DEMO_REPO_ID,
    source_revision: 'manifest:0000111122223333444455556666777788889999aaaabbbbccccddddeeee',
    manifest_hash: 'sha256:prev00112233445566778899aabbccddeeff00112233445566778899aa',
    scan_config_digest: 'sha256:scancfg-prev0011223344556677',
    analyzer_version: '0.1.0-m0',
    schema_version: 'graph-1',
    adapter_versions: { fastapi: '0.1.0' },
    status: 'ready',
    metrics: {
      entity_count: 8,
      edge_count: 7,
      warning_count: 0,
    },
    capabilities: {
      technologies: ['fastapi'],
      graph_ready: true,
    },
    created_at: '2026-09-21T10:00:00Z',
    is_active: false,
  },
]

export const seedEntities: EntitySummary[] = [
  {
    id: 'ent-endpoint-get-order',
    type: 'endpoint',
    name: 'GET /orders/{id}',
    qualified_name: 'app.api.orders:get_order',
    summary: 'Fetch a single order by ID',
    attributes: { method: 'GET', path: '/orders/{id}' },
  },
  {
    id: 'ent-fn-get-order',
    type: 'function',
    name: 'get_order',
    qualified_name: 'app.api.orders:get_order',
    summary: 'Handler for order detail',
  },
  {
    id: 'ent-fn-load-order',
    type: 'function',
    name: 'load_order',
    qualified_name: 'app.services.orders:load_order',
    summary: 'Service layer load',
  },
  {
    id: 'ent-method-order-repo',
    type: 'function',
    name: 'load',
    qualified_name: 'app.repositories.orders:OrderRepository.load',
    summary: 'Read and update an order',
  },
  {
    id: 'ent-class-order-repo',
    type: 'class',
    name: 'OrderRepository',
    qualified_name: 'app.repositories.orders:OrderRepository',
    summary: 'SQLAlchemy repository',
  },
  {
    id: 'ent-table-orders',
    type: 'table',
    name: 'orders',
    qualified_name: 'db.tables:orders',
    summary: 'Orders table',
  },
  {
    id: 'ent-topic-order-events',
    type: 'topic',
    name: 'order.events',
    qualified_name: 'kafka.topics:order.events',
    summary: 'Order domain events',
  },
  {
    id: 'ent-fn-publish-order',
    type: 'function',
    name: 'publish_order_event',
    qualified_name: 'app.messaging:publish_order_event',
    summary: 'Publishes order.events',
  },
  {
    id: 'ent-fn-consume-order',
    type: 'function',
    name: 'handle_order_event',
    qualified_name: 'app.workers:handle_order_event',
    summary: 'Consumes order.events',
  },
  {
    id: 'ent-config-db-url',
    type: 'config',
    name: 'DATABASE_URL',
    qualified_name: 'app.settings:DATABASE_URL',
    summary: 'DB connection setting',
  },
  {
    id: 'ent-iface-order-store',
    type: 'interface',
    name: 'OrderStore',
    qualified_name: 'app.ports:OrderStore',
    summary: 'Persistence port',
  },
  {
    id: 'ent-module-main',
    type: 'module',
    name: 'main',
    qualified_name: 'app.main',
    summary: 'FastAPI application module',
  },
  {
    id: 'ent-class-app',
    type: 'class',
    name: 'app',
    qualified_name: 'app.main:app',
    summary: 'FastAPI instance',
  },
]

export const seedEntityDetails: Record<string, EntityDetail> = Object.fromEntries(
  seedEntities.map((e) => [
    e.id,
    {
      ...e,
      snapshot_id: DEMO_SNAPSHOT_ID,
      file_path: pathFor(e.id),
      start_line: lineFor(e.id),
      end_line: lineFor(e.id) + 8,
      evidence: [
        {
          relative_path: pathFor(e.id),
          start_line: lineFor(e.id),
          end_line: lineFor(e.id) + 8,
          excerpt: `# ${e.name}`,
        },
      ],
      metadata: {
        language: 'python',
        kind: e.type,
        ...(e.attributes ?? {}),
      },
    },
  ]),
)

export const seedGraphNodes: GraphNode[] = seedEntities.map((e) => ({
  id: e.id,
  type: e.type,
  label: e.name,
  qualified_name: e.qualified_name,
  file_path: pathFor(e.id),
}))

export const seedGraphEdges: GraphEdge[] = [
  {
    id: 'e1',
    source: 'ent-endpoint-get-order',
    target: 'ent-fn-get-order',
    type: 'handled_by',
    label: 'handled_by',
  },
  {
    id: 'e2',
    source: 'ent-fn-get-order',
    target: 'ent-fn-load-order',
    type: 'calls',
    label: 'calls',
  },
  {
    id: 'e3',
    source: 'ent-fn-load-order',
    target: 'ent-method-order-repo',
    type: 'calls',
    label: 'calls',
  },
  {
    id: 'e4',
    source: 'ent-method-order-repo',
    target: 'ent-table-orders',
    type: 'reads',
    label: 'reads',
  },
  {
    id: 'e5',
    source: 'ent-method-order-repo',
    target: 'ent-table-orders',
    type: 'writes',
    label: 'writes',
  },
  {
    id: 'e6',
    source: 'ent-fn-publish-order',
    target: 'ent-topic-order-events',
    type: 'publishes',
    label: 'publishes',
  },
  {
    id: 'e7',
    source: 'ent-fn-consume-order',
    target: 'ent-topic-order-events',
    type: 'consumes',
    label: 'consumes',
  },
  {
    id: 'e8',
    source: 'ent-method-order-repo',
    target: 'ent-config-db-url',
    type: 'depends_on',
    label: 'depends_on',
  },
  {
    id: 'e9',
    source: 'ent-class-order-repo',
    target: 'ent-iface-order-store',
    type: 'implements',
    label: 'implements',
  },
  {
    id: 'e10',
    source: 'ent-fn-load-order',
    target: 'ent-fn-publish-order',
    type: 'calls',
    label: 'calls',
  },
  {
    id: 'e11',
    source: 'ent-module-main',
    target: 'ent-class-app',
    type: 'depends_on',
    label: 'depends_on',
  },
  {
    id: 'e12',
    source: 'ent-class-app',
    target: 'ent-endpoint-get-order',
    type: 'depends_on',
    label: 'depends_on',
  },
  {
    id: 'e13', source: 'ent-class-order-repo', target: 'ent-method-order-repo',
    type: 'contains', label: 'contains',
  },
]

export const seedTechnologies: TechnologyDetection[] = [
  {
    technology: 'fastapi',
    version: '0.115.0',
    support_state: 'supported_patterns',
    evidence: [{ relative_path: 'app/main.py', start_line: 12 }],
    limitations: [],
  },
  {
    technology: 'sqlalchemy',
    version: '2.0.36',
    support_state: 'supported_patterns',
    evidence: [{ relative_path: 'app/db.py', start_line: 8 }],
    limitations: [],
  },
  {
    technology: 'aiokafka',
    version: '0.12.0',
    support_state: 'version_unverified',
    evidence: [{ relative_path: 'app/messaging.py', start_line: 4 }],
    limitations: ['Version pin not verified against adapter matrix'],
  },
  {
    technology: 'celery',
    version: null,
    support_state: 'detected_only',
    evidence: [{ relative_path: 'pyproject.toml', start_line: 22 }],
    limitations: ['Detected in inventory only — no adapter patterns applied'],
  },
  {
    technology: 'django',
    version: '3.2.0',
    support_state: 'unsupported_version',
    evidence: [{ relative_path: 'legacy/notes.md', start_line: 3 }],
    limitations: ['Unsupported major version — ignored for graph extraction'],
  },
]

export const seedDependencies: DependencyItem[] = [
  {
    id: 'dep-fastapi',
    name: 'fastapi',
    version: '0.115.0',
    subtype: 'declared',
    provenance: 'declared',
    evidence: [{ relative_path: 'pyproject.toml', start_line: 18 }],
  },
  {
    id: 'dep-sqlalchemy',
    name: 'sqlalchemy',
    version: '2.0.36',
    subtype: 'declared',
    provenance: 'declared',
    evidence: [{ relative_path: 'pyproject.toml', start_line: 19 }],
  },
  {
    id: 'dep-import-httpx',
    name: 'httpx',
    version: null,
    subtype: 'imported',
    provenance: 'imported',
    evidence: [{ relative_path: 'app/clients.py', start_line: 1 }],
  },
  {
    id: 'dep-usage-redis',
    name: 'redis',
    version: '5.0.1',
    subtype: 'usage',
    provenance: 'usage',
    evidence: [{ relative_path: 'app/cache.py', start_line: 14 }],
  },
]

export const seedDiagnostics: DiagnosticItem[] = [
  {
    id: 'diag-1',
    severity: 'warning',
    code: 'ADAPTER_VERSION_UNVERIFIED',
    message: 'aiokafka version was detected but not verified against the adapter matrix.',
    evidence: [{ relative_path: 'app/messaging.py', start_line: 4 }],
  },
  {
    id: 'diag-2',
    severity: 'info',
    code: 'DETECTED_ONLY',
    message: 'celery is inventoried (detected_only); no runtime usage edges were inferred.',
  },
]

export const seedJobSucceeded: IndexJob = {
  job_id: DEMO_JOB_ID,
  repository_id: DEMO_REPO_ID,
  stage: 'succeeded_with_warnings',
  progress_revision: 4,
  message: 'Lập chỉ mục xong với 1 cảnh báo',
  report: {
    summary: 'Đã lập chỉ mục 12 thực thể và 14 cạnh.',
    warnings: ['phiên bản aiokafka chưa được xác minh'],
    selected_app_id: 'app-main',
    app_candidates: [
      {
        candidate_id: 'app-main',
        module: 'app.main',
        symbol: 'app',
        evidence: 'app/main.py:12',
      },
    ],
    technologies: [
      { technology: 'fastapi', support_state: 'supported_patterns' },
      { technology: 'aiokafka', support_state: 'version_unverified' },
    ],
  },
  snapshot_id: DEMO_SNAPSHOT_ID,
  error: null,
  updated_at: '2026-09-23T14:28:00Z',
}

function pathFor(id: string): string {
  const map: Record<string, string> = {
    'ent-endpoint-get-order': 'app/api/orders.py',
    'ent-fn-get-order': 'app/api/orders.py',
    'ent-fn-load-order': 'app/services/orders.py',
    'ent-class-order-repo': 'app/repositories/orders.py',
    'ent-method-order-repo': 'app/repositories/orders.py',
    'ent-table-orders': 'app/models.py',
    'ent-topic-order-events': 'app/messaging.py',
    'ent-fn-publish-order': 'app/messaging.py',
    'ent-fn-consume-order': 'app/workers.py',
    'ent-config-db-url': 'app/settings.py',
    'ent-iface-order-store': 'app/ports.py',
    'ent-module-main': 'app/main.py',
    'ent-class-app': 'app/main.py',
  }
  return map[id] ?? 'app/unknown.py'
}

function lineFor(id: string): number {
  let n = 10
  for (const ch of id) n += ch.charCodeAt(0)
  return (n % 80) + 1
}
