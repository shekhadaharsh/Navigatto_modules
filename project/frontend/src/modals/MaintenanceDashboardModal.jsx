import React from 'react';
import {
  Wrench, XCircle, Search, Filter, AlertTriangle, AlertCircle, CheckCircle2,
  Activity, Thermometer, Battery, Compass, ChevronRight, RefreshCw, Clock, Info, Truck, ArrowLeft
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, CartesianGrid, XAxis, YAxis, Tooltip, Legend
} from 'recharts';

export default function MaintenanceDashboardModal({
  isOpen,
  onClose,
  maintSearchTerm,
  setMaintSearchTerm,
  maintHealthData,
  isLoadingMaintHealth,
  activeMaintTab: propActiveTab,
  setActiveMaintTab: propSetActiveTab,
  maintFleetSummary: propFleetSummary,
  maintHistoryData: propHistoryData,
  isLoadingMaintHistory: propIsLoadingHistory,
  openMaintenanceDashboard,
  handleResolveComponent
}) {
  const [localActiveTab, setLocalActiveTab] = React.useState('vehicle');
  const [maintFilterStatus, setMaintFilterStatus] = React.useState('all');
  const [localFleetSummary, setLocalFleetSummary] = React.useState({ open_alerts: 0, fleet: [] });
  const [localHistoryData, setLocalHistoryData] = React.useState([]);
  const [localIsLoadingHistory, setLocalIsLoadingHistory] = React.useState(false);

  const activeMaintTab = propActiveTab !== undefined ? propActiveTab : localActiveTab;
  const setActiveMaintTab = propSetActiveTab || setLocalActiveTab;
  const maintFleetSummary = propFleetSummary || localFleetSummary;
  const maintHistoryData = propHistoryData || localHistoryData;
  const isLoadingMaintHistory = propIsLoadingHistory !== undefined ? propIsLoadingHistory : localIsLoadingHistory;

  if (!isOpen) return null;
  return (
                <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-50 flex items-center justify-center p-4 transition-all">
                  <div className="bg-white rounded-[32px] border border-slate-200/80 shadow-2xl w-full max-w-4xl h-[85vh] flex flex-col overflow-hidden animate-fade-in">

                    {/* Modal Header */}
                    <div className="px-6 py-5 bg-slate-50 border-b border-slate-200/80 flex flex-wrap items-center justify-between gap-4 shrink-0">
                      <div className="flex items-center gap-3">
                        {activeMaintTab === 'vehicle' ? (
                          <button
                            onClick={() => setActiveMaintTab('fleet')}
                            title="Back to Fleet Status"
                            className="p-3 bg-brand-50 hover:bg-brand-100 text-brand-600 rounded-2xl transition-all active:scale-95 border-0 cursor-pointer flex items-center justify-center outline-none"
                          >
                            <ArrowLeft className="w-6 h-6" />
                          </button>
                        ) : (
                          <div className="p-3 bg-brand-500 text-white rounded-2xl shadow-brand-glow">
                            <Wrench className="w-6 h-6 animate-pulse" />
                          </div>
                        )}
                        <div>
                          <h2 className="text-lg font-black font-outfit text-slate-900 tracking-tight flex items-center gap-2">
                            Predictive Vehicle Diagnostics Centre
                          </h2>
                          <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">
                            {maintHealthData ? `${maintHealthData.make || 'Vehicle'} ${maintHealthData.model || ''} (${maintHealthData.reg_no || maintHealthData.vehicle_id || 'Unknown'})`.trim() : "Vehicle Telemetry Wear Analysis"}
                          </p>
                        </div>
                      </div>

                      {/* Interactive Tabs */}
                      <div className="flex items-center gap-2 bg-slate-200/60 p-1 rounded-2xl">
                        <button
                          onClick={() => setActiveMaintTab('vehicle')}
                          className={`px-4 py-2 text-xs font-bold font-outfit rounded-xl flex items-center gap-1.5 transition-all cursor-pointer border-0 outline-none ${
                            activeMaintTab === 'vehicle'
                              ? 'bg-white text-brand-600 shadow-sm'
                              : 'bg-transparent text-slate-500 hover:text-slate-800'
                          }`}
                        >
                          <Activity className="w-3.5 h-3.5" /> Vehicle Wear & RUL
                        </button>
                        <button
                          onClick={() => setActiveMaintTab('fleet')}
                          className={`px-4 py-2 text-xs font-bold font-outfit rounded-xl flex items-center gap-1.5 transition-all cursor-pointer border-0 outline-none ${
                            activeMaintTab === 'fleet'
                              ? 'bg-white text-brand-600 shadow-sm'
                              : 'bg-transparent text-slate-500 hover:text-slate-800'
                          }`}
                        >
                          <Truck className="w-3.5 h-3.5" /> Vehicles Status
                        </button>
                      </div>

                      {/* Close Button */}
                      <button
                        onClick={() => onClose()}
                        className="p-1 hover:bg-slate-200 rounded-full text-slate-400 hover:text-rose-500 transition-colors cursor-pointer active:scale-95 border-0 bg-transparent"
                      >
                        <XCircle className="w-7 h-7" />
                      </button>
                    </div>

                    {/* Modal Body */}
                    <div className="flex-1 overflow-y-auto p-6 bg-slate-50/50">
                      {isLoadingMaintHealth && (activeMaintTab === 'vehicle' || !maintFleetSummary) ? (
                        <div className="h-full flex flex-col items-center justify-center gap-3">
                          <div className="w-12 h-12 border-4 border-brand-500/20 border-t-brand-500 rounded-full animate-spin"></div>
                          <span className="text-xs text-slate-500 font-bold tracking-wide">Fusing physical wear models and sensor history...</span>
                        </div>
                      ) : activeMaintTab === 'vehicle' ? (
                        /* Tab 1: Vehicle Diagnostics */
                        <div className="space-y-6">
                          {/* Vehicle overview stats ribbon */}
                          {maintHealthData && (
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                              <div className="bg-white rounded-2xl border border-slate-200/60 p-4 shadow-sm flex items-center gap-3">
                                <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
                                  <CheckCircle2 className="w-5 h-5" />
                                </div>
                                <div>
                                  <span className="text-[10px] text-slate-400 font-bold uppercase block leading-none mb-1">Health Status</span>
                                  <span className="text-sm font-extrabold font-outfit text-slate-800">
                                    {maintHealthData.components && maintHealthData.components.some(c => c.health_score < 10.0)
                                      ? "Urgent Maintenance Needed"
                                      : maintHealthData.components && maintHealthData.components.some(c => c.health_score < 30.0)
                                        ? "Warning Alerts Open"
                                        : "Systems Optimal"}
                                  </span>
                                </div>
                              </div>
                              <div className="bg-white rounded-2xl border border-slate-200/60 p-4 shadow-sm flex items-center gap-3">
                                <div className="p-3 bg-amber-50 text-amber-600 rounded-xl">
                                  <Clock className="w-5 h-5" />
                                </div>
                                <div>
                                  <span className="text-[10px] text-slate-400 font-bold uppercase block leading-none mb-1">Critical Components</span>
                                  <span className="text-sm font-extrabold font-outfit text-slate-800">
                                    {maintHealthData.components ? maintHealthData.components.filter(c => c.health_score < 30.0).length : 0} of {maintHealthData.components ? maintHealthData.components.length : 0} Wear Limits Exceeded
                                  </span>
                                </div>
                              </div>
                              <div className="bg-white rounded-2xl border border-slate-200/60 p-4 shadow-sm flex items-center gap-3">
                                <div className="p-3 bg-blue-50 text-blue-600 rounded-xl">
                                  <Compass className="w-5 h-5" />
                                </div>
                                <div>
                                  <span className="text-[10px] text-slate-400 font-bold uppercase block leading-none mb-1">Vehicle ID / Reg No</span>
                                  <span className="text-sm font-extrabold font-outfit text-slate-800">{maintHealthData.reg_no || 'Unknown'} {maintHealthData.vehicle_id && `(${maintHealthData.vehicle_id})`}</span>
                                </div>
                              </div>
                            </div>
                          )}

                          {/* Components Wear Grid */}
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {maintHealthData && maintHealthData.components && maintHealthData.components
                              .filter(c => c.component !== 'clutch')
                              .map((c, ci) => {
                                const healthScoreVal = c && c.health_score !== undefined && c.health_score !== null ? parseFloat(c.health_score) : 100.0;
                                const health = healthScoreVal.toFixed(1);
                                const isCrit = healthScoreVal < 10.0;
                                const isWarn = healthScoreVal >= 10.0 && healthScoreVal < 30.0;
                                const colorClass = isCrit ? 'text-rose-500' : isWarn ? 'text-amber-500' : 'text-emerald-500';
                                const strokeColor = isCrit ? '#ef4444' : isWarn ? '#f59e0b' : '#10b981';

                                const unitText = { brake: 'km', tire: 'km', engine: 'hrs', battery: 'cycles', clutch: 'km' }[c.component] || 'units';

                                // Calculate circumference for progress ring
                                const radius = 35;
                                const circumference = 2 * Math.PI * radius;
                                const offset = circumference - (c.health_score / 100) * circumference;

                                return (
                                  <div key={ci} className="bg-white rounded-3xl border border-slate-200/80 p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between">
                                    <div>
                                      {/* Component Title & Status */}
                                      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4">
                                        <div className="flex items-center gap-2">
                                          <span className="p-2 bg-slate-50 text-slate-500 rounded-xl">
                                            {c.component === "brake" ? <Wrench className="w-4 h-4" /> :
                                              c.component === "tire" ? <Compass className="w-4 h-4" /> :
                                                c.component === "battery" ? <Battery className="w-4 h-4" /> :
                                                  <Thermometer className="w-4 h-4" />}
                                          </span>
                                        <div>
                                          <h4 className="text-sm font-black font-outfit text-slate-800 uppercase tracking-wide leading-none">{c.component} Systems</h4>
                                          <span className="text-[10px] text-slate-400 font-bold uppercase">Physics wear engine</span>
                                        </div>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        {healthScoreVal < 100.0 && (
                                          <button
                                            onClick={(e) => {
                                              e.stopPropagation();
                                              handleResolveComponent(c.component, maintHealthData.vehicle_id);
                                            }}
                                            className="text-[9px] font-bold bg-white/80 hover:bg-white text-slate-700 px-2 py-0.5 rounded border border-slate-200 shadow-sm transition-all cursor-pointer select-none active:scale-95"
                                          >
                                            Resolve
                                          </button>
                                        )}
                                        <span className={`text-[9px] px-2 py-0.5 rounded-full font-black border uppercase tracking-wider ${isCrit ? 'bg-rose-50 text-rose-700 border-rose-200' :
                                            isWarn ? 'bg-amber-50 text-amber-700 border-amber-200' :
                                              'bg-emerald-50 text-emerald-700 border-emerald-200'
                                          }`}>
                                          {c.status}
                                        </span>
                                      </div>
                                    </div>

                                    {/* Circular radial indicator and details */}
                                    <div className="flex items-center justify-around gap-4 mb-4">
                                      {/* Radial Gauge */}
                                      <div className="relative w-24 h-24 shrink-0 flex items-center justify-center">
                                        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                                          <circle className="text-slate-100" strokeWidth="8" stroke="currentColor" fill="transparent" r={radius} cx="50" cy="50" />
                                          <circle
                                            stroke={strokeColor}
                                            strokeWidth="8"
                                            strokeDasharray={circumference}
                                            strokeDashoffset={offset}
                                            strokeLinecap="round"
                                            fill="transparent"
                                            r={radius} cx="50" cy="50"
                                            className="transition-all duration-500"
                                          />
                                        </svg>
                                        <div className="absolute flex flex-col items-center justify-center">
                                          <span className={`text-lg font-black font-outfit leading-none ${colorClass}`}>{health}%</span>
                                          <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wide">Health</span>
                                        </div>
                                      </div>

                                      {/* Wear details */}
                                      <div className="flex-1 space-y-2 text-xs font-semibold text-slate-500">
                                        <div className="flex justify-between border-b border-slate-50 pb-1">
                                          <span>RUL (Predictive):</span>
                                          <span className="text-slate-800 font-bold">{Math.round(c.rul).toLocaleString()} {unitText}</span>
                                        </div>
                                        <div className="flex justify-between border-b border-slate-50 pb-1">
                                          <span>Accumulated Wear:</span>
                                          <span className="text-slate-800 font-bold">{parseFloat(c.accumulated_wear).toFixed(1)} {unitText}</span>
                                        </div>
                                        <div className="flex justify-between">
                                          <span>Life Threshold limit:</span>
                                          <span className="text-slate-800 font-bold">{Math.round(c.base_life).toLocaleString()} {unitText}</span>
                                        </div>
                                      </div>
                                    </div>
                                  </div>

                                  <div className="bg-slate-50 rounded-2xl border border-slate-200/40 p-2.5 text-[10px] text-slate-400 font-bold flex items-center justify-between">
                                    <span>LAST ANALYZED CYCLES:</span>
                                    <span className="text-slate-600 font-extrabold">{c.last_updated ? c.last_updated : "N/A"}</span>
                                  </div>
                                </div>
                              );
                            })}
                          </div>

                          {/* Component Daily Wear Accumulation Trend Chart */}
                          {maintHistoryData && maintHistoryData.length > 0 && (
                            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-sm">
                              <div className="flex items-center justify-between border-b border-slate-100 pb-4 mb-4">
                                <div>
                                  <h4 className="text-sm font-black font-outfit text-slate-800 uppercase tracking-wide">Component Daily Wear Trend</h4>
                                  <p className="text-[10px] text-slate-400 font-bold uppercase">Last 10 active days wear accumulation rate (wear units)</p>
                                </div>
                                <span className="text-[10px] bg-brand-50 text-brand-600 px-2 py-0.5 rounded-full font-bold border border-brand-100">
                                  Trend Analysis
                                </span>
                              </div>
                              
                              <div className="h-64 w-full">
                                {isLoadingMaintHistory ? (
                                  <div className="h-full flex items-center justify-center">
                                    <RefreshCw className="w-5 h-5 text-brand-500 animate-spin" />
                                    <span className="text-xs text-slate-400 font-medium ml-2 font-outfit">Loading history chart...</span>
                                  </div>
                                ) : (
                                  <ResponsiveContainer width="100%" height="100%">
                                    <AreaChart
                                      data={maintHistoryData}
                                      margin={{ top: 10, right: 10, left: -10, bottom: 0 }}
                                    >
                                      <defs>
                                        <linearGradient id="colorBrakes" x1="0" y1="0" x2="0" y2="1">
                                          <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.8}/>
                                          <stop offset="95%" stopColor="#f59e0b" stopOpacity={0}/>
                                        </linearGradient>
                                        <linearGradient id="colorTires" x1="0" y1="0" x2="0" y2="1">
                                          <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.8}/>
                                          <stop offset="95%" stopColor="#3b82f6" stopOpacity={0}/>
                                        </linearGradient>
                                        <linearGradient id="colorEngine" x1="0" y1="0" x2="0" y2="1">
                                          <stop offset="5%" stopColor="#6366f1" stopOpacity={0.8}/>
                                          <stop offset="95%" stopColor="#6366f1" stopOpacity={0}/>
                                        </linearGradient>
                                      </defs>
                                      <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.5} />
                                      <XAxis 
                                        dataKey="date" 
                                        stroke="#94a3b8" 
                                        fontSize={10} 
                                        fontWeight={600} 
                                        tickLine={false} 
                                        axisLine={false} 
                                        dy={8}
                                        tickFormatter={(dateStr) => {
                                          try {
                                            const parts = (dateStr || '').split('-');
                                            if (parts.length === 3) {
                                              return `${parts[2]}/${parts[1]}`; // DD/MM format
                                            }
                                          } catch (_) {}
                                          return dateStr;
                                        }}
                                      />
                                      <YAxis 
                                        stroke="#94a3b8" 
                                        fontSize={10} 
                                        fontWeight={600} 
                                        tickLine={false} 
                                        axisLine={false} 
                                        dx={-8}
                                      />
                                      <Tooltip
                                        contentStyle={{
                                          backgroundColor: 'rgba(255, 255, 255, 0.95)',
                                          backdropFilter: 'blur(8px)',
                                          borderRadius: '16px',
                                          border: '1px solid #e2e8f0',
                                          boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.05)',
                                          fontSize: '11px',
                                          fontWeight: 'bold',
                                        }}
                                      />
                                      <Legend verticalAlign="top" height={36} iconType="circle" wrapperStyle={{ fontSize: '11px', fontWeight: 'bold' }} />
                                      <Area type="monotone" dataKey="brakes" stackId="1" stroke="#f59e0b" strokeWidth={2} fillOpacity={1} fill="url(#colorBrakes)" name="Brakes" />
                                      <Area type="monotone" dataKey="tires" stackId="1" stroke="#3b82f6" strokeWidth={2} fillOpacity={1} fill="url(#colorTires)" name="Tires" />
                                      <Area type="monotone" dataKey="engine" stackId="1" stroke="#6366f1" strokeWidth={2} fillOpacity={1} fill="url(#colorEngine)" name="Engine" />
                                    </AreaChart>
                                  </ResponsiveContainer>
                                )}
                              </div>
                            </div>
                          )}
                        </div>
                      ) : (
                        /* Tab 2: Fleet Summary */
                        <div className="space-y-6">
                          {/* Fleet status overview metrics */}
                          {maintFleetSummary && (
                            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                              <div className="bg-white rounded-2xl border border-slate-200/60 p-4 shadow-sm text-center">
                                <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Fleet size</span>
                                <p className="text-2xl font-black font-outfit text-slate-800">{maintFleetSummary.fleet.length}</p>
                              </div>
                              <div className="bg-white rounded-2xl border border-slate-200/60 p-4 shadow-sm text-center">
                                <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Warning Components</span>
                                <p className="text-2xl font-black font-outfit text-amber-600">
                                  {maintFleetSummary.fleet.reduce((acc, c) => acc + c.warning_count, 0)}
                                </p>
                              </div>
                              <div className="bg-white rounded-2xl border border-slate-200/60 p-4 shadow-sm text-center">
                                <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Critical Components</span>
                                <p className="text-2xl font-black font-outfit text-rose-600">
                                  {maintFleetSummary.fleet.reduce((acc, c) => acc + c.critical_count, 0)}
                                </p>
                              </div>
                              <div className="bg-white rounded-2xl border border-slate-200/60 p-4 shadow-sm text-center">
                                <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider block mb-1">Open database Alerts</span>
                                <p className="text-2xl font-black font-outfit text-brand-600">{maintFleetSummary.open_alerts}</p>
                              </div>
                            </div>
                          )}

                          {/* Fleet search and filter bar */}
                          <div className="bg-white p-4 rounded-2xl border border-slate-200/60 shadow-sm flex flex-wrap items-center justify-between gap-4">
                            <div className="relative w-64">
                              <Search className="absolute left-3 top-2.5 w-4 h-4 text-slate-400" />
                              <input
                                type="text"
                                placeholder="Search vehicle reg no..."
                                value={maintSearchTerm}
                                onChange={(e) => setMaintSearchTerm(e.target.value)}
                                className="pl-9 pr-4 py-2 w-full text-xs font-semibold bg-slate-50 hover:bg-slate-100 focus:bg-white border border-slate-200 focus:border-brand-500 rounded-xl outline-none transition-all placeholder-slate-400"
                              />
                            </div>

                            <div className="flex gap-1.5 bg-slate-100 p-1 rounded-xl">
                              {['all', 'critical', 'warning', 'ok'].map((f) => (
                                <button
                                  key={f}
                                  onClick={() => setMaintFilterStatus(f)}
                                  className={`px-3 py-1.5 text-[10px] font-black uppercase rounded-lg cursor-pointer transition-all border-0 ${maintFilterStatus === f ? 'bg-white text-slate-800 shadow-sm' : 'text-slate-400 hover:text-slate-600 bg-transparent'
                                    }`}
                                >
                                  {f}
                                </button>
                              ))}
                            </div>
                          </div>

                          {/* Fleet Table list */}
                          <div className="bg-white rounded-3xl border border-slate-200/80 overflow-hidden shadow-sm">
                            <div className="overflow-x-auto">
                              <table className="w-full text-left text-xs font-semibold text-slate-500 border-collapse">
                                <thead>
                                  <tr className="bg-slate-50 border-b border-slate-200/80 text-[10px] text-slate-400 font-black uppercase tracking-wider">
                                    <th className="py-3.5 px-6">Vehicle info</th>
                                    <th className="py-3.5 px-6">Status label</th>
                                    <th className="py-3.5 px-6 text-center">Critical issues</th>
                                    <th className="py-3.5 px-6 text-center">Warning issues</th>
                                    <th className="py-3.5 px-6 text-right">Min Component Health</th>
                                    <th className="py-3.5 px-6 text-right">Actions</th>
                                  </tr>
                                </thead>
                                <tbody className="divide-y divide-slate-100">
                                  {maintFleetSummary && maintFleetSummary.fleet && maintFleetSummary.fleet
                                    .filter(v => {
                                      if (!v) return false;
                                      const regNo = (v.reg_no || '').toLowerCase();
                                      return maintSearchTerm === '' || regNo.includes((maintSearchTerm || '').toLowerCase());
                                    })
                                    .filter(v => v && (maintFilterStatus === 'all' || v.overall_status === maintFilterStatus))
                                    .map((v, vi) => {
                                      const regNo = v.reg_no || v.vehicle_id || 'Unknown';
                                      const make = v.make || 'Vehicle';
                                      const model = v.model || '';
                                      const vehicleId = v.vehicle_id || '';
                                      const overallStatus = v.overall_status || 'ok';
                                      const criticalCount = v.critical_count || 0;
                                      const warningCount = v.warning_count || 0;
                                      const minHealth = v.min_health !== undefined && v.min_health !== null ? parseFloat(v.min_health) : 100.0;
                                      return (
                                        <tr key={vi} className="hover:bg-slate-50/60 transition-colors">
                                          <td className="py-4 px-6">
                                            <div className="flex items-center gap-3">
                                              <div className="w-9 h-9 rounded-xl bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-500 font-black font-outfit shrink-0">
                                                {regNo.substring(0, 2)}
                                              </div>
                                              <div>
                                                <span className="text-slate-800 font-bold block">{regNo}</span>
                                                <span className="text-[10px] text-slate-400">{make} {model} {vehicleId && `(${vehicleId})`}</span>
                                              </div>
                                            </div>
                                          </td>
                                          <td className="py-4 px-6">
                                            <span className={`text-[9px] px-2 py-0.5 rounded-full font-black border uppercase tracking-wider ${overallStatus === 'critical' ? 'bg-rose-50 text-rose-700 border-rose-200' :
                                                overallStatus === 'warning' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                                                  'bg-emerald-50 text-emerald-700 border-emerald-200'
                                              }`}>
                                              {overallStatus}
                                            </span>
                                          </td>
                                          <td className="py-4 px-6 text-center text-slate-800 font-black">{criticalCount}</td>
                                          <td className="py-4 px-6 text-center text-slate-800 font-black">{warningCount}</td>
                                          <td className="py-4 px-6 text-right text-slate-800 font-black">
                                            <span className={minHealth < 30.0 ? 'text-rose-600 animate-pulse' : 'text-slate-800'}>
                                              {minHealth.toFixed(1)}%
                                            </span>
                                          </td>
                                          <td className="py-4 px-6 text-right">
                                            <button
                                              onClick={() => {
                                                openMaintenanceDashboard(vehicleId);
                                                setActiveMaintTab('vehicle');
                                              }}
                                              className="text-[10px] font-bold text-brand-600 hover:text-brand-700 bg-brand-50 hover:bg-brand-100 border border-brand-100 rounded-xl px-2.5 py-1.5 transition-all cursor-pointer outline-none"
                                            >
                                              Load Wear diagnostics
                                            </button>
                                          </td>
                                        </tr>
                                      );
                                    })}
                                </tbody>
                              </table>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>

                    {/* Modal Footer */}
                    <div className="px-6 py-4 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between shrink-0">
                      <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
                        <Info className="w-3.5 h-3.5 text-slate-400" />
                        <span>Computed live via SQL Server component wear integrations and FMC650 G-force models.</span>
                      </div>
                      <button
                        onClick={() => onClose()}
                        className="px-5 py-2.5 bg-slate-800 hover:bg-slate-900 active:scale-95 text-white text-xs font-bold font-outfit rounded-xl transition-all cursor-pointer shadow-sm border-0 outline-none"
                      >
                        Close View
                      </button>
                    </div>
                  </div>
                </div>
  );
}
