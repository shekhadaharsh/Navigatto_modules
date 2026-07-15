import React from 'react';
import {
  ArrowLeft, ArrowRight, Compass, Truck, Navigation, Clock, MapPin, Gauge, Activity,
  TrendingUp, TrendingDown, ShieldAlert, ShieldCheck, Droplet, AlertTriangle, RefreshCw,
  CheckCircle2, ChevronRight, Wrench, Battery, Thermometer, Upload
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, Cell, LineChart, Line, XAxis, YAxis,
  CartesianGrid, Tooltip, Legend, AreaChart, Area
} from 'recharts';
import TheftLocationMap from './TheftLocationMap';
import { InsightIcon, getDriverInsights } from '../utils/insights';

export default function TripDiagnostics({
  mobileViewTab,
  setMobileViewTab,
  isLoadingDetails,
  journeyDetails,
  isScoreCardFlipped,
  setIsScoreCardFlipped,
  isMaintCardFlipped,
  setIsMaintCardFlipped,
  activeFuelAlert,
  setActiveFuelAlert,
  openMaintenanceDashboard,
  maintHealthData,
  isSidebarCollapsed,
  setIsSidebarCollapsed,
  handleRecompute,
  handleAckAlert
}) {
  const handleReceiptUpload = async (logId, file) => {
    if (!file) return;
    
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const response = await fetch(`/api/fuel/upload-receipt/${logId}`, {
        method: "POST",
        body: formData,
      });
      
      if (!response.ok) {
        const errorData = await response.json();
        alert(errorData.detail || "Failed to upload receipt.");
        return;
      }
      
      const result = await response.json();
      if (result.theft_type === "INVALID_RECEIPT_DATE") {
        alert(`🚨 Alert! Fraud detected: The receipt date does not match the vehicle's actual refuel date!`);
      } else if (result.theft_type === "INVALID_RECEIPT_TIME") {
        alert(`🚨 Alert! Fraud detected: The receipt time does not match the vehicle's actual refuel time!`);
      } else if (result.status === "THEFT_DETECTED") {
        alert(`🚨 Alert! Discrepancy of ${result.discrepancy_liters}L detected between receipt and sensor!`);
      } else {
        alert("Refuel bill parsed and reconciled successfully!");
      }
      
      if (handleRecompute) {
        handleRecompute();
      }
    } catch (error) {
      console.error("Error uploading receipt:", error);
      alert("An error occurred while uploading the receipt.");
    }
  };

  return (
              <section className={`flex-1 bg-slate-50 flex flex-col overflow-hidden relative ${mobileViewTab === 'details' ? 'flex' : 'hidden lg:flex'
                }`}>

                {/* Loading Overlay */}
                {isLoadingDetails && (
                  <div className="absolute inset-0 bg-white/70 backdrop-blur-sm z-50 flex flex-col items-center justify-center gap-3">
                    <div className="w-10 h-10 border-4 border-brand-500/20 border-t-brand-500 rounded-full animate-spin"></div>
                    <span className="text-xs text-slate-500 font-bold tracking-wide">Fusing telemetry models...</span>
                  </div>
                )}

                {/* Empty state when no trip is selected */}
                {!journeyDetails ? (
                  <div className="flex-1 flex flex-col items-center justify-center p-8 text-center text-slate-400">
                    <button
                      onClick={() => setMobileViewTab('journeys')}
                      className="lg:hidden mb-6 flex items-center gap-1.5 px-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs font-bold text-slate-600 shadow-sm"
                    >
                      <ArrowLeft className="w-4 h-4" /> Back to Journeys
                    </button>
                    <div className="bg-white p-4 rounded-3xl shadow-premium border border-slate-100/50 mb-4 text-brand-500">
                      <Compass className="w-12 h-12" />
                    </div>
                    <h3 className="text-lg font-bold font-outfit text-slate-800 mb-1">Select a Journey</h3>
                    <p className="text-xs max-w-xs leading-relaxed">Choose a journey on the left to analyze safety scores, fuel theft forensics, fuel predictions, and real-time maintenance warnings.</p>
                  </div>
                ) : (
                  <div className="flex-1 flex flex-col overflow-hidden animate-fade-in">

                    {/* Trip Ribbon Header */}
                    <div className="p-5 bg-white border-b border-slate-200/80 flex flex-col md:flex-row md:items-center justify-between gap-4 shrink-0 shadow-sm">
                      
                      {/* Left: Time and Vehicle classification */}
                      <div className="flex flex-col gap-1">
                        <div className="flex items-center gap-2 text-slate-800 font-bold text-sm font-outfit">
                          <button
                            onClick={() => setMobileViewTab('journeys')}
                            className="lg:hidden p-1.5 hover:bg-slate-100 rounded-xl text-slate-500 transition-colors shrink-0"
                          >
                            <ArrowLeft className="w-5 h-5" />
                          </button>
                          <span>{journeyDetails.journey.start_time}</span>
                          <span className="text-slate-400 font-medium">to</span>
                          <span>{journeyDetails.journey.end_time ? String(journeyDetails.journey.end_time).split(' ')[1] || journeyDetails.journey.end_time : 'Active'}</span>
                        </div>
                        <div className="flex items-center gap-2 text-[10px] text-slate-400 font-extrabold uppercase tracking-wider">
                          <span>{journeyDetails.journey.route_type} route</span>
                          {journeyDetails.journey.vehicle_type && (
                            <>
                              <span className="w-1.5 h-1.5 rounded-full bg-slate-200"></span>
                              <span className="text-slate-500 flex items-center gap-0.5">
                                <Truck className="w-3.5 h-3.5 text-brand-500" />
                                {journeyDetails.journey.vehicle_type}
                              </span>
                            </>
                          )}
                        </div>
                      </div>

                      {/* Right: Key metrics */}
                      <div className="flex items-center gap-5">
                        <div className="text-left md:text-right">
                          <span className="block text-[9px] text-slate-400 font-bold uppercase tracking-wider leading-none mb-1">Distance</span>
                          <span className="text-xs font-black font-outfit text-slate-800">{journeyDetails.journey.distance_km} km</span>
                        </div>
                        <div className="w-px h-6 bg-slate-200"></div>
                        <div className="text-left md:text-right">
                          <span className="block text-[9px] text-slate-400 font-bold uppercase tracking-wider leading-none mb-1">Duration</span>
                          <span className="text-xs font-black font-outfit text-slate-800">{journeyDetails.journey.duration_min} mins</span>
                        </div>
                        <div className="w-px h-6 bg-slate-200"></div>
                        <div className="text-left md:text-right">
                          <span className="block text-[9px] text-slate-400 font-bold uppercase tracking-wider leading-none mb-1">Stops</span>
                          <span className="text-xs font-black font-outfit text-slate-800">{journeyDetails.journey.stops} stops</span>
                        </div>
                      </div>

                    </div>

                    {/* Dashboard Cards Grid Container */}
                    <div className="flex-1 overflow-y-auto p-6 space-y-6">

                      {/* 1 Column Vertical List of Modules */}
                      <div className="grid grid-cols-1 gap-6">

                        {/* -------------------- CARD 1: DRIVER SCORE CARD WITH 3D FLIP -------------------- */}
                        {(() => {
                          const ML_ACTIVE = journeyDetails?.driver_score?.score_comparison?.active_method === "ML";
                          return (
                            <div
                              className={`w-full perspective-1000 select-none ${ML_ACTIVE ? 'cursor-pointer' : ''}`}
                              onClick={() => {
                                if (ML_ACTIVE) {
                                  setIsScoreCardFlipped(!isScoreCardFlipped);
                                }
                              }}
                              style={{ minHeight: '480px' }}
                            >
                              <div
                                className={`relative w-full transition-transform duration-700 preserve-3d h-full ${isScoreCardFlipped ? 'rotate-y-180' : ''
                                  }`}
                                style={{ transformStyle: 'preserve-3d', minHeight: '480px' }}
                              >
                                {/* FRONT FACE */}
                                <div className="absolute inset-0 w-full h-full backface-hidden bg-white rounded-3xl border border-slate-200/80 p-6 shadow-premium hover:shadow-premium-lg transition-all flex flex-col justify-start gap-3 z-10" style={{ backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden' }}>
                                  <div>
                                    <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3.5 mb-4">
                                      <h3 className="text-sm font-extrabold text-slate-800 font-outfit tracking-wide flex items-center gap-2 uppercase">
                                        {ML_ACTIVE ? (
                                          <>
                                            <Gauge className="w-4.5 h-4.5 text-violet-500 animate-pulse" /> Driver Safety Score <span className="text-[10px] bg-violet-50 border border-violet-200 text-violet-600 px-1.5 py-0.5 rounded-md font-bold">🤖 AI</span>
                                          </>
                                        ) : (
                                          <>
                                            <Gauge className="w-4.5 h-4.5 text-brand-500" /> Driver Safety Score
                                          </>
                                        )}
                                      </h3>
                                      <div className="flex items-center gap-2">
                                        {ML_ACTIVE && (
                                          <span className="text-[9px] text-slate-400 font-bold bg-slate-50 border border-slate-100 px-2 py-0.5 rounded-full select-none">
                                            Click to compare
                                          </span>
                                        )}
                                        <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${(journeyDetails?.driver_score || {}).score >= 80
                                            ? 'bg-blue-50 text-blue-700 border-blue-200'
                                            : ((journeyDetails?.driver_score || {}).score >= 60
                                              ? 'bg-amber-50 text-amber-700 border-amber-200'
                                              : 'bg-rose-50 text-rose-700 border-rose-200')
                                          }`}>
                                          {(journeyDetails?.driver_score || {}).label} Classification
                                        </span>
                                      </div>
                                    </div>

                                    {/* Circular Score Gauge & Layout */}
                                    <div className="flex flex-col sm:flex-row items-center justify-center gap-6 sm:gap-8 mb-5 w-full">
                                      {/* Circle Progress bar */}
                                      <div className="relative w-32 h-32 shrink-0 flex items-center justify-center bg-slate-50/50 rounded-full p-2 border border-slate-100/50 shadow-inner">
                                        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                                          <defs>
                                            {/* Premium Gradients for Score classification */}
                                            <linearGradient id="scoreBlue" x1="0%" y1="0%" x2="100%" y2="100%">
                                              <stop offset="0%" stopColor="#3b82f6" />
                                              <stop offset="100%" stopColor="#1d4ed8" />
                                            </linearGradient>
                                            <linearGradient id="scoreAmber" x1="0%" y1="0%" x2="100%" y2="100%">
                                              <stop offset="0%" stopColor="#f59e0b" />
                                              <stop offset="100%" stopColor="#d97706" />
                                            </linearGradient>
                                            <linearGradient id="scoreRose" x1="0%" y1="0%" x2="100%" y2="100%">
                                              <stop offset="0%" stopColor="#f43f5e" />
                                              <stop offset="100%" stopColor="#e11d48" />
                                            </linearGradient>

                                            {/* Glassmorphic concentric backgrounds */}
                                            <radialGradient id="innerCircleBg" cx="50%" cy="50%" r="50%">
                                              <stop offset="0%" stopColor="#ffffff" stopOpacity="1" />
                                              <stop offset="70%" stopColor="#f8fafc" stopOpacity="0.8" />
                                              <stop offset="100%" stopColor="#e2e8f0" stopOpacity="0.3" />
                                            </radialGradient>
                                          </defs>

                                          {/* Telemetry Dial Outer Ring Accent */}
                                          <circle
                                            className="text-slate-200/40"
                                            strokeWidth="0.5"
                                            strokeDasharray="2 3"
                                            stroke="currentColor"
                                            fill="transparent"
                                            r="46"
                                            cx="50"
                                            cy="50"
                                          />

                                          {/* Background track circle */}
                                          <circle
                                            className="text-slate-100"
                                            strokeWidth="7"
                                            stroke="currentColor"
                                            fill="url(#innerCircleBg)"
                                            r="40"
                                            cx="50"
                                            cy="50"
                                          />

                                          {/* Colored indicator circle */}
                                          <circle
                                            className="transition-all duration-1000"
                                            strokeWidth="7"
                                            strokeDasharray="251.2"
                                            strokeDashoffset={251.2 - (251.2 * (journeyDetails?.driver_score || {}).score) / 100}
                                            strokeLinecap="round"
                                            stroke={
                                              (journeyDetails?.driver_score || {}).score >= 80
                                                ? 'url(#scoreBlue)'
                                                : ((journeyDetails?.driver_score || {}).score >= 60 ? 'url(#scoreAmber)' : 'url(#scoreRose)')
                                            }
                                            fill="transparent"
                                            r="40"
                                            cx="50"
                                            cy="50"
                                          />
                                        </svg>
                                        <div className="absolute text-center">
                                          <span className="text-4xl font-black font-outfit text-slate-800 block leading-none">{(journeyDetails?.driver_score || {}).score}</span>
                                          <span className="text-[10px] text-slate-400 font-bold uppercase mt-1 tracking-wider">out of 100</span>
                                        </div>
                                      </div>

                                      {/* Quick Stats on events */}
                                      <div className="w-full sm:max-w-[210px] space-y-1.5 text-[11px] shrink-0">
                                        <div className="flex items-center justify-between gap-2 text-slate-600 p-1 hover:bg-slate-50 rounded-xl transition-all duration-200">
                                          <span className="font-bold text-slate-600 flex items-center gap-2 select-none shrink-0">
                                            <span className={`w-2 h-2 rounded-full shrink-0 ${journeyDetails.journey.acceleration_events === 0 ? 'bg-blue-500 shadow-sm shadow-blue-400' : (journeyDetails.journey.acceleration_events < 4 ? 'bg-amber-500' : 'bg-rose-500')
                                              }`} />
                                            Harsh Accelerations
                                          </span>
                                          <span className="font-extrabold text-slate-700 shrink-0 bg-slate-100/80 px-2 py-0.5 rounded-lg text-[9.5px] font-outfit select-none">
                                            {journeyDetails.journey.acceleration_events} events
                                          </span>
                                        </div>
                                        <div className="flex items-center justify-between gap-2 text-slate-600 p-1 hover:bg-slate-50 rounded-xl transition-all duration-200">
                                          <span className="font-bold text-slate-600 flex items-center gap-2 select-none shrink-0">
                                            <span className={`w-2 h-2 rounded-full shrink-0 ${journeyDetails.journey.brake_events === 0 ? 'bg-blue-500 shadow-sm shadow-blue-400' : (journeyDetails.journey.brake_events < 4 ? 'bg-amber-500' : 'bg-rose-500')
                                              }`} />
                                            Harsh Braking
                                          </span>
                                          <span className="font-extrabold text-slate-700 shrink-0 bg-slate-100/80 px-2 py-0.5 rounded-lg text-[9.5px] font-outfit select-none">
                                            {journeyDetails.journey.brake_events} events
                                          </span>
                                        </div>
                                        <div className="flex items-center justify-between gap-2 text-slate-600 p-1 hover:bg-slate-50 rounded-xl transition-all duration-200">
                                          <span className="font-bold text-slate-600 flex items-center gap-2 select-none shrink-0">
                                            <span className={`w-2 h-2 rounded-full shrink-0 ${journeyDetails.journey.overspeed_count === 0 ? 'bg-blue-500 shadow-sm shadow-blue-400' : (journeyDetails.journey.overspeed_count < 2 ? 'bg-amber-500' : 'bg-rose-500')
                                              }`} />
                                            Overspeeding
                                          </span>
                                          <span className="font-extrabold text-slate-700 shrink-0 bg-slate-100/80 px-2 py-0.5 rounded-lg text-[9.5px] font-outfit select-none">
                                            {journeyDetails.journey.overspeed_count} events
                                          </span>
                                        </div>
                                        <div className="flex items-center justify-between gap-2 text-slate-600 p-1 hover:bg-slate-50 rounded-xl transition-all duration-200">
                                          <span className="font-bold text-slate-600 flex items-center gap-2 select-none shrink-0">
                                            <span className={`w-2 h-2 rounded-full shrink-0 ${(journeyDetails.journey.idle_time_min || 0) < 10 ? 'bg-blue-500 shadow-sm shadow-blue-400' : ((journeyDetails.journey.idle_time_min || 0) < 25 ? 'bg-amber-500' : 'bg-rose-500')
                                              }`} />
                                            Idling Time
                                          </span>
                                          <span className="font-extrabold text-slate-700 shrink-0 bg-slate-100/80 px-2 py-0.5 rounded-lg text-[9.5px] font-outfit select-none">
                                            {(journeyDetails.journey.idle_time_min || 0).toFixed(1)} mins
                                          </span>
                                        </div>
                                      </div>
                                    </div>
                                  </div>

                                  {/* Telematics Coaching Insights */}
                                  {(() => {
                                    const insights = getDriverInsights(journeyDetails);
                                    const topInsight = insights[0] || {
                                      text: "Excellent defensive driving! All safety metrics are within optimal thresholds.",
                                      icon: "CheckCircle2",
                                      color: "text-blue-600 bg-blue-50 border-blue-100",
                                      chipLabel: "🏆 CLASS LEADER",
                                      chipStyle: "bg-blue-50 text-blue-700 border-blue-200/50",
                                      estimate: "Est. Impact: All systems operating at peak safety"
                                    };
                                    return (
                                      <div className="bg-slate-50/70 rounded-2xl border border-slate-200/50 p-4 transition-all duration-300 hover:bg-slate-50/95 hover:-translate-y-0.5 hover:shadow-premium-sm">
                                        <div className="flex items-center justify-between gap-2 mb-3">
                                          <span className="text-[10px] font-extrabold tracking-wider uppercase bg-gradient-to-r from-violet-600 via-indigo-600 to-blue-600 bg-clip-text text-transparent flex items-center gap-1.5 select-none">
                                            <Activity className="w-3.5 h-3.5 text-violet-500 animate-pulse" /> Telematics AI Coach
                                          </span>
                                          <span className={`text-[8px] font-extrabold px-2 py-0.5 rounded-full border tracking-wider select-none shrink-0 ${topInsight.chipStyle}`}>
                                            {topInsight.chipLabel}
                                          </span>
                                        </div>
                                        <div className="flex gap-3.5 items-start">
                                          <div className={`p-2.5 rounded-xl shrink-0 border ${topInsight.color} flex items-center justify-center shadow-sm`}>
                                            <InsightIcon iconType={topInsight.icon} className="w-5 h-5 animate-bounce-slow" />
                                          </div>
                                          <div className="flex flex-col gap-1 min-w-0">
                                            <div className="text-[11px] font-bold text-slate-700 leading-relaxed">
                                              {topInsight.text}
                                            </div>
                                            <div className="text-[9.5px] font-bold text-slate-400 italic">
                                              {topInsight.estimate}
                                            </div>
                                          </div>
                                        </div>
                                      </div>
                                    );
                                  })()}
                                </div>

                                {/* BACK FACE (ML DUAL SCORE COMPARISON) */}
                                {ML_ACTIVE && journeyDetails?.driver_score?.score_comparison && (
                                  <div
                                    className="absolute inset-0 w-full h-full backface-hidden rotate-y-180 bg-white rounded-3xl border border-slate-200/80 p-6 shadow-premium hover:shadow-premium-lg transition-all flex flex-col justify-between z-0"
                                    style={{ backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
                                  >
                                    <div>
                                      <div className="flex items-center justify-between border-b border-slate-100 pb-3 mb-4 shrink-0">
                                        <h3 className="text-sm font-extrabold text-slate-800 font-outfit tracking-wide flex items-center gap-2 uppercase">
                                          <Gauge className="w-4.5 h-4.5 text-violet-500 animate-pulse" /> Model Dual Comparison
                                        </h3>
                                        <span className="text-[9px] bg-slate-50 border border-slate-100 text-slate-400 px-2 py-0.5 rounded-full font-bold">
                                          Click to flip back
                                        </span>
                                      </div>

                                      {/* Side-by-side Score blocks */}
                                      <div className="grid grid-cols-2 gap-4 mb-4 shrink-0">
                                        {/* ML Model Block */}
                                        <div className="bg-violet-50/20 rounded-2xl p-3 border border-violet-100 relative overflow-hidden">
                                          <span className="text-[9px] text-violet-600 font-bold uppercase tracking-wider block mb-1">🤖 ML XGBoost</span>
                                          <div className="flex items-baseline gap-1.5">
                                            <span className="text-2xl font-black font-outfit text-violet-700">
                                              {(journeyDetails?.driver_score || {}).score_comparison.ml.final_score}
                                            </span>
                                            <span className="text-[10px] text-violet-400 font-bold">/100</span>
                                          </div>
                                          <span className="text-[9.5px] font-bold text-violet-500 italic animate-pulse">
                                            {(journeyDetails?.driver_score || {}).score_comparison.ml.risk_level}
                                          </span>
                                        </div>

                                        {/* Rule-Based Block */}
                                        <div className="bg-slate-50/70 rounded-2xl p-3 border border-slate-200/40 relative overflow-hidden">
                                          <span className="text-[9px] text-slate-400 font-bold uppercase tracking-wider block mb-1">📐 Rule-Based</span>
                                          <div className="flex items-baseline gap-1.5">
                                            <span className="text-2xl font-black font-outfit text-slate-700">
                                              {(journeyDetails?.driver_score || {}).score_comparison.rule_based.final_score}
                                            </span>
                                            <span className="text-[10px] text-slate-400 font-bold">/100</span>
                                          </div>
                                          <span className="text-[9.5px] font-bold text-slate-400 italic">
                                            {(journeyDetails?.driver_score || {}).score_comparison.rule_based.risk_level}
                                          </span>
                                        </div>
                                      </div>

                                      {/* Score gap badge & ML confidence */}
                                      <div className="space-y-3.5 mb-4 shrink-0">
                                        {/* Score Difference Gap */}
                                        {(() => {
                                          const diff = (journeyDetails?.driver_score || {}).score_comparison.score_difference;
                                          const absDiff = Math.abs(diff);
                                          let colorClass = "bg-blue-50 text-blue-700 border-blue-100";
                                          let gapLabel = "Models Agree";
                                          if (absDiff >= 15.0) {
                                            colorClass = "bg-rose-50 text-rose-700 border-rose-100";
                                            gapLabel = "Context Gap Detected";
                                          } else if (absDiff >= 5.0) {
                                            colorClass = "bg-amber-50 text-amber-700 border-amber-100";
                                            gapLabel = "Minor Difference";
                                          }
                                          return (
                                            <div className={`py-2 px-3 rounded-xl border flex items-center justify-between text-xs font-semibold ${colorClass}`}>
                                              <span>Divergence Gap:</span>
                                              <span className="font-black font-outfit">
                                                {diff > 0 ? `▲ +${diff}` : `▼ ${diff}`} pts ({gapLabel})
                                              </span>
                                            </div>
                                          );
                                        })()}
                                      </div>
                                    </div>

                                    {/* Category Safety Grades / Scores */}
                                    <div className="space-y-2 border-t border-slate-100 pt-3 flex-1 flex flex-col justify-center">
                                      <span className="text-[9.5px] text-slate-400 font-extrabold tracking-wide uppercase block select-none">
                                        Safety Component Analysis (ML Context-Aware)
                                      </span>
                                      <div className="space-y-2.5 pr-1">
                                        {(() => {
                                          const compScores = journeyDetails?.driver_score?.score_comparison?.ml?.component_scores || {};
                                          const cats = [
                                            { name: "Acceleration", val: compScores.accel_score ?? 100.0, icon: <TrendingUp className="w-4 h-4 shrink-0" /> },
                                            { name: "Braking", val: compScores.braking_score ?? 100.0, icon: <ShieldAlert className="w-4 h-4 shrink-0" /> },
                                            { name: "Speeding", val: compScores.speeding_score ?? 100.0, icon: <Gauge className="w-4 h-4 shrink-0" /> },
                                            { name: "Cornering", val: compScores.cornering_score ?? 100.0, icon: <Compass className="w-4 h-4 shrink-0" /> },
                                            { name: "Idling", val: compScores.idle_score ?? 100.0, icon: <Clock className="w-4 h-4 shrink-0" /> }
                                          ];

                                          return cats.map(c => {
                                            let barColor = "bg-blue-500";
                                            let textColor = "text-blue-700 bg-blue-50 border-blue-100";
                                            if (c.val < 60) {
                                              barColor = "bg-rose-500";
                                              textColor = "text-rose-700 bg-rose-50 border-rose-100";
                                            } else if (c.val < 80) {
                                              barColor = "bg-amber-500";
                                              textColor = "text-amber-700 bg-amber-50 border-amber-100";
                                            }
                                            return (
                                              <div key={c.name} className="flex flex-col gap-0.5 text-[11px]">
                                                <div className="flex items-center justify-between font-bold">
                                                  <span className="text-slate-500 flex items-center gap-1.5 min-w-0 truncate">
                                                    {c.icon} {c.name}
                                                  </span>
                                                  <span className={`text-[10px] px-1.5 py-0.2 border rounded-md font-extrabold ${textColor}`}>
                                                    {c.val.toFixed(0)}%
                                                  </span>
                                                </div>
                                                <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden w-full">
                                                  <div className={`h-full ${barColor} rounded-full transition-all duration-500`} style={{ width: `${c.val}%` }}></div>
                                                </div>
                                              </div>
                                            );
                                          });
                                        })()}
                                      </div>
                                    </div>
                                  </div>
                                )}

                              </div>
                            </div>
                          );
                        })()}

                        {/* -------------------- CARD 2: FUEL THEFT CARD -------------------- */}
                        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-premium flex flex-col justify-between hover:shadow-premium-lg transition-shadow">
                          {(() => {
                            const hasRefuelTheft = journeyDetails?.fuel_theft?.refuel_stops?.some(s => s.is_fuel_theft) || false;
                            const refuelTheftAmount = journeyDetails?.fuel_theft?.refuel_stops?.find(s => s.is_fuel_theft)?.theft_amount_liters || 0.0;
                            const isTheft = journeyDetails?.fuel_theft?.detected || hasRefuelTheft;
                            const confidence = hasRefuelTheft ? 90.0 : (journeyDetails?.fuel_theft?.confidence || 5.0);
                            return (
                              <>
                                <div>
                                  <div className="flex items-center justify-between border-b border-slate-100 pb-3.5 mb-4">
                                    <h3 className="text-sm font-extrabold text-slate-800 font-outfit tracking-wide flex items-center gap-2 uppercase">
                                      <Droplet className="w-4.5 h-4.5 text-brand-500" /> Fuel Theft Detection
                                    </h3>
                                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${isTheft
                                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                                        : 'bg-blue-50 text-blue-700 border-blue-200'
                                      }`}>
                                      {isTheft ? 'ALERT HIGH RISK' : 'NORMAL SECURED'}
                                    </span>
                                  </div>

                                  {/* Status pulsing bar */}
                                  <div className={`p-4 rounded-2xl flex flex-col sm:flex-row xl:flex-col 2xl:flex-row items-start sm:items-center xl:items-start 2xl:items-center gap-4 mb-5 border transition-all ${isTheft
                                      ? 'bg-rose-50/50 border-rose-200/50 pulse-glow-red'
                                      : 'bg-blue-50/50 border-blue-200/50'
                                    }`}>
                                    <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${isTheft ? 'bg-rose-500 text-white' : 'bg-blue-500 text-white'
                                      }`}>
                                      {isTheft ? <ShieldAlert className="w-5 h-5" /> : <ShieldCheck className="w-5 h-5" />}
                                    </div>
                                    <div className="flex-1 min-w-0">
                                      <p className="text-xs text-slate-400 font-bold tracking-wide uppercase">Fuel Security Monitor</p>
                                      <p className="text-sm font-extrabold text-slate-800 font-outfit break-words">
                                        {isTheft
                                          ? `Fuel theft event suspected (Confidence: ${confidence}%)`
                                          : "No suspicious fuel variations identified."
                                        }
                                      </p>
                                    </div>
                                  </div>
                                </div>

                                {/* Theft Forensics Details */}
                                <div className="bg-slate-50 rounded-2xl border border-slate-200/50 p-4 flex-1 flex flex-col justify-center">
                                  <span className="text-[9px] text-slate-400 font-bold tracking-wide uppercase block mb-2">Suspected Forensics Check</span>
                                  {isTheft ? (
                                    <ul className="space-y-2 text-xs font-semibold text-slate-700">
                                      <div className="flex items-center justify-between mb-3 p-2.5 bg-rose-100/60 border border-rose-200 rounded-xl">
                                          <span className="text-xs font-bold text-rose-700">Total Fuel Stolen</span>
                                          <span className="text-sm font-black text-rose-700 font-outfit">
                                              {((journeyDetails?.fuel_theft?.total_theft_liters || 0) + refuelTheftAmount).toFixed(2)} L
                                          </span>
                                      </div>
                                      
                                      {/* Standard theft reasons from backend */}
                                      {journeyDetails?.fuel_theft?.reasons?.map((r, ri) => (
                                          <li key={ri} className="flex items-start gap-2 text-rose-600 bg-rose-50/50 border border-rose-100/50 p-2.5 rounded-xl">
                                              <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-rose-500" />
                                              <span>{r}</span>
                                          </li>
                                      ))}

                                      {/* Refuel discrepancy details */}
                                      {hasRefuelTheft && (
                                        <li className="flex items-start gap-2 text-rose-600 bg-rose-50/50 border border-rose-100/50 p-2.5 rounded-xl">
                                            <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-rose-500" />
                                            <span>Refuel theft: {refuelTheftAmount.toFixed(1)} L discrepancy detected between receipt and sensor</span>
                                        </li>
                                      )}
                                    </ul>
                                  ) : (
                                    <div className="space-y-2 text-xs font-semibold text-slate-500">
                                      <div className="flex items-center gap-2 py-1 border-b border-slate-200/30">
                                        <CheckCircle2 className="w-4.5 h-4.5 text-blue-500 shrink-0" />
                                        <span>No drops detected when ignition was OFF</span>
                                      </div>
                                      <div className="flex items-center gap-2 py-1 border-b border-slate-200/30">
                                        <CheckCircle2 className="w-4.5 h-4.5 text-blue-500 shrink-0" />
                                        <span>No refueling theft detected</span>
                                      </div>
                                      <div className="flex items-center gap-2">
                                        <CheckCircle2 className="w-4.5 h-4.5 text-blue-500 shrink-0" />
                                        <span>No sudden fuel drop while the vehicle was running</span>
                                      </div>
                                    </div>
                                  )}

                                  {/* Refueling Events / Receipt Uploads list */}
                                  {journeyDetails?.fuel_theft?.refuel_stops && journeyDetails.fuel_theft.refuel_stops.length > 0 && (
                                    <div className="mt-4 border-t border-slate-200/50 pt-3.5">
                                      <span className="text-[9px] text-slate-400 font-bold tracking-wide uppercase block mb-2">Refueling Logs & Receipts</span>
                                      <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
                                        {journeyDetails.fuel_theft.refuel_stops.map((stop) => (
                                          <div key={stop.id} className="p-3 bg-white rounded-xl border border-slate-200/60 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shadow-sm">
                                            <div className="min-w-0">
                                              <div className="flex flex-wrap items-center gap-2">
                                                <span className="text-xs font-bold text-slate-700">Refueled: {stop.refuel_amount_liters?.toFixed(1)} L</span>
                                                {stop.receipt_uploaded ? (
                                                  stop.is_fuel_theft ? (
                                                    <span className="text-[9px] px-1.5 py-0.5 bg-rose-50 text-rose-600 border border-rose-200 rounded font-bold uppercase tracking-wider">Theft Detected</span>
                                                  ) : (
                                                    <span className="text-[9px] px-1.5 py-0.5 bg-emerald-50 text-emerald-600 border border-emerald-200 rounded font-bold uppercase tracking-wider">Reconciled</span>
                                                  )
                                                ) : (
                                                  <span className="text-[9px] px-1.5 py-0.5 bg-amber-50 text-amber-600 border border-amber-200 rounded font-bold uppercase tracking-wider">Pending Bill</span>
                                                )}
                                              </div>
                                              <span className="text-[10px] text-slate-400 block mt-0.5">Time: {new Date(stop.event_time).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}</span>
                                              {stop.receipt_uploaded && (
                                                <div className="text-[10px] text-slate-500 mt-1">
                                                  Receipt Qty: <strong className="text-slate-700">{stop.receipt_amount_liters?.toFixed(1)} L</strong>
                                                  {stop.is_fuel_theft && (
                                                    <span className="text-rose-600 font-bold ml-1.5">
                                                      {stop.theft_type === "INVALID_RECEIPT_DATE" 
                                                        ? "(Date Mismatch!)" 
                                                        : stop.theft_type === "INVALID_RECEIPT_TIME" 
                                                          ? "(Time Mismatch!)" 
                                                          : `(${stop.theft_amount_liters?.toFixed(1)} L short!)`
                                                      }
                                                    </span>
                                                  )}
                                                </div>
                                              )}
                                            </div>
                                            
                                            <div className="shrink-0 flex items-center gap-2">
                                              <label className="cursor-pointer text-[10px] font-bold px-2.5 py-1.5 rounded-lg border border-brand-200 bg-brand-50/10 text-brand-700 hover:bg-brand-50 transition-colors flex items-center gap-1.5">
                                                <Upload className="w-3.5 h-3.5" />
                                                <span>{stop.receipt_uploaded ? "Update Bill" : "Upload Bill"}</span>
                                                <input 
                                                  type="file" 
                                                  accept="image/*" 
                                                  className="hidden" 
                                                  onChange={(e) => handleReceiptUpload(stop.id, e.target.files[0])}
                                                />
                                              </label>
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    </div>
                                  )}
                                </div>
                              </>
                            );
                          })()}
                        </div>

                        {/* -------------------- CARD 3: EXPECTED FUEL CHART -------------------- */}
                        <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-premium flex flex-col justify-between hover:shadow-premium-lg transition-shadow">
                          <div className="flex flex-col flex-1">
                            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-slate-100 pb-3.5 mb-4">
                              <h3 className="text-sm font-extrabold text-slate-800 font-outfit tracking-wide flex items-center gap-2 uppercase">
                                <Activity className="w-4.5 h-4.5 text-brand-500" /> Predictive Expected Fuel
                              </h3>
                              <div className="flex items-center gap-2">
                {journeyDetails?.expected_fuel?.source === "ml_model" && (
                  <span className="text-[10px] px-2 py-0.5 rounded-full font-bold border bg-violet-50 text-violet-700 border-violet-200 flex items-center gap-1">
                    🤖 AI Predicted
                  </span>
                )}
                <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${Math.abs(journeyDetails?.expected_fuel?.variance_pct) > 20
                    ? 'bg-rose-50 text-rose-700 border-rose-200'
                    : 'bg-blue-50 text-blue-700 border-blue-200'
                  }`}>
                  Variance: {journeyDetails?.expected_fuel?.variance_pct > 0 ? '+' : ''}{(journeyDetails?.expected_fuel?.variance_pct || 0).toFixed(1)}%
                </span>
              </div>
                            </div>
                            {/* Side-by-side Recharts bar chart */}
                            <div className="flex-1 min-h-[150px] w-full mt-3">
                              <ResponsiveContainer width="100%" height="100%">
                                <BarChart
                                  data={[
                                    { name: 'Predicted Expected', fuel: (journeyDetails?.expected_fuel?.expected_liters || 0), fill: '#3b82f6' },
                                    { name: 'Actual Consumed', fuel: (journeyDetails?.expected_fuel?.actual_liters || 0), fill: journeyDetails?.fuel_theft?.detected ? '#f43f5e' : '#f97316' }
                                  ]}
                                  margin={{ top: 20, right: 15, left: -20, bottom: 5 }}
                                  barSize={48}
                                >
                                  <defs>
                                    <linearGradient id="blueGrad" x1="0" y1="0" x2="0" y2="1">
                                      <stop offset="0%" stopColor="#3b82f6" stopOpacity={0.9} />
                                      <stop offset="100%" stopColor="#2563eb" stopOpacity={1} />
                                    </linearGradient>
                                    <linearGradient id="orangeGrad" x1="0" y1="0" x2="0" y2="1">
                                      <stop offset="0%" stopColor="#f97316" stopOpacity={0.9} />
                                      <stop offset="100%" stopColor="#ea580c" stopOpacity={1} />
                                    </linearGradient>
                                    <linearGradient id="redGrad" x1="0" y1="0" x2="0" y2="1">
                                      <stop offset="0%" stopColor="#f43f5e" stopOpacity={0.9} />
                                      <stop offset="100%" stopColor="#dc2626" stopOpacity={1} />
                                    </linearGradient>
                                  </defs>
                                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" opacity={0.6} />
                                  <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} fontWeight={700} tickLine={false} axisLine={false} dy={10} />
                                  <YAxis stroke="#94a3b8" fontSize={11} fontWeight={600} tickLine={false} axisLine={false} dx={-5} />
                                  <Tooltip cursor={{ fill: '#f8fafc' }} contentStyle={{ borderRadius: '16px', border: '1px solid #e2e8f0', boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)', fontSize: '12px', fontWeight: 'bold' }} />
                                  <Bar dataKey="fuel" radius={[6, 6, 0, 0]} background={{ fill: '#f1f5f9', radius: [6, 6, 0, 0] }} animationDuration={1500}>
                                    {
                                      [
                                        { fill: 'url(#blueGrad)' },
                                        { fill: journeyDetails?.fuel_theft?.detected ? 'url(#redGrad)' : 'url(#orangeGrad)' }
                                      ].map((entry, index) => (
                                        <Cell key={`cell-${index}`} fill={entry.fill} />
                                      ))
                                    }
                                  </Bar>
                                </BarChart>
                              </ResponsiveContainer>
                            </div>
                          </div>

                          {/* Adjustment parameters explanation removed per layout request */}
                        </div>

                        {/* -------------------- CARD 4: VEHICLE MAINTENANCE DIAGNOSTIC WITH 3D FLIP -------------------- */}
                        <div
                          className="w-full perspective-1000 select-none cursor-pointer"
                          onClick={() => {
                            setIsMaintCardFlipped(!isMaintCardFlipped);
                          }}
                          style={{ minHeight: '520px' }}
                        >
                          <div
                            className={`relative w-full transition-transform duration-700 preserve-3d h-full ${isMaintCardFlipped ? 'rotate-y-180' : ''}`}
                            style={{ transformStyle: 'preserve-3d', minHeight: '520px' }}
                          >
                            {/* FRONT FACE */}
                            <div
                              className="absolute inset-0 w-full h-full backface-hidden bg-white rounded-3xl border border-slate-200/80 p-6 shadow-premium hover:shadow-premium-lg transition-all flex flex-col justify-between z-10"
                              style={{ backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden' }}
                            >
                              <div>
                                <div className="flex items-center justify-between border-b border-slate-100 pb-3.5 mb-4">
                                  <h3 className="text-sm font-extrabold text-slate-800 font-outfit tracking-wide flex items-center gap-2 uppercase">
                                    <Wrench className="w-4.5 h-4.5 text-brand-500" /> Vehicle Maintenance diagnostics
                                  </h3>
                                  <div className="flex items-center gap-2">
                                    <button
                                      onClick={(e) => {
                                        e.stopPropagation();
                                        setIsMaintCardFlipped(true);
                                      }}
                                      className="text-[10px] bg-brand-50 hover:bg-brand-100 border border-brand-200 text-brand-700 px-2.5 py-1 rounded-xl font-bold transition-all flex items-center gap-1 cursor-pointer shadow-sm active:scale-95"
                                    >
                                      <Activity className="w-3.5 h-3.5" /> Wear Details
                                    </button>
                                    <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${(journeyDetails?.maintenance?.priority || 'OK') === 'Critical'
                                        ? 'bg-rose-50 text-rose-700 border-rose-200'
                                        : ((journeyDetails?.maintenance?.priority || 'OK') === 'Warning'
                                          ? 'bg-amber-50 text-amber-700 border-amber-200'
                                          : 'bg-blue-50 text-blue-700 border-blue-200')
                                      }`}>
                                      {(journeyDetails?.maintenance?.priority || 'OK')}
                                    </span>
                                  </div>
                                </div>

                                {/* Sensory parameters diagnostics */}
                                <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-2 gap-4 mb-4">
                                  <div className={`p-3 rounded-2xl border transition-all ${journeyDetails.journey.external_voltage < 11.5 ? 'bg-rose-50 border-rose-200' : 'bg-slate-50 border-slate-200/40'
                                    }`}>
                                    <div className="flex items-center gap-2 text-slate-400 mb-1.5">
                                      <Battery className={`w-4.5 h-4.5 ${journeyDetails.journey.external_voltage < 11.5 ? 'text-rose-500 animate-pulse' : 'text-slate-400'}`} />
                                      <span className="text-[10px] font-bold uppercase">Battery Voltage</span>
                                    </div>
                                    <p className={`text-base font-black font-outfit ${journeyDetails.journey.external_voltage < 11.5 ? 'text-rose-700' : 'text-slate-800'}`}>
                                      {(journeyDetails.journey.external_voltage || 0).toFixed(1)} V
                                    </p>
                                  </div>

                                  <div className={`p-3 rounded-2xl border transition-all ${journeyDetails.journey.dallas_temp_celsius > 100.0 ? 'bg-rose-50 border-rose-200' : 'bg-slate-50 border-slate-200/40'
                                    }`}>
                                    <div className="flex items-center gap-2 text-slate-400 mb-1.5">
                                      <Thermometer className={`w-4.5 h-4.5 ${journeyDetails.journey.dallas_temp_celsius > 100.0 ? 'text-rose-500 animate-pulse' : 'text-slate-400'}`} />
                                      <span className="text-[10px] font-bold uppercase">Engine Temp</span>
                                    </div>
                                    <p className={`text-base font-black font-outfit ${journeyDetails.journey.dallas_temp_celsius > 100.0 ? 'text-rose-700' : 'text-slate-800'}`}>
                                      {(journeyDetails.journey.dallas_temp_celsius || 0).toFixed(1)}°C
                                    </p>
                                  </div>
                                </div>

                                {/* Component Wear Health Scores Grid */}
                                <div className="border-t border-slate-100 pt-4 mt-1 mb-4 space-y-3">
                                  <span className="text-[9px] text-slate-400 font-bold tracking-wide uppercase block">Component Wear Health Scores</span>
                                  <div className="grid grid-cols-1 gap-2.5">
                                    {(() => {
                                      const scores = journeyDetails.maintenance?.health_scores || {
                                        brake: 100, tire: 100, battery: 100, engine: 100
                                      };
                                      return Object.entries(scores)
                                        .filter(([comp]) => comp !== 'clutch')
                                        .map(([comp, val]) => {
                                        const scoreVal = val ?? 100;
                                        const isCrit = scoreVal < 10;
                                        const isWarn = scoreVal >= 10 && scoreVal < 30;

                                        let colorClass = "from-blue-500 to-indigo-500";
                                        let textClass = "text-blue-600 bg-blue-50 border-blue-100";
                                        if (isCrit) {
                                          colorClass = "from-rose-500 to-red-600";
                                          textClass = "text-rose-600 bg-rose-50 border-rose-100";
                                        } else if (isWarn) {
                                          colorClass = "from-amber-500 to-orange-500";
                                          textClass = "text-amber-600 bg-amber-50 border-amber-100";
                                        }

                                        return (
                                          <div key={comp} className="flex items-center justify-between gap-3 text-xs font-semibold">
                                            <span className="w-16 capitalize text-slate-600 truncate">{comp}</span>
                                            <div className="flex-1 h-2 bg-slate-100 rounded-full overflow-hidden relative shadow-inner">
                                              <div
                                                className={`h-full rounded-full bg-gradient-to-r ${colorClass} transition-all duration-1000`}
                                                style={{ width: `${Math.max(0, Math.min(100, scoreVal))}%` }}
                                              ></div>
                                            </div>
                                            <span className={`text-[9.5px] font-bold font-outfit px-1.5 py-0.5 rounded border select-none shrink-0 w-11 text-center ${textClass}`}>
                                              {scoreVal.toFixed(0)}%
                                            </span>
                                          </div>
                                        );
                                      });
                                    })()}
                                  </div>
                                </div>
                              </div>

                              {/* Diagnostics list */}
                              <div className="bg-slate-50 rounded-2xl border border-slate-200/50 p-4 flex-1 flex flex-col justify-center">
                                <span className="text-[9px] text-slate-400 font-bold tracking-wide uppercase block mb-2">Predictive Issue Analyzer</span>
                                {(journeyDetails?.maintenance?.alerts || []).length > 0 ? (
                                  <div className="space-y-2.5">
                                    {(journeyDetails?.maintenance?.alerts || []).map((a, ai) => (
                                      <div key={ai} className={`text-xs p-2.5 rounded-xl border flex items-start gap-2.5 ${a.severity === 'Critical'
                                          ? 'bg-rose-50/50 border-rose-100 text-rose-700'
                                          : 'bg-amber-50/50 border-amber-100 text-amber-700'
                                        }`}>
                                        <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                                        <div className="flex-1">
                                          <div className="flex items-start justify-between gap-2">
                                            <p className="font-extrabold font-outfit leading-none mb-1">{a.issue}</p>
                                            {a.id && (
                                              <button
                                                onClick={(e) => {
                                                  e.stopPropagation();
                                                  handleAckAlert(a.id);
                                                }}
                                                className="text-[9px] font-bold bg-white/80 hover:bg-white text-slate-700 px-1.5 py-0.5 rounded-md border border-slate-200 shadow-sm transition-all cursor-pointer select-none active:scale-95 shrink-0"
                                              >
                                                Resolve
                                              </button>
                                            )}
                                          </div>
                                          <p className="text-[11px] font-semibold text-slate-500 leading-snug">{a.detail}</p>
                                        </div>
                                      </div>
                                    ))}
                                  </div>
                                ) : (
                                  <div className="text-center py-4 space-y-1 text-slate-400">
                                    <CheckCircle2 className="w-8 h-8 text-blue-500 mx-auto" />
                                    <p className="text-xs font-bold text-slate-700 font-outfit">All Vehicle Systems Healthy</p>
                                    <p className="text-[10px] font-semibold max-w-[200px] mx-auto">Sensors verify braking, cornering forces, and engine heat are optimal.</p>
                                  </div>
                                )}
                              </div>
                            </div>

                            {/* BACK FACE */}
                            <div
                              className="absolute inset-0 w-full h-full backface-hidden rotate-y-180 bg-white rounded-3xl border border-slate-200/80 p-6 shadow-premium hover:shadow-premium-lg transition-all flex flex-col justify-between z-0"
                              style={{ backfaceVisibility: 'hidden', WebkitBackfaceVisibility: 'hidden', transform: 'rotateY(180deg)' }}
                            >
                              <div className="flex-1 flex flex-col min-h-0">
                                <div className="flex items-center justify-between border-b border-slate-100 pb-3.5 mb-4 shrink-0">
                                  <h3 className="text-sm font-extrabold text-slate-800 font-outfit tracking-wide flex items-center gap-2 uppercase">
                                    <Activity className="w-4.5 h-4.5 text-brand-500" /> Wear Details &amp; RUL
                                  </h3>
                                  <button
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      setIsMaintCardFlipped(false);
                                    }}
                                    className="text-[9px] bg-slate-50 hover:bg-slate-100 border border-slate-200 text-slate-500 px-2 py-0.5 rounded-full font-bold transition-all cursor-pointer"
                                  >
                                    Back to Summary
                                  </button>
                                </div>

                                {/* Component items scrollable container */}
                                <div className="flex-1 overflow-y-auto space-y-3 pr-1">
                                  {maintHealthData && maintHealthData.components ? (
                                    maintHealthData.components
                                      .filter(c => c.component !== 'clutch')
                                      .map((c, ci) => {
                                        const isCrit = c.health_score < 10.0;
                                        const isWarn = c.health_score >= 10.0 && c.health_score < 30.0;
                                        const colorClass = isCrit ? 'text-rose-600 bg-rose-50 border-rose-100' : isWarn ? 'text-amber-600 bg-amber-50 border-amber-100' : 'text-blue-600 bg-blue-50 border-blue-100';
                                        const progressColor = isCrit ? 'from-rose-500 to-red-600' : isWarn ? 'from-amber-500 to-orange-500' : 'from-blue-500 to-indigo-500';

                                        const unitText = { brake: 'km', tire: 'km', engine: 'hrs', battery: 'cycles', clutch: 'km' }[c.component] || 'units';

                                        return (
                                          <div key={ci} className="bg-slate-50/70 border border-slate-200/40 p-3 rounded-2xl flex items-center gap-3 hover:bg-slate-50 transition-all">
                                            <div className="p-2 bg-white rounded-xl shadow-sm text-slate-500 shrink-0">
                                              {c.component === "brake" ? <Wrench className="w-4 h-4 text-brand-500" /> :
                                                c.component === "tire" ? <Compass className="w-4 h-4 text-brand-500" /> :
                                                  c.component === "battery" ? <Battery className="w-4 h-4 text-brand-500" /> :
                                                    <Thermometer className="w-4 h-4 text-brand-500" />}
                                            </div>
                                          <div className="flex-1 min-w-0">
                                            <div className="flex justify-between items-center mb-1">
                                              <span className="text-xs font-black text-slate-800 uppercase font-outfit">{c.component}</span>
                                              <span className={`text-[9.5px] font-bold font-outfit px-1.5 py-0.5 rounded border select-none shrink-0 text-center ${colorClass}`}>
                                                {c.health_score.toFixed(0)}% Health
                                              </span>
                                            </div>
                                            <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden relative shadow-inner mb-2">
                                              <div
                                                className={`h-full rounded-full bg-gradient-to-r ${progressColor} transition-all duration-1000`}
                                                style={{ width: `${Math.max(0, Math.min(100, c.health_score))}%` }}
                                              ></div>
                                            </div>
                                            <div className="flex justify-between text-[9px] text-slate-400 font-bold">
                                              <span>RUL: <strong className="text-slate-600 font-extrabold">{Math.round(c.rul).toLocaleString()} {unitText}</strong></span>
                                              <span>Wear: <strong className="text-slate-600 font-extrabold">{parseFloat(c.accumulated_wear).toFixed(0)} {unitText}</strong></span>
                                            </div>
                                          </div>
                                        </div>
                                      );
                                    })
                                  ) : (
                                    <div className="h-40 flex flex-col items-center justify-center gap-2">
                                      <RefreshCw className="w-5 h-5 text-brand-500 animate-spin" />
                                      <span className="text-[10px] text-slate-400 font-bold">Loading components wear...</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>

                          </div>
                        </div>

                      </div>


                    </div>
                  </div>
                )}
              </section>
  );
}
