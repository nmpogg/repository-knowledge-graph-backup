import type { ResponseMetadata } from '../../types/api'

export function readResponseMetadata(value: unknown): ResponseMetadata | null {
  if (!value || typeof value !== 'object') return null
  const item = value as Record<string, unknown>
  if (item.version !== 1 || !['vi', 'en'].includes(String(item.language)) ||
      !['answer', 'clarification', 'greeting', 'insufficient', 'error'].includes(String(item.kind)) ||
      !['complete', 'partial', 'unknown', 'not_applicable'].includes(String(item.coverage)) ||
      ![true, false, null].includes(item.retrieval_truncated as boolean | null) ||
      ![true, false, null].includes(item.history_truncated as boolean | null) ||
      !Array.isArray(item.limitations) ||
      !item.limitations.every((code) => ['max_chars', 'max_nodes', 'max_edges', 'max_depth', 'history_truncated'].includes(code)) ||
      !(item.subject === null || (typeof item.subject === 'object' && item.subject != null)) ||
      !(item.insufficient_reason === null || typeof item.insufficient_reason === 'string')) return null
  const required = ['version','language','kind','subject','coverage','retrieval_truncated','history_truncated','limitations','insufficient_reason']
  if (Object.keys(item).length !== required.length || required.some((key) => !(key in item))) return null
  const limits = item.limitations as string[]
  if (new Set(limits).size !== limits.length ||
      (limits.some((code) => code !== 'history_truncated')) !== (item.retrieval_truncated === true) ||
      limits.includes('history_truncated') !== (item.history_truncated === true)) return null
  if (item.coverage === 'partial' && item.retrieval_truncated !== true && item.history_truncated !== true) return null
  if (['greeting','clarification'].includes(String(item.kind)) && item.coverage !== 'not_applicable') return null
  if ((item.kind === 'insufficient') !== (item.insufficient_reason !== null)) return null
  if (item.kind === 'greeting' && item.subject !== null) return null
  if (item.subject !== null) {
    const subject = item.subject as Record<string, unknown>
    if (!['entity_id','type','name','qualified_name'].every((key) => typeof subject[key] === 'string' && (subject[key] as string).length > 0) ||
        ![subject.method, subject.path].every((value) => value === null || typeof value === 'string')) return null
  }
  if (item.kind === 'answer' && (item.subject === null || typeof item.retrieval_truncated !== 'boolean' || typeof item.history_truncated !== 'boolean' || !['complete','partial'].includes(String(item.coverage)))) return null
  if (item.coverage === 'complete'  && (item.retrieval_truncated !== false || item.history_truncated !== false || item.limitations.length)) return null
  return item as unknown as ResponseMetadata
}
