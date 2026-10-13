import { GitBranch, Network, PanelLeftClose, PanelLeftOpen } from 'lucide-react'
import { useEffect, useState } from 'react'
import { NavLink, Outlet } from 'react-router-dom'
import { getClientMode } from '../../client'
import { LocaleToggle, useT } from '../../i18n'
import { Badge } from '../ui/Badge'
import { ThemeToggle } from '../ui/ThemeToggle'

const NAV_COLLAPSED_KEY = 'rkg.nav.collapsed'

export function AppShell() {
  const mode = getClientMode()
  const t = useT()
  const [collapsed, setCollapsed] = useState(() => {
    try {
      return localStorage.getItem(NAV_COLLAPSED_KEY) === '1'
    } catch {
      return false
    }
  })

  useEffect(() => {
    try {
      localStorage.setItem(NAV_COLLAPSED_KEY, collapsed ? '1' : '0')
    } catch {
      /* ignore */
    }
  }, [collapsed])

  const links = [
    { to: '/repositories', label: t('shell.nav.repositories'), icon: GitBranch, end: false },
    { to: '/explorer', label: t('shell.nav.explorer'), icon: Network, end: true },
  ]

  return (
    <div className={`app-shell${collapsed ? ' is-nav-collapsed' : ''}`}>
      <a className="skip-link" href="#main">
        {t('shell.skip')}
      </a>
      <nav
        className={`app-nav${collapsed ? ' is-collapsed' : ''}`}
        aria-label={t('shell.nav')}
        data-collapsed={collapsed ? 'true' : 'false'}
      >
        <div className="app-brand">
          <div className="app-brand-row">
            <strong>RKG</strong>
            <button
              type="button"
              className="app-nav-toggle"
              aria-expanded={!collapsed}
              aria-controls="app-nav-list"
              title={collapsed ? t('shell.expandNav') : t('shell.collapseNav')}
              onClick={() => setCollapsed((v) => !v)}
            >
              {collapsed ? (
                <PanelLeftOpen size={16} aria-hidden />
              ) : (
                <PanelLeftClose size={16} aria-hidden />
              )}
              <span className="sr-only">
                {collapsed ? t('shell.expandNav') : t('shell.collapseNav')}
              </span>
            </button>
          </div>
          {!collapsed ? <span>{t('shell.brandSub')}</span> : null}
        </div>
        <ul id="app-nav-list" className="app-nav-list">
          {links.map(({ to, label, icon: Icon, end }) => (
            <li key={to}>
              <NavLink
                to={to}
                end={end}
                title={label}
                aria-label={label}
                className={({ isActive }) =>
                  `app-nav-link${isActive ? ' is-active' : ''}`
                }
              >
                <Icon size={16} aria-hidden />
                <span className="app-nav-label">{label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
        <div className="app-nav-footer">
          {!collapsed ? (
            <Badge tone="info">{t('shell.clientMode', { mode })}</Badge>
          ) : null}
          <LocaleToggle />
          <ThemeToggle />
        </div>
      </nav>
      <div className="app-main">
        <main id="main" className="app-main-inner" tabIndex={-1}>
          <Outlet />
        </main>
      </div>
    </div>
  )
}
