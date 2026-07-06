import React from 'react';
import { ShieldAlert, XCircle, AlertTriangle, Clock, MapPin, Droplet, ArrowRight } from 'lucide-react';
import TheftLocationMap from '../components/TheftLocationMap';

export default function FuelTheftModal({
  activeFuelAlert,
  setActiveFuelAlert,
  isReplayRunningRef,
  globalMuteRef,
  dismissedToastIdsRef,
  renderToastBanner
}) {
  if (!activeFuelAlert) return null;
  return (
            <div
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in"
              onClick={() => setActiveFuelAlert(null)}
            >
              <div className="relative flex items-start w-full max-w-2xl">
                <div
                  className="bg-white rounded-3xl shadow-2xl w-full overflow-hidden animate-slide-up shrink-0 max-h-[90vh] flex flex-col"
                  style={{ maxWidth: '680px' }}
                  onClick={e => e.stopPropagation()}
                >
                  {/* Modal Header */}
                  <div className="bg-rose-600 px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <ShieldAlert className="w-5 h-5 text-white" />
                      <span className="text-sm font-extrabold text-white font-outfit tracking-wide uppercase">
                        🚨 Fuel Theft Detected
                      </span>
                    </div>
                  <button
                    onClick={() => {
                      setActiveFuelAlert(null);
                      if (!isReplayRunningRef.current) {
                        globalMuteRef.current = true;
                        if (activeFuelAlert) {
                          dismissedToastIdsRef.current.add(`${activeFuelAlert.driver_id}-${activeFuelAlert.trip_id}`);
                        }
                      }
                    }}
                    className="text-white/70 hover:text-white transition-colors p-1 rounded-lg hover:bg-white/10 border-0 outline-none cursor-pointer"
                  >
                    <XCircle className="w-5 h-5" />
                  </button>
                </div>

                {/* Modal Body */}
                <div className="p-6 space-y-4 overflow-y-auto flex-1">
                  {/* Human-readable theft description */}
                  <div className={`px-4 py-3 rounded-2xl border text-sm font-bold flex items-start gap-3 ${activeFuelAlert.theft_type === 'IGNITION_OFF_DROP'
                      ? 'bg-rose-50 border-rose-200 text-rose-700'
                      : activeFuelAlert.theft_type === 'RUNNING_THEFT'
                        ? 'bg-orange-50 border-orange-200 text-orange-700'
                        : 'bg-amber-50 border-amber-200 text-amber-700'
                    }`}>
                    <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" />
                    <span>
                      {activeFuelAlert.theft_type === 'IGNITION_OFF_DROP' &&
                        `Fuel theft while ignition is OFF — ${activeFuelAlert.theft_amount_liters?.toFixed(2)}L drained while vehicle was stationary and engine was off`
                      }
                      {activeFuelAlert.theft_type === 'RUNNING_THEFT' &&
                        `Running theft detected — ${activeFuelAlert.theft_amount_liters?.toFixed(2)}L siphoned while vehicle was moving at ${activeFuelAlert.speed_kmh?.toFixed(1)} km/h`
                      }
                      {activeFuelAlert.theft_type === 'REFUEL_THEFT' &&
                        `Refuel discrepancy — ${activeFuelAlert.theft_amount_liters?.toFixed(2)}L mismatch between sensor reading and uploaded receipt`
                      }
                      {!['IGNITION_OFF_DROP', 'RUNNING_THEFT', 'REFUEL_THEFT'].includes(activeFuelAlert.theft_type) &&
                        `Suspicious fuel drop of ${activeFuelAlert.theft_amount_liters?.toFixed(2)}L detected (${activeFuelAlert.theft_type})`
                      }
                    </span>
                  </div>

                  {/* Detail Grid */}
                  <div className="grid grid-cols-2 gap-3">
                    <div className="bg-slate-50 border border-slate-200/60 p-3 rounded-xl">
                      <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wide mb-0.5">Driver Name</p>
                      <p className="text-sm font-extrabold text-slate-800 font-outfit">{activeFuelAlert.driver_name}</p>
                    </div>
                    <div className="bg-slate-50 border border-slate-200/60 p-3 rounded-xl">
                      <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wide mb-0.5">Vehicle</p>
                      <p className="text-sm font-extrabold text-slate-800 font-outfit">{activeFuelAlert.vehicle_id}</p>
                    </div>
                    <div className="bg-slate-50 border border-slate-200/60 p-3 rounded-xl">
                      <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wide mb-0.5">Fuel Stolen</p>
                      <p className="text-sm font-extrabold text-rose-600 font-outfit">
                        {activeFuelAlert.theft_amount_liters?.toFixed(2)} L
                      </p>
                    </div>
                    <div className="bg-slate-50 border border-slate-200/60 p-3 rounded-xl">
                      <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wide mb-0.5">Speed at Event</p>
                      <p className="text-sm font-extrabold text-slate-800 font-outfit">
                        {activeFuelAlert.speed_kmh?.toFixed(1) ?? '0.0'} km/h
                      </p>
                    </div>
                    <div className="bg-slate-50 border border-slate-200/60 p-3 rounded-xl col-span-2">
                      <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wide mb-0.5">Event Time</p>
                      <p className="text-xs font-bold text-slate-700">{activeFuelAlert.event_time}</p>
                    </div>
                    <div className="bg-slate-50 border border-slate-200/60 p-3 rounded-xl col-span-2">
                      <p className="text-[9px] text-slate-400 font-bold uppercase tracking-wide mb-0.5">Trip ID</p>
                      <p className="text-xs font-bold text-slate-700">{activeFuelAlert.trip_id}</p>
                    </div>
                    {activeFuelAlert.gps_lat && activeFuelAlert.gps_lng && (
                      <div className="col-span-2">
                        <p className="text-xs font-semibold text-slate-400 uppercase tracking-wide mb-2">GPS Location</p>
                        <TheftLocationMap lat={activeFuelAlert.gps_lat} lng={activeFuelAlert.gps_lng} />
                      </div>
                    )}
                  </div>

                  {activeFuelAlert.accumulated_count > 1 && (
                    <div className="mt-4 bg-rose-50 border border-rose-200/60 p-3.5 rounded-xl flex items-center justify-between shadow-sm">
                      <div>
                        <p className="text-[10px] text-rose-600 font-extrabold uppercase tracking-wide mb-1">Repeated Alert Accumulation</p>
                        <p className="text-xs font-bold text-rose-700 leading-tight">
                          Added <span className="font-black font-outfit">{activeFuelAlert.original_amount?.toFixed(2)}L</span> to previous total. <br/>
                          Total is now <span className="font-black font-outfit">{activeFuelAlert.theft_amount_liters?.toFixed(2)}L</span>
                        </p>
                      </div>
                      <div className="bg-rose-100 text-rose-700 px-3 py-1.5 rounded-lg flex flex-col items-center justify-center border border-rose-200">
                        <span className="text-xl font-black font-outfit leading-none">{activeFuelAlert.accumulated_count}x</span>
                        <span className="text-[8px] font-extrabold uppercase tracking-wider mt-0.5">Events</span>
                      </div>
                    </div>
                  )}
                </div>

                {/* Modal Footer */}
                <div className="px-6 py-4 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between gap-3 flex-wrap">
                  <button
                    onClick={() => {
                      setActiveDriverId(activeFuelAlert.driver_id);
                      setActiveJourneyId(activeFuelAlert.trip_id);
                      setMobileViewTab('details');
                      setActiveFuelAlert(null);
                      setShowAlertToast(false);
                    }}
                    className="flex items-center gap-2 px-4 py-2.5 bg-slate-800 hover:bg-slate-900 active:scale-95 text-white text-xs font-bold font-outfit rounded-xl transition-all cursor-pointer shadow-sm border-0 outline-none"
                  >
                    <ArrowRight className="w-4 h-4" />
                    Go to Driver &amp; Trip
                  </button>

                  {fuelAlerts.length > 1 && (
                    <button
                      onClick={() => {
                        setFuelAlerts(prev => {
                          const newAlerts = prev.filter(a => a.alert_id !== activeFuelAlert.alert_id);
                          setActiveFuelAlert(newAlerts[0] || null);
                          return newAlerts;
                        });
                      }}
                      className="text-xs font-bold text-slate-500 hover:text-slate-700 bg-white border border-slate-200 hover:bg-slate-50 px-3 py-2.5 rounded-xl transition-all cursor-pointer outline-none"
                    >
                      Next ({fuelAlerts.length - 1} more)
                    </button>
                  )}

                  <button
                    onClick={() => {
                      setFuelAlerts(prev => prev.filter(a => a.alert_id !== activeFuelAlert.alert_id));
                      setActiveFuelAlert(null);
                    }}
                    className="px-4 py-2.5 bg-rose-600 hover:bg-rose-700 active:scale-95 text-white text-xs font-bold font-outfit rounded-xl transition-all cursor-pointer shadow-sm border-0 outline-none"
                  >
                    Dismiss
                  </button>
                </div>
              </div>
              {/* Toast on the right */}
              <div className="absolute top-0 -right-6 translate-x-full">
                {renderToastBanner(false)}
              </div>
            </div>
            </div>
  );
}
