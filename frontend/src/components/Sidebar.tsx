/**
 * Sidebar — Suradak Navigation
 */

import React from 'react'
import type { PageId } from '../types'
import {
  LayoutDashboard,
  Navigation,
  Cpu,
  AlertTriangle,
  BarChart3,
  Settings,
  ShieldCheck,
  Radar,
} from 'lucide-react'

interface SidebarProps {
  activePage: PageId
  onNavigate: (page: PageId) => void
  defectCount: number
  vehicleCount: number
  isConnected: boolean
}

export default function Sidebar({
  activePage,
  onNavigate,
  defectCount,
  isConnected,
}: SidebarProps) {
  const navItems: { id: PageId; label: string; icon: React.ReactNode; badge?: number }[] = [
    { id: 'command',   label: 'Command Center',    icon: <LayoutDashboard size={18} /> },
    { id: 'fleet',     label: 'Fleet Tracking',    icon: <Navigation size={18} /> },
    { id: 'video',     label: 'AI Intelligence',   icon: <Cpu size={18} /> },
    { id: 'events',    label: 'Urban Events',       icon: <AlertTriangle size={18} />, badge: defectCount },
    { id: 'analytics', label: 'Analytics',          icon: <BarChart3 size={18} /> },
    { id: 'settings',  label: 'Settings',           icon: <Settings size={18} /> },
  ]

  return (
    <aside className="routesense-sidebar">
      {/* Brand Header */}
      <div className="sidebar-brand-box">
        <div className="suradak-logo-icon">
          <Radar size={22} color="#06b6d4" strokeWidth={1.8} />
        </div>
        <div className="brand-text">
          <h1 className="brand-title">SURADAK</h1>
          <p className="brand-tagline">Smart Urban Road AI</p>
        </div>
      </div>

      {/* Nav Menu */}
      <nav className="sidebar-nav-menu">
        {navItems.map(item => {
          const isActive = activePage === item.id
          return (
            <button
              key={item.id}
              className={`routesense-nav-btn ${isActive ? 'active' : ''}`}
              onClick={() => onNavigate(item.id)}
              id={`nav-${item.id}`}
            >
              <span className="nav-btn-icon">{item.icon}</span>
              <span className="nav-btn-label">{item.label}</span>
              {item.badge !== undefined && item.badge > 0 && (
                <span className="nav-counter-badge">{item.badge}</span>
              )}
            </button>
          )
        })}
      </nav>

      {/* System Status */}
      <div className="sidebar-system-box">
        <div className="system-status-header">System Status</div>
        <div className="system-status-indicator">
          <span className={`status-led ${isConnected ? 'green' : 'red'}`}></span>
          <span>{isConnected ? 'All Systems Operational' : 'Offline / Standby'}</span>
        </div>
      </div>

      {/* Admin Profile Footer */}
      <div className="sidebar-user-footer">
        <div className="user-avatar-circle">
          <ShieldCheck size={16} color="#10b981" />
        </div>
        <div className="user-meta">
          <div className="user-name">Admin</div>
          <div className="user-email">admin@suradak.in</div>
        </div>
      </div>
    </aside>
  )
}
