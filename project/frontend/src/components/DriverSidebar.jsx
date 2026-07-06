import React from 'react';
import { Search, RefreshCw } from 'lucide-react';
import { getScoreColorClass } from '../data/mockData';

export default function DriverSidebar({
  mobileViewTab,
  searchTerm,
  setSearchTerm,
  isLoadingDrivers,
  filteredDrivers,
  activeDriverId,
  setActiveDriverId,
  setMobileViewTab,
  isSidebarCollapsed,
  setIsSidebarCollapsed
}) {
  return (
    <aside className={`w-full lg:w-[20%] xl:w-96 min-w-[280px] max-w-[380px] border-r border-slate-200 bg-white flex flex-col shrink-0 z-10 shadow-sm ${isSidebarCollapsed ? 'hidden' : (mobileViewTab === 'drivers' ? 'flex' : 'hidden lg:flex')}`}>
      {/* Search Box */}
      <div className="p-4 border-b border-slate-100 bg-slate-50/50 shrink-0">
        <div className="relative">
          <input
            type="text"
            placeholder="Search drivers or vehicles..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-white border border-slate-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all font-medium placeholder-slate-400 shadow-sm"
          />
          <Search className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
        </div>
      </div>

      {/* Drivers List */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-100 p-2 space-y-1">
        {isLoadingDrivers ? (
          <div className="h-40 flex flex-col items-center justify-center gap-2">
            <RefreshCw className="w-6 h-6 text-brand-500 animate-spin" />
            <span className="text-xs text-slate-400 font-medium">Loading Fleet Drivers...</span>
          </div>
        ) : filteredDrivers.length === 0 ? (
          <div className="p-6 text-center text-xs text-slate-400 font-medium">
            No matching drivers found.
          </div>
        ) : (
          filteredDrivers.map(d => {
            const isActive = d.driver_id === activeDriverId;
            return (
              <button
                key={d.driver_id}
                onClick={() => {
                  setActiveDriverId(d.driver_id);
                  setMobileViewTab('journeys');
                }}
                className={`w-full flex items-center gap-3.5 p-3 rounded-xl transition-all text-left relative ${isActive
                    ? 'bg-brand-50/60 border border-brand-100 shadow-sm'
                    : 'border border-transparent hover:bg-slate-50'
                  }`}
              >
                {/* Active Gradient Side Indicator */}
                {isActive && (
                  <div className="absolute left-0 top-3 bottom-3 w-1.5 rounded-r bg-brand-500 animate-pulse"></div>
                )}

                {/* Driver Avatar */}
                <div
                  className="w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm shadow-sm relative shrink-0"
                  style={{ backgroundColor: d.avatar_color || '#2563eb' }}
                >
                  {d.name.split(' ').map(n => n[0]).join('')}
                  <span className="absolute -bottom-1 -right-1 w-3.5 h-3.5 bg-emerald-500 border-2 border-white rounded-full flex items-center justify-center"></span>
                </div>

                {/* Driver Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-1 mb-0.5">
                    <span className="text-sm font-bold text-slate-900 truncate font-outfit">
                      {d.name}
                    </span>
                    <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold shrink-0 ${
                      d.total_trips === 0
                        ? 'bg-slate-100 text-slate-400'
                        : getScoreColorClass(d.avg_score)
                    }`}>
                      {d.total_trips === 0 ? '—' : d.avg_score}
                    </span>
                  </div>
                  <div className="text-[11px] font-semibold text-slate-400">
                    {d.total_trips} trip{d.total_trips !== 1 ? 's' : ''}
                  </div>
                </div>
              </button>
            );
          })
        )}
      </div>
    </aside>
  );
}
