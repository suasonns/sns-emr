import React from 'react';
import BrandLogo from '../../components/BrandLogo';
import { NAV_ICONS, IconBell, IconSunMoon, IconLogout } from './icons';
import './tailwind.css';

/**
 * SNS Operations Command Center shell — the approved Figma redesign of the
 * Owner Platform chrome (icon-only sidebar + status topbar), wired to the
 * real navigation, auth, and theme logic already used by OwnerDashboard.
 *
 * This component only renders the shell (sidebar/topbar); the actual page
 * content for each route is passed in as `children`, unchanged, so none of
 * the 9 existing owner pages need to be rewritten to adopt this shell.
 */
export default function OwnerShell({
  navItems,
  activeTab,
  onNavigate,
  userDisplayName,
  userRole,
  onSignOut,
  mode,
  onToggleMode,
  systemHealthy = true,
  children,
}) {
  return (
    <div className="flex h-screen w-full bg-sns-app font-sans text-text-primary overflow-hidden">
      {/* Sidebar */}
      <aside className="w-16 flex flex-col justify-between items-center py-5 bg-sns-sidebar border-r border-sns-border shrink-0">
        <div className="flex flex-col items-center gap-8">
          <div className="w-12 h-12 rounded-[22px] bg-ai border border-ai flex items-center justify-center shadow-[0_4px_14px_rgba(13,148,136,0.35)] overflow-hidden">
            <BrandLogo variant="icon-dark-tile" alt="SNS Hospice Solutions" style={{ width: 36, height: 36 }} />
          </div>

          <nav className="flex flex-col gap-3" aria-label="Owner navigation">
            {navItems.map((item) => {
              const Icon = NAV_ICONS[item.key];
              const active = activeTab === item.key;
              return (
                <button
                  key={item.key}
                  type="button"
                  title={item.label}
                  aria-label={item.label}
                  aria-pressed={active}
                  aria-current={active ? 'page' : undefined}
                  onClick={() => onNavigate(item.key)}
                  className={`w-11 h-11 rounded-xl flex items-center justify-center cursor-pointer transition-colors duration-150 ${
                    active
                      ? 'bg-[var(--owner-nav-active-bg)] border border-sns-border-active text-ai'
                      : 'bg-transparent text-[var(--owner-nav-text)] hover:bg-[var(--owner-nav-hover-bg)] hover:text-[var(--owner-nav-text-hover)]'
                  }`}
                >
                  {Icon ? <Icon /> : null}
                </button>
              );
            })}
          </nav>
        </div>

        <div className="flex flex-col items-center gap-2">
          <button
            type="button"
            title={mode === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
            aria-label="Toggle theme"
            onClick={onToggleMode}
            className="w-9 h-9 rounded-lg flex items-center justify-center bg-transparent text-[var(--owner-nav-text)] hover:bg-[var(--owner-nav-hover-bg)] hover:text-[var(--owner-nav-text-hover)] transition-colors"
          >
            <IconSunMoon mode={mode} />
          </button>
          <button
            type="button"
            title={`Sign out (${userDisplayName})`}
            aria-label="Sign out"
            onClick={onSignOut}
            className="w-10 h-10 rounded-full border border-[var(--owner-sidebar-divider)] bg-gradient-to-br from-ai to-status-info flex items-center justify-center text-white hover:opacity-90 transition-opacity"
          >
            <IconLogout />
          </button>
        </div>
      </aside>

      {/* Main column */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="flex items-center justify-between px-8 h-14 bg-sns-topbar border-b border-sns-border shadow-topbar shrink-0">
          <div className="flex flex-col leading-tight">
            <span className="font-bold text-base text-text-primary tracking-tight">SNS Hospice Solutions</span>
            <span className="text-[11px] font-medium text-text-tertiary">by SNS Tech Solutions</span>
          </div>

          <div
            className={`flex items-center gap-2 px-3 py-1.5 rounded-full border ${
              systemHealthy
                ? 'bg-status-healthy/10 border-status-healthy/20'
                : 'bg-status-critical/10 border-status-critical/20'
            }`}
          >
            <span className={`w-2 h-2 rounded-full ${systemHealthy ? 'bg-status-healthy' : 'bg-status-critical'}`} />
            <span className={`font-semibold text-xs ${systemHealthy ? 'text-status-healthy' : 'text-status-critical'}`}>
              {systemHealthy ? 'All systems healthy' : 'Attention needed'}
            </span>
          </div>

          <div className="flex items-center gap-4">
            <div className="w-[34px] h-[34px] rounded-lg bg-[var(--owner-icon-btn-bg)] border border-sns-border flex items-center justify-center cursor-pointer text-text-secondary">
              <IconBell />
            </div>
            <div className="flex items-center gap-2.5">
              <span className="font-medium text-sm text-text-primary">{userDisplayName}</span>
              <span className="text-xs text-text-tertiary">{userRole}</span>
            </div>
          </div>
        </header>

        <main className="flex-1 overflow-y-auto">{children}</main>
      </div>
    </div>
  );
}
