import React from 'react';
import { Settings, XCircle, RefreshCw } from 'lucide-react';

export default function SettingsModal({
  isOpen,
  onClose,
  handleSaveSettings,
  settingsEmail,
  setSettingsEmail,
  isSavingSettings
}) {
  if (!isOpen) return null;

  return (
    <div 
      className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in"
      onClick={onClose}
    >
      <div 
        className="bg-white/95 rounded-3xl border border-slate-200/80 shadow-2xl w-full max-w-md overflow-hidden animate-slide-up shrink-0 flex flex-col"
        onClick={e => e.stopPropagation()}
      >
        {/* Modal Header */}
        <div className="bg-gradient-to-r from-slate-800 to-slate-900 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Settings className="w-5 h-5 text-white animate-spin-slow" />
            <span className="text-sm font-extrabold text-white font-outfit tracking-wide uppercase">
              ⚙️ System Settings
            </span>
          </div>
          <button
            onClick={onClose}
            className="text-white/70 hover:text-white transition-colors p-1 rounded-lg hover:bg-white/10 border-0 outline-none cursor-pointer"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <form onSubmit={handleSaveSettings} className="p-6 flex flex-col gap-4">
          <div>
            <label className="block text-xs font-bold text-slate-500 uppercase tracking-wider mb-2">
              Alerts Recipient Email
            </label>
            <div className="relative">
              <div className="absolute inset-y-0 left-0 pl-3.5 flex items-center pointer-events-none text-slate-400 font-bold">
                @
              </div>
              <input
                type="email"
                required
                value={settingsEmail}
                onChange={e => setSettingsEmail(e.target.value)}
                placeholder="Enter recipient email address"
                className="w-full pl-9 pr-4 py-2.5 bg-slate-50 border border-slate-200 rounded-xl text-sm font-medium text-slate-800 focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all"
              />
            </div>
            <p className="text-[11px] text-slate-400 mt-1.5 leading-relaxed">
              Real-time security notifications for fuel theft anomalies and critical predictive maintenance warnings will be sent here.
            </p>
          </div>

          <div className="pt-2 border-t border-slate-100 flex items-center justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-bold rounded-xl transition-all border-0 outline-none cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSavingSettings}
              className={`px-5 py-2.5 bg-brand-500 hover:bg-brand-600 text-white text-xs font-bold font-outfit rounded-xl transition-all cursor-pointer shadow-brand-glow border-0 outline-none flex items-center gap-2 ${
                isSavingSettings ? 'opacity-70 cursor-not-allowed' : ''
              }`}
            >
              {isSavingSettings ? (
                <>
                  <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                  <span>Saving...</span>
                </>
              ) : (
                <span>Save Settings</span>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
