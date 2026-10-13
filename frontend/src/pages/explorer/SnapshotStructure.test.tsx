import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { LocaleProvider } from '../../i18n'
import { SnapshotStructure } from './SnapshotStructure'

const fixtureClient = vi.hoisted(() => ({
    searchEntities: async () => ({
      items: [
        { id: 'dir', type: 'directory', name: 'pkg', qualified_name: 'pkg', file_path: 'pkg' },
        { id: 'file', type: 'file', name: 'unit.py', qualified_name: 'pkg.unit', file_path: 'pkg/unit.py' },
        { id: 'fn', type: 'function', name: 'run', qualified_name: 'pkg.unit.run', file_path: 'pkg/unit.py' },
      ],
      page: { total: 3, offset: 0, limit: 100 },
    }),
}))

vi.mock('../../client', () => ({ getRkgClient: () => fixtureClient }))

afterEach(cleanup)

describe('canonical Directory selection', () => {
  it('selects the same directory/file IDs as the API and still supports collapsing', async () => {
    const selected = vi.fn()
    render(<LocaleProvider><SnapshotStructure snapshotId="snap" schemaVersion="2"
      selectedId="dir" onSelectLeaf={selected} /></LocaleProvider>)
    const directory = await screen.findByRole('treeitem', { name: 'pkg, Directory' })
    expect(directory).toHaveAttribute('aria-selected', 'true')
    expect(directory).toHaveAttribute('aria-expanded', 'true')
    fireEvent.click(directory)
    expect(selected).toHaveBeenLastCalledWith('dir')
    expect(directory).toHaveAttribute('aria-expanded', 'false')
    fireEvent.keyDown(directory, { key: 'ArrowRight' })
    expect(directory).toHaveAttribute('aria-expanded', 'true')
    fireEvent.click(screen.getByRole('treeitem', { name: 'unit.py, File' }))
    expect(selected).toHaveBeenLastCalledWith('file')
    expect(screen.getByRole('treeitem', { name: 'run, Function' })).toBeInTheDocument()
  })
})
