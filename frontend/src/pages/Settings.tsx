/**
 * System Settings — RouteSense Screen 6
 * Features:
 *   - Category Navigation Tabs: General, Fleet, Video Sources, AI Models, Alerts, Users
 *   - General Settings Form (System Name, Time Zone, Refresh Interval, Units)
 *   - System Information Card (Version, Uptime, Database Status, Storage, Backup)
 *   - AI Model Status Checklist (YOLOv8, ByteTrack, Pothole Detector, Edge MAPE-K)
 */

import React, { useState } from 'react'
import {
  Save,
  CheckCircle2,
  Database,
  HardDrive,
  Cpu,
  Clock,
  RefreshCw,
  Sliders,
  Shield,
  Bell,
  Camera,
  Users,
} from 'lucide-react'

export default function Settings() {
  const [activeTab, setActiveTab] = useState<'general' | 'fleet' | 'video' | 'models' | 'alerts' | 'users'>('general')
  const [systemName, setSystemName] = useState('SURADAK')
  const [timeZone, setTimeZone] = useState('Asia/Kolkata (GMT+5:30)')
  const [refreshInterval, setRefreshInterval] = useState('5 seconds')
  const [distanceUnit, setDistanceUnit] = useState('Kilometers (km)')
  const [speedUnit, setSpeedUnit] = useState('Kilometers per hour (km/h)')
  const [savedToast, setSavedToast] = useState(false)
  const [backingUp, setBackingUp] = useState(false)
  const [backupSuccess, setBackupSuccess] = useState(false)

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault()
    setSavedToast(true)
    setTimeout(() => setSavedToast(false), 3000)
  }

  const handleBackup = () => {
    setBackingUp(true)
    setTimeout(() => {
      setBackingUp(false)
      setBackupSuccess(true)
      setTimeout(() => setBackupSuccess(false), 3000)
    }, 1200)
  }

  return (
    <div className="routesense-page settings-view">
      {/* Header */}
      <header className="routesense-page-header">
        <div className="header-left">
          <h2 className="header-main-title">System Settings</h2>
          <p className="header-subtitle">Configure system preferences and manage data</p>
        </div>

        <div className="header-right-meta">
          <div className="live-status-chip">
            <span className="live-dot-green"></span>
            <span className="live-text">LIVE</span>
          </div>
          <div className="live-clock-text">10:42:18 AM</div>
          <div className="header-user-avatar">RK</div>
        </div>
      </header>

      {/* Tabs Row */}
      <div className="settings-tabs-bar">
        <button
          className={`settings-tab-btn ${activeTab === 'general' ? 'active' : ''}`}
          onClick={() => setActiveTab('general')}
        >
          <Sliders size={14} />
          <span>General</span>
        </button>
        <button
          className={`settings-tab-btn ${activeTab === 'fleet' ? 'active' : ''}`}
          onClick={() => setActiveTab('fleet')}
        >
          <span>Fleet</span>
        </button>
        <button
          className={`settings-tab-btn ${activeTab === 'video' ? 'active' : ''}`}
          onClick={() => setActiveTab('video')}
        >
          <Camera size={14} />
          <span>Video Sources</span>
        </button>
        <button
          className={`settings-tab-btn ${activeTab === 'models' ? 'active' : ''}`}
          onClick={() => setActiveTab('models')}
        >
          <Cpu size={14} />
          <span>AI Models</span>
        </button>
        <button
          className={`settings-tab-btn ${activeTab === 'alerts' ? 'active' : ''}`}
          onClick={() => setActiveTab('alerts')}
        >
          <Bell size={14} />
          <span>Alerts</span>
        </button>
        <button
          className={`settings-tab-btn ${activeTab === 'users' ? 'active' : ''}`}
          onClick={() => setActiveTab('users')}
        >
          <Users size={14} />
          <span>Users</span>
        </button>
      </div>

      {/* Settings Grid Content */}
      <div className="settings-content-layout">
        {/* Left Column: Form */}
        <div className="settings-card general-settings-card">
          <div className="settings-card-header">
            <h3 className="card-heading">General Settings</h3>
            <span className="card-subheading">Core system parameters and units</span>
          </div>

          <form onSubmit={handleSave} className="settings-form">
            <div className="form-group">
              <label className="form-label" htmlFor="systemName">System Name</label>
              <input
                id="systemName"
                type="text"
                className="settings-input"
                value={systemName}
                onChange={e => setSystemName(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="timeZone">Time Zone</label>
              <select
                id="timeZone"
                className="settings-select"
                value={timeZone}
                onChange={e => setTimeZone(e.target.value)}
              >
                <option value="Asia/Kolkata (GMT+5:30)">Asia/Kolkata (GMT+5:30)</option>
                <option value="UTC (GMT+0:00)">UTC (GMT+0:00)</option>
                <option value="America/New_York (EST)">America/New_York (EST)</option>
                <option value="Europe/London (GMT)">Europe/London (GMT)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="refreshInterval">Refresh Interval</label>
              <select
                id="refreshInterval"
                className="settings-select"
                value={refreshInterval}
                onChange={e => setRefreshInterval(e.target.value)}
              >
                <option value="1 second">1 second (High Performance)</option>
                <option value="5 seconds">5 seconds (Recommended)</option>
                <option value="10 seconds">10 seconds</option>
                <option value="30 seconds">30 seconds (Low Bandwidth)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="distanceUnit">Distance Unit</label>
              <select
                id="distanceUnit"
                className="settings-select"
                value={distanceUnit}
                onChange={e => setDistanceUnit(e.target.value)}
              >
                <option value="Kilometers (km)">Kilometers (km)</option>
                <option value="Miles (mi)">Miles (mi)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="speedUnit">Speed Unit</label>
              <select
                id="speedUnit"
                className="settings-select"
                value={speedUnit}
                onChange={e => setSpeedUnit(e.target.value)}
              >
                <option value="Kilometers per hour (km/h)">Kilometers per hour (km/h)</option>
                <option value="Miles per hour (mph)">Miles per hour (mph)</option>
              </select>
            </div>

            <div className="form-actions-row">
              <button type="submit" className="routesense-primary-btn">
                <Save size={14} />
                <span>Save Changes</span>
              </button>
              {savedToast && (
                <div className="toast-pill success">
                  <CheckCircle2 size={13} />
                  <span>Preferences saved successfully</span>
                </div>
              )}
            </div>
          </form>
        </div>

        {/* Right Column: System Info & AI Model Status */}
        <div className="settings-info-column">
          {/* Card 1: System Information */}
          <div className="settings-card system-info-card">
            <div className="settings-card-header">
              <h3 className="card-heading">System Information</h3>
            </div>

            <div className="info-key-val-list">
              <div className="info-row">
                <span className="info-key">Version</span>
                <span className="info-val font-mono">1.0.0</span>
              </div>
              <div className="info-row">
                <span className="info-key">Uptime</span>
                <span className="info-val font-mono">2d 14h 32m</span>
              </div>
              <div className="info-row">
                <span className="info-key">Database</span>
                <span className="status-chip-pill active">
                  <span className="pill-dot"></span>
                  Connected
                </span>
              </div>
              <div className="info-row column">
                <div className="storage-label-row">
                  <span className="info-key">Storage</span>
                  <span className="info-val font-mono">72% Used</span>
                </div>
                <div className="storage-progress-bar">
                  <div className="progress-fill" style={{ width: '72%' }}></div>
                </div>
              </div>
              <div className="info-row">
                <span className="info-key">Last Backup</span>
                <span className="info-val">10:00 AM, Today</span>
              </div>
            </div>

            <div className="card-footer-action">
              <button
                type="button"
                className="routesense-secondary-btn"
                onClick={handleBackup}
                disabled={backingUp}
              >
                <RefreshCw size={13} className={backingUp ? 'spin-icon' : ''} />
                <span>{backingUp ? 'Backing up...' : backupSuccess ? 'Backed up!' : 'Backup Now'}</span>
              </button>
            </div>
          </div>

          {/* Card 2: AI Model Status */}
          <div className="settings-card ai-status-card">
            <div className="settings-card-header">
              <h3 className="card-heading">AI Model Status</h3>
            </div>

            <div className="ai-models-checklist">
              <div className="ai-model-item">
                <div className="model-name-box">
                  <div className="model-indicator active"></div>
                  <span className="model-title">YOLOv8</span>
                </div>
                <span className="status-chip-pill active">Active</span>
              </div>

              <div className="ai-model-item">
                <div className="model-name-box">
                  <div className="model-indicator active"></div>
                  <span className="model-title">ByteTrack</span>
                </div>
                <span className="status-chip-pill active">Active</span>
              </div>

              <div className="ai-model-item">
                <div className="model-name-box">
                  <div className="model-indicator active"></div>
                  <span className="model-title">Pothole Detector</span>
                </div>
                <span className="status-chip-pill active">Active</span>
              </div>

              <div className="ai-model-item">
                <div className="model-name-box">
                  <div className="model-indicator active"></div>
                  <span className="model-title">Edge MAPE-K Loop</span>
                </div>
                <span className="status-chip-pill active">Active</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
