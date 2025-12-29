'use client'

import Link from 'next/link'
import { ReactNode } from 'react'
import { usePathname } from 'next/navigation'

type NavLink = {
  href: string
  label: string
}

const links: NavLink[] = [
  { href: '/', label: 'Leads' },
  { href: '/chat', label: 'AI Chat' },
  { href: '/inventory', label: 'Inventory' },
  { href: '/marketing/personas', label: 'Marketing' },
  { href: '/pipeline', label: 'Pipeline' },
]

export function Layout({ title, children }: { title: string; children: ReactNode }) {
  const pathname = usePathname()

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)' }}>
      <header className="topbar">
        <div className="topbar__inner">
          <div>
            <div className="brand">Real Estate AI CRM</div>
            <div className="subtitle">{title}</div>
          </div>
          <nav className="nav">
            {links.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={`nav__link${pathname === link.href ? ' nav__link--active' : ''}`}
              >
                {link.label}
              </Link>
            ))}
          </nav>
        </div>
      </header>
      <main className="page">{children}</main>
    </div>
  )
}
