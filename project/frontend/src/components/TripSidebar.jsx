import React from 'react';
import { ArrowLeft, Search, RefreshCw, Navigation, Calendar, Clock, AlertCircle, ChevronRight } from 'lucide-react';
import { getScoreColorClass } from '../data/mockData';

export default function TripSidebar({
  mobileViewTab,
  setMobileViewTab,
  activeDriver,
  filteredJourneys,
  journeys,
  tripSearchTerm,
  setTripSearchTerm,
  isLoadingJourneys,
  activeJourneyId,
  setActiveJourneyId,
  isSidebarCollapsed,
  setIsSidebarCollapsed
}) {
  if (!activeDriver) return null;

  return (
    <section className={`w-full lg:w-[26%] xl:w-[410px] min-w-[340px] max-w-[430px] border-r border-slate-200 bg-white flex flex-col shrink-0 z-0 ${isSidebarCollapsed ? 'hidden' : (mobileViewTab === 'journeys' ? 'flex' : 'hidden lg:flex')}`}>
      {/* Active Driver Profile Header */}
      <div className="p-5 border-b border-slate-100 bg-slate-50/20 shrink-0">
        <div className="flex items-center gap-2 mb-3 lg:hidden">
          <button
            onClick={() => setMobileViewTab('drivers')}
            className="p-1.5 hover:bg-slate-100 rounded-xl text-slate-500 transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </button>
          <span className="text-xs font-bold text-slate-500">Back to Drivers</span>
        </div>
        <div className="flex items-start gap-4">
          <div
            className="w-12 h-12 rounded-2xl flex items-center justify-center text-white font-extrabold text-lg shadow-sm"
            style={{ backgroundColor: activeDriver.avatar_color || '#2563eb' }}
          >
            {activeDriver.name.split(' ').map(n => n[0]).join('')}
          </div>
          <div className="flex-1 min-w-0">
            <h2 className="text-base font-extrabold text-slate-900 truncate font-outfit tracking-tight">{activeDriver.name}</h2>
            <p className="text-xs text-slate-400 font-medium">Assigned Vehicle: <span className="text-slate-600 font-semibold">{activeDriver.vehicle_id || "VH001"}</span></p>
          </div>
        </div>

        {/* Driver Aggregate Parameters Grid */}
        <div className="grid grid-cols-2 gap-3 mt-4">
          <div className="bg-slate-50 border border-slate-200/50 p-2.5 rounded-xl text-center">
            <p className="text-[9px] text-slate-400 font-bold tracking-wide uppercase mb-0.5">Odometer Total</p>
            <p className="text-sm font-extrabold text-slate-800 font-outfit">
              {Math.round(activeDriver.total_odometer_km ?? 120400).toLocaleString()} km
            </p>
          </div>
          <div className="bg-slate-50 border border-slate-200/50 p-2.5 rounded-xl text-center">
            <p className="text-[9px] text-slate-400 font-bold tracking-wide uppercase mb-0.5">Engine Hours</p>
            <p className="text-sm font-extrabold text-slate-800 font-outfit">
              {Math.round(activeDriver.engine_total_hours ?? 2450).toLocaleString()} hrs
            </p>
          </div>
        </div>
      </div>

      {/* Past Journeys Header */}
      <div className="px-5 py-3 border-b border-slate-100 bg-slate-50/50 flex flex-col gap-3 shrink-0">
        <div className="flex items-center justify-between">
          <span className="text-xs font-bold text-slate-900 font-outfit tracking-wide uppercase">Journey History</span>
          <span className="text-[10px] px-2 py-0.5 bg-slate-200/60 text-slate-600 font-bold rounded-full">{filteredJourneys.length} Records</span>
        </div>
        <div className="relative">
          <input
            type="text"
            placeholder="Search trip ID or route..."
            value={tripSearchTerm}
            onChange={(e) => setTripSearchTerm(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-white border border-slate-200 rounded-lg text-xs focus:outline-none focus:ring-2 focus:ring-brand-500/20 focus:border-brand-500 transition-all font-medium placeholder-slate-400 shadow-sm"
          />
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-2.5 top-2" />
        </div>
      </div>

      {/* Journeys List */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        {isLoadingJourneys ? (
          <div className="h-40 flex flex-col items-center justify-center gap-2">
            <RefreshCw className="w-5 h-5 text-brand-500 animate-spin" />
            <span className="text-xs text-slate-400 font-medium">Retrieving journeys...</span>
          </div>
        ) : filteredJourneys.length === 0 ? (
          journeys.length === 0 ? (
            <div className="flex flex-col items-center justify-center gap-3 p-8 text-center">
              <div className="w-12 h-12 rounded-2xl bg-slate-100 flex items-center justify-center">
                <Navigation className="w-5 h-5 text-slate-300" />
              </div>
              <div>
                <p className="text-xs font-bold text-slate-500">No trips yet</p>
                <p className="text-[10px] text-slate-400 mt-0.5">Use the Simulator to inject a trip for this driver.</p>
              </div>
            </div>
          ) : (
            <div className="text-center p-6 text-xs text-slate-400 font-medium">No matching journeys found.</div>
          )
        ) : (
          filteredJourneys.map(j => {
            const isActive = j.journey_id === activeJourneyId;
            const hasAlert = j.fuel_theft_detected || j.maintenance_critical;

            return (
              <button
                key={j.journey_id}
                onClick={() => {
                  setActiveJourneyId(j.journey_id);
                  setMobileViewTab('details');
                }}
                className={`w-full p-3 rounded-xl transition-all text-left border relative flex flex-col gap-2 ${isActive
                    ? 'bg-brand-50/60 border-brand-100 shadow-sm'
                    : 'bg-white border-slate-200/70 hover:border-slate-300'
                  }`}
              >
                {/* Active Gradient Side Indicator */}
                {isActive && (
                  <div className="absolute left-0 top-3 bottom-3 w-1.5 rounded-r bg-brand-500 animate-pulse"></div>
                )}
                {/* Top segment */}
                <div className="flex items-center justify-between gap-1">
                  <div className="flex items-center gap-1.5">
                    <span className="text-xs font-extrabold text-slate-800 font-outfit tracking-tight">{j.journey_id}</span>
                    <span className="text-[9px] px-1.5 py-0.5 font-bold rounded-md bg-slate-100 text-slate-500 border border-slate-200/50">{j.route_type}</span>
                  </div>
                  <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold ${getScoreColorClass(j.driver_score)}`}>
                    Score: {j.driver_score}
                  </span>
                </div>

                {/* Detail parameters */}
                <div className="flex items-center justify-between text-[11px] text-slate-400 font-medium">
                  <span className="flex items-center gap-1">
                    <Calendar className="w-3.5 h-3.5 text-slate-300" /> {j.start_time.split(' ')[0]}
                  </span>
                  <span className="flex items-center gap-1">
                    <Navigation className="w-3.5 h-3.5 text-slate-300" /> {j.distance_km} km
                  </span>
                  <span className="flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 text-slate-300" /> {j.duration_min} min
                  </span>
                </div>

                {/* Warnings banner */}
                {hasAlert && (
                  <div className={`mt-1 py-1 px-2 rounded-lg text-[10px] font-bold flex items-center justify-between relative overflow-hidden ${j.fuel_theft_detected
                      ? 'bg-rose-50 text-rose-700 border border-rose-100'
                      : 'bg-amber-50 text-amber-700 border border-amber-100'
                    }`}>
                    <span className="flex items-center gap-1.5">
                      <AlertCircle className={`w-3.5 h-3.5 ${j.fuel_theft_detected ? 'text-rose-500 pulse-glow-red rounded-full' : 'text-amber-500'}`} />
                      {j.fuel_theft_detected ? 'THEFT ALERT DETECTED' : 'CRITICAL VEHICLE WARNING'}
                    </span>
                    <ChevronRight className="w-3.5 h-3.5" />
                  </div>
                )}
              </button>
            );
          })
        )}
      </div>
    </section>
  );
}
