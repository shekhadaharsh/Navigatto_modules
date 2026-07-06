import ReplayControl from './ReplayControl';
import DeviceSimulator from './DeviceSimulator';
import React, { useState, useEffect, useRef } from 'react';
import {
  Compass, Search, Truck, Calendar, Clock, Navigation, MapPin, Gauge,
  ShieldAlert, ShieldCheck, Droplet, Wrench, RefreshCw, AlertTriangle,
  AlertCircle, TrendingUp, TrendingDown, ArrowRight, ArrowLeft, User, Settings,
  Info, CheckCircle2, XCircle, ChevronRight, Activity, Battery, Thermometer, Menu
} from 'lucide-react';
import DriverSidebar from './components/DriverSidebar';
import TripSidebar from './components/TripSidebar';
import TripDiagnostics from './components/TripDiagnostics';
import MaintenanceDashboardModal from './modals/MaintenanceDashboardModal';
import SettingsModal from './modals/SettingsModal';
import FuelTheftModal from './modals/FuelTheftModal';
import { MOCK_DRIVERS, MOCK_VEHICLES, generateMockJourneys, getMockJourneyDetails, getDriverColor, cleanTripDetails } from './data/mockData';

export default function App() {
  // --- UI STATES ---
  const [drivers, setDrivers] = useState([]);
  const [activeDriverId, setActiveDriverId] = useState(null);
  const [journeys, setJourneys] = useState([]);
  const [activeJourneyId, setActiveJourneyId] = useState(null);
  const [journeyDetails, setJourneyDetails] = useState(null);
  const [mobileViewTab, setMobileViewTab] = useState('drivers');
  const [isScoreCardFlipped, setIsScoreCardFlipped] = useState(false);
  const [isMaintCardFlipped, setIsMaintCardFlipped] = useState(false);
  const [isSimDialogOpen, setIsSimDialogOpen] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

  // --- LOADERS / CONTROL ---
  const [searchTerm, setSearchTerm] = useState('');
  const [tripSearchTerm, setTripSearchTerm] = useState('');
  const [isLoadingDrivers, setIsLoadingDrivers] = useState(true);
  const [isLoadingJourneys, setIsLoadingJourneys] = useState(false);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [isRecomputing, setIsRecomputing] = useState(false);
  const [isUsingMock, setIsUsingMock] = useState(false);
  const [sqlError, setSqlError] = useState(false);

  // --- PREDICTIVE VEHICLE MAINTENANCE SYSTEM STATES ---
  const [isMaintDialogOpen, setIsMaintDialogOpen] = useState(false);
  const [maintVehicleId, setMaintVehicleId] = useState(null);
  const [maintHealthData, setMaintHealthData] = useState(null);
  const [maintFleetSummary, setMaintFleetSummary] = useState(null);
  const [isLoadingMaintHealth, setIsLoadingMaintHealth] = useState(false);
  const [maintHistoryData, setMaintHistoryData] = useState([]);
  const [isLoadingMaintHistory, setIsLoadingMaintHistory] = useState(false);
  const [activeMaintTab, setActiveMaintTab] = useState('vehicle');
  const [maintSearchTerm, setMaintSearchTerm] = useState('');
  const [maintFilterStatus, setMaintFilterStatus] = useState('all');
  const [fuelAlerts, setFuelAlerts] = useState([]);
  const [activeFuelAlert, setActiveFuelAlert] = useState(null);
  const [showAlertToast, setShowAlertToast] = useState(false);
  const dismissedToastIdsRef = useRef(new Set());
  const isReplayRunningRef = useRef(false);
  const globalMuteRef = useRef(false);

  // --- SYSTEM SETTINGS STATES ---
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);
  const [settingsEmail, setSettingsEmail] = useState('');
  const [isSavingSettings, setIsSavingSettings] = useState(false);
  const [settingsStatus, setSettingsStatus] = useState(null);

  useEffect(() => {
    if (isSettingsOpen) {
      setSettingsStatus(null);
      fetch('/api/maintenance/settings')
        .then(res => res.json())
        .then(data => {
          if (data.alert_recipient_email) {
            setSettingsEmail(data.alert_recipient_email);
          }
        })
        .catch(err => console.error("Error loading settings:", err));
    }
  }, [isSettingsOpen]);

  const handleSaveSettings = (e) => {
    e.preventDefault();
    setIsSavingSettings(true);
    setSettingsStatus(null);
    
    fetch('/api/maintenance/settings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ alert_recipient_email: settingsEmail }),
    })
      .then(res => {
        if (!res.ok) {
          return res.json().then(err => { throw new Error(err.detail || "Failed to update settings") });
        }
        return res.json();
      })
      .then(data => {
        setSettingsStatus({ type: 'success', message: 'Settings saved successfully!' });
        setTimeout(() => setIsSettingsOpen(false), 1500);
      })
      .catch(err => {
        setSettingsStatus({ type: 'error', message: err.message || 'Error saving settings.' });
      })
      .finally(() => {
        setIsSavingSettings(false);
      });
  };

  useEffect(() => {
    const handleReplayStart = () => {
      isReplayRunningRef.current = true;
    };
    const handleReplayStop = () => {
      isReplayRunningRef.current = false;
      dismissedToastIdsRef.current.clear();
      globalMuteRef.current = false;
      setShowAlertToast(false);
      setFuelAlerts([]);
    };
    window.addEventListener("replay-started", handleReplayStart);
    window.addEventListener("replay-stopped", handleReplayStop);
    return () => {
      window.removeEventListener("replay-started", handleReplayStart);
      window.removeEventListener("replay-stopped", handleReplayStop);
    };
  }, []);

  // --- 1. LOAD DRIVERS (STRICT SQL SERVER MODE - NO MOCK DATA) ---
  const fetchDrivers = async () => {
    setIsLoadingDrivers(true);
    setSqlError(false);
    try {
      const res = await fetch('/api/drivers/');
      if (!res.ok) throw new Error(`SQL Server offline or returned status ${res.status}`);
      const data = await res.json();

      const enriched = data.map(d => {
        const fallbackName = {
          "DR001": "Alexander Sterling",
          "DR002": "Marcus Vance",
          "DR003": "Elena Rostova",
          "DR004": "Devon Lane",
          "DR005": "Ronald Richards",
          "DR006": "Bessie Cooper",
          "DR007": "Albert Flores",
          "DR008": "Courtney Henry",
          "DR009": "Kathryn Murphy",
          "DR010": "Dianne Russell"
        }[d.driver_id] || `Driver ${d.driver_id.replace('DR', '')}`;

        const fallbackVehicleType = {
          "DR001": "Mini Truck",
          "DR002": "Mini Truck",
          "DR003": "Medium Cargo",
          "DR004": "Heavy Cargo Truck",
          "DR005": "Heavy Cargo Truck",
          "DR006": "Pickup Truck",
          "DR007": "Heavy Cargo Truck",
          "DR008": "Mini Truck",
          "DR009": "Mini Truck",
          "DR010": "Mini Truck"
        }[d.driver_id] || "Mini Truck";

        const fallbackVehicleId = `VH0${d.driver_id.replace('DR', '')}`;

        return {
          ...d,
          name: d.driver_name || fallbackName,
          avatar_color: getDriverColor(d.driver_id),
          vehicle_type: d.vehicle_type || fallbackVehicleType,
          vehicle_id: d.vehicle_id || fallbackVehicleId,
          total_distance_km: d.total_distance_km ?? d.total_distance ?? 0.0
        };
      });

      if (enriched.length === 0) {
        console.error("[SQL Server Notice]: Connected to database, but 0 drivers found in SQL DB.");
        setDrivers([]);
      } else {
        setDrivers(enriched);
        if (enriched.length > 0) {
          setActiveDriverId(enriched[0].driver_id);
        }
      }
    } catch (err) {
      console.error("[Backend Terminal Error]: Could not connect to SQL Server database. No mock data loaded.", err);
      setSqlError(true);
      setDrivers([]);
    } finally {
      setIsLoadingDrivers(false);
    }
  };

  useEffect(() => {
    fetchDrivers();
  }, []);

  // --- 2. LOAD JOURNEYS (triggers when activeDriverId changes) ---
  useEffect(() => {
    if (!activeDriverId) return;

    const fetchJourneys = async () => {
      setIsLoadingJourneys(true);
      setJourneyDetails(null);
      setJourneys([]);
      setActiveJourneyId(null);

      try {
        const res = await fetch(`/api/drivers/${activeDriverId}/trips`);

        if (res.status === 404) {
          setJourneys([]);
          setActiveJourneyId(null);
          return;
        }

        if (!res.ok) throw new Error(`SQL Server API error: ${res.status}`);

        const list = await res.json();
        const normalized = list.map(t => ({
          journey_id: t.trip_id,
          route_type: t.route_type,
          start_time: t.trip_start || '',
          distance_km: parseFloat(Number(t.distance_km).toFixed(2)),
          duration_min: parseFloat(Number(t.trip_duration_min).toFixed(1)),
          driver_score: parseFloat(Number(t.final_score).toFixed(1)),
          fuel_theft_detected: t.fuel_theft_detected || false,
          maintenance_critical: false,
        }));
        setJourneys(normalized);
        setActiveJourneyId(normalized.length > 0 ? normalized[0].journey_id : null);
      } catch (err) {
        console.error("[Backend Terminal Error]: Error loading journeys from SQL DB", err);
        setJourneys([]);
        setActiveJourneyId(null);
      } finally {
        setIsLoadingJourneys(false);
      }
    };
    fetchJourneys();
  }, [activeDriverId]);

  // --- 3. LOAD JOURNEY DETAILS (triggers when activeJourneyId changes) ---
  useEffect(() => {
    if (!activeJourneyId) return;

    setIsScoreCardFlipped(false);
    setIsMaintCardFlipped(false);

    const fetchDetails = async () => {
      setIsLoadingDetails(true);
      try {
        const res = await fetch(`/api/drivers/${activeDriverId}/trips/${activeJourneyId}/details`);
        if (!res.ok) throw new Error('Network error');
        const rawData = await res.json();
        const data = cleanTripDetails(rawData);

        if (!data.speed_profile) {
          const avgSpd = data.journey.avg_speed_kmh || 60;
          data.speed_profile = Array.from({ length: 12 }, (_, k) => ({
            time: `${k * 10}m`,
            speed: data.journey.route_type === 'Highway'
              ? Math.round(avgSpd + Math.sin(k) * 12 + (k === 5 ? 18 : 0))
              : Math.round(avgSpd * 0.7 + Math.sin(k * 2) * 15)
          }));
        }

        setJourneyDetails(data);
      } catch (err) {
        console.error("[Backend Terminal Error]: Error loading journey details from SQL DB", err);
      } finally {
        setIsLoadingDetails(false);
      }
    };
    fetchDetails();
  }, [activeJourneyId, activeDriverId, journeys]);


  // --- GLOBAL REAL-TIME FUEL THEFT SSE STREAM ---
  useEffect(() => {
    const es = new EventSource('/api/fuel/stream');

    es.onmessage = (e) => {
      try {
        const payload = JSON.parse(e.data);
        if (payload.error) return;

        setFuelAlerts(prev => {
          const alreadyExists = prev.some(a => a.alert_id === payload.alert_id);
          if (alreadyExists) return prev;

          const existingIdx = prev.findIndex(a => a.driver_id === payload.driver_id && a.trip_id === payload.trip_id);
          if (existingIdx !== -1) {
            const updatedAlerts = [...prev];
            const existingAlert = updatedAlerts[existingIdx];
            
            const accumulatedAmount = (existingAlert.theft_amount_liters || 0) + (payload.theft_amount_liters || 0);
            
            const mergedAlert = {
              ...payload,
              theft_amount_liters: accumulatedAmount,
              accumulated_count: (existingAlert.accumulated_count || 1) + 1,
              original_amount: payload.theft_amount_liters
            };
            
            updatedAlerts.splice(existingIdx, 1);
            if (isReplayRunningRef.current && !globalMuteRef.current && !dismissedToastIdsRef.current.has(`${mergedAlert.driver_id}-${mergedAlert.trip_id}`)) {
              setShowAlertToast(true);
            }
            return [mergedAlert, ...updatedAlerts].slice(0, 20);
          }

          if (isReplayRunningRef.current && !globalMuteRef.current && !dismissedToastIdsRef.current.has(`${payload.driver_id}-${payload.trip_id}`)) {
            setShowAlertToast(true);
          }
          return [payload, ...prev].slice(0, 20);
        });
      } catch (_) { }
    };

    es.onerror = () => { };

    return () => es.close();
  }, []);

  // --- BACKGROUND FETCH VEHICLE COMPONENT WEAR DATA FOR CARD FLIP ---
  useEffect(() => {
    if (!journeyDetails) return;
    const vid = journeyDetails.journey.vehicle_id || "VH001";

    const fetchMaintHealth = async () => {
      try {
        const resH = await fetch(`/api/maintenance/health/${vid}`);
        if (resH.ok) {
          const dataH = await resH.json();
          setMaintHealthData(dataH);
        }
      } catch (err) {
        console.error("[Backend Terminal Error]: Error pre-loading maintenance health from SQL DB:", err);
      }
    };

    fetchMaintHealth();
  }, [journeyDetails]);

  // --- 4. RECOMPUTE SAFETY MODELS ---
  const handleRecompute = async () => {
    if (!activeJourneyId) return;
    setIsRecomputing(true);

    try {
      const res = await fetch(`/api/drivers/${activeDriverId}/trips/${activeJourneyId}/details`);
      if (!res.ok) throw new Error('Recompute failed');
      const rawData = await res.json();
      const data = cleanTripDetails(rawData);

      if (!data.speed_profile) {
        const avgSpd = data.journey.avg_speed_kmh || 60;
        data.speed_profile = Array.from({ length: 12 }, (_, k) => ({
          time: `${k * 10}m`,
          speed: data.journey.route_type === 'Highway'
            ? Math.round(avgSpd + Math.sin(k) * 12 + (k === 5 ? 18 : 0))
            : Math.round(avgSpd * 0.7 + Math.sin(k * 2) * 15)
        }));
      }

      setJourneyDetails(data);
    } catch (err) {
      console.error("[Backend Terminal Error]: Recompute API failed against SQL DB", err);
    } finally {
      setIsRecomputing(false);
    }
  };

  // --- PREDICTIVE VEHICLE MAINTENANCE SYSTEM ACTIONS ---
  const openMaintenanceDashboard = async (vehicleId) => {
    const vid = vehicleId || (journeyDetails && journeyDetails.journey.vehicle_id) || "VH001";
    setMaintVehicleId(vid);
    setIsMaintDialogOpen(true);
    setIsLoadingMaintHealth(true);
    setActiveMaintTab(vehicleId ? 'vehicle' : 'fleet');

    if (isUsingMock) {
      setTimeout(() => {
        const activeDriver = drivers.find(d => d.driver_id === activeDriverId);
        setMaintHealthData({
          vehicle_id: vid,
          reg_no: activeDriver ? activeDriver.vehicle_id || "VH001" : "VH001",
          make: activeDriver ? (activeDriver.vehicle_type === "Mini Truck" ? "Tata" : "BharatBenz") : "Tata",
          model: activeDriver ? (activeDriver.vehicle_type === "Mini Truck" ? "Signa 4825.T" : "1914R") : "Signa 4825.T",
          components: [
            { component: "brake", accumulated_wear: 14500.2, base_life: 20000.0, rul: 5499.8, health_score: 27.5, status: "warning", last_updated: "2026-05-21 12:45" },
            { component: "tire", accumulated_wear: 48900.0, base_life: 120000.0, rul: 71100.0, health_score: 59.3, status: "ok", last_updated: "2026-05-21 12:45" },
            { component: "battery", accumulated_wear: 350.0, base_life: 5000.0, rul: 4650.0, health_score: 93.0, status: "ok", last_updated: "2026-05-21 12:45" },
            { component: "engine", accumulated_wear: 45750.0, base_life: 50000.0, rul: 4250.0, health_score: 8.5, status: "critical", last_updated: "2026-05-21 12:45" }
          ]
        });
        setMaintFleetSummary({
          open_alerts: 5,
          fleet: [
            { vehicle_id: "VH001", reg_no: "GJ-01-AA-1234", make: "Tata", model: "Signa", critical_count: 1, warning_count: 1, min_health: 8.5, overall_status: "critical" },
            { vehicle_id: "VH002", reg_no: "MH-02-BB-5678", make: "Ashok Leyland", model: "Dost", critical_count: 1, warning_count: 1, min_health: 8.0, overall_status: "critical" },
            { vehicle_id: "VH003", reg_no: "KA-03-CC-9012", make: "BharatBenz", model: "1914R", critical_count: 0, warning_count: 1, min_health: 25.0, overall_status: "warning" },
            { vehicle_id: "VH004", reg_no: "DL-04-DD-3456", make: "Tata", model: "LPT", critical_count: 0, warning_count: 0, min_health: 85.0, overall_status: "ok" }
          ]
        });
        
        // Mock wear history
        const mockHistory = [];
        const today = new Date();
        for (let i = 9; i >= 0; i--) {
          const d = new Date();
          d.setDate(today.getDate() - i);
          const dateStr = d.toISOString().split('T')[0];
          mockHistory.push({
            date: dateStr,
            brakes: parseFloat((5.0 + Math.sin(i) * 2.0).toFixed(2)),
            tires: parseFloat((3.0 + Math.cos(i) * 1.5).toFixed(2)),
            engine: parseFloat((8.0 + Math.sin(i * 1.5) * 3.0).toFixed(2)),
          });
        }
        setMaintHistoryData(mockHistory);
        setIsLoadingMaintHealth(false);
      }, 400);
    } else {
      try {
        setIsLoadingMaintHistory(true);
        const resDash = await fetch(`/api/maintenance/dashboard/${vid}`).catch(() => null);
        if (resDash && resDash.ok) {
          const dashData = await resDash.json();
          if (dashData.health) setMaintHealthData(dashData.health);
          if (dashData.fleet) setMaintFleetSummary(dashData.fleet);
          if (dashData.history) {
            setMaintHistoryData(dashData.history.history || dashData.history || []);
          }
        }
      } catch (e) {
        console.error("Error loading maintenance views:", e);
      } finally {
        setIsLoadingMaintHealth(false);
        setIsLoadingMaintHistory(false);
      }
    }
  };

  const handleAckAlert = async (alertId) => {
    if (isUsingMock) {
      // Find the component being resolved from the current mock state
      const resolvedAlert = journeyDetails?.maintenance?.alerts?.find(a => a.id === alertId);
      let targetComponent = "";
      if (resolvedAlert) {
        const issueLower = (resolvedAlert.issue || "").toLowerCase();
        const detailLower = (resolvedAlert.detail || "").toLowerCase();
        if (issueLower.includes("engine") || detailLower.includes("engine")) targetComponent = "engine";
        else if (issueLower.includes("brake") || detailLower.includes("brake")) targetComponent = "brake";
        else if (issueLower.includes("tire") || detailLower.includes("tire")) targetComponent = "tire";
        else if (issueLower.includes("battery") || detailLower.includes("battery")) targetComponent = "battery";
      }

      setJourneyDetails(prev => {
        if (!prev) return prev;
        let updatedHealthScores = { ...(prev.maintenance.health_scores || { brake: 100, tire: 100, battery: 100, engine: 100 }) };
        if (targetComponent) {
          updatedHealthScores[targetComponent] = 100;
        }
        return {
          ...prev,
          maintenance: {
            ...prev.maintenance,
            alerts: prev.maintenance.alerts.filter(a => a.id !== alertId),
            alert_count: Math.max(0, prev.maintenance.alert_count - 1),
            priority: prev.maintenance.alerts.filter(a => a.id !== alertId).length > 0 ? "Warning" : "OK",
            health_scores: updatedHealthScores
          }
        };
      });

      if (targetComponent) {
        setMaintHealthData(prev => {
          if (!prev || !prev.components) return prev;
          return {
            ...prev,
            components: prev.components.map(c => {
              if (c.component === targetComponent) {
                return { ...c, health_score: 100.0, rul: c.base_life || 50000.0, accumulated_wear: 0.0 };
              }
              return c;
            })
          };
        });
      }
      // Acknowledged mock alert state successfully updated
    } else {
      try {
        const res = await fetch(`/api/maintenance/alerts/${alertId}/ack`, { method: 'POST' });
        if (res.ok) {
          const detailsRes = await fetch(`/api/drivers/${activeDriverId}/trips/${activeJourneyId}/details`);
          if (detailsRes.ok) {
            const rawData = await detailsRes.json();
            setJourneyDetails(cleanTripDetails(rawData));
          }
          if (maintVehicleId) {
            openMaintenanceDashboard(maintVehicleId);
          }
        }
      } catch (err) {
        console.error("Failed to acknowledge alert", err);
      }
    }
  };

  const handleResolveComponent = async (componentName, vehicleId) => {
    if (isUsingMock) {
      setMaintHealthData(prev => {
        if (!prev || !prev.components) return prev;
        return {
          ...prev,
          components: prev.components.map(c => {
            if (c.component === componentName) {
              return { ...c, health_score: 100.0, rul: c.base_life || 50000.0, accumulated_wear: 0.0, status: "ok" };
            }
            return c;
          })
        };
      });
      setJourneyDetails(prev => {
        if (!prev) return prev;
        let updatedHealthScores = { ...(prev.maintenance.health_scores || { brake: 100, tire: 100, battery: 100, engine: 100 }) };
        updatedHealthScores[componentName] = 100;
        return {
          ...prev,
          maintenance: {
            ...prev.maintenance,
            health_scores: updatedHealthScores
          }
        };
      });
    } else {
      try {
        const res = await fetch(`/api/maintenance/components/${vehicleId}/${componentName}/resolve`, { method: 'POST' });
        if (res.ok) {
          if (maintVehicleId) {
            openMaintenanceDashboard(maintVehicleId);
          }
        }
      } catch (err) {
        console.error("Failed to resolve component", err);
      }
    }
  };

  // --- 5. SEARCH & FILTER ---
  const filteredDrivers = drivers.filter(d =>
    (d.name || '').toLowerCase().includes(searchTerm.toLowerCase()) ||
    (d.driver_id || '').toLowerCase().includes(searchTerm.toLowerCase())
  );

  const activeDriver = drivers.find(d => d.driver_id === activeDriverId) || MOCK_DRIVERS[0];

  const filteredJourneys = journeys.filter(j =>
    (j.journey_id || '').toLowerCase().includes(tripSearchTerm.toLowerCase()) ||
    (j.route_type || '').toLowerCase().includes(tripSearchTerm.toLowerCase())
  );

  // Helper colors for Score pill badges
  const getScoreColorClass = (score) => {
    if (score >= 80) return 'bg-blue-50 text-blue-700 border border-blue-200';
    if (score >= 60) return 'bg-amber-50 text-amber-700 border border-amber-200';
    return 'bg-rose-50 text-rose-700 border border-rose-200';
  };

  // Aggregate values
  const totalFleetTrips = drivers.reduce((acc, curr) => acc + curr.total_trips, 0);
  const totalFleetDist = drivers.reduce((acc, curr) => acc + curr.total_distance_km, 0);

  const renderToastBanner = (isFloating) => {
    if (!showAlertToast || fuelAlerts.length === 0) return null;
    return (
      <div className={isFloating ? "fixed top-24 right-8 z-[70] w-96 animate-slide-up shadow-2xl" : "w-full max-w-md animate-slide-down shadow-2xl z-[70]"}>
        <button
          onClick={() => {
            setActiveFuelAlert(fuelAlerts[0]);
            setShowAlertToast(false);
          }}
          className="w-full flex items-start gap-3 bg-rose-600 hover:bg-rose-700 active:scale-95 text-white p-4 rounded-2xl shadow-alert-glow border border-rose-500 transition-all cursor-pointer outline-none text-left"
        >
          <div className="w-9 h-9 bg-white/20 rounded-xl flex items-center justify-center shrink-0 mt-0.5">
            <ShieldAlert className="w-5 h-5 text-white animate-pulse" />
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-[10px] font-black uppercase tracking-widest text-rose-200 mb-0.5">
              🚨 Live Fuel Theft Alert
            </p>
            <p className="text-sm font-extrabold text-white font-outfit leading-snug">
              {fuelAlerts[0].theft_type === 'IGNITION_OFF_DROP'
                ? `Ignition OFF theft — ${fuelAlerts[0].theft_amount_liters?.toFixed(2)}L stolen`
                : fuelAlerts[0].theft_type === 'RUNNING_THEFT'
                  ? `Running theft — ${fuelAlerts[0].theft_amount_liters?.toFixed(2)}L siphoned while moving`
                  : `Refuel mismatch — ${fuelAlerts[0].theft_amount_liters?.toFixed(2)}L discrepancy`
              }
            </p>
            <p className="text-[10px] text-rose-200 font-semibold mt-0.5 flex items-center gap-1.5">
              <span>Driver: {fuelAlerts[0].driver_id} · Vehicle: {fuelAlerts[0].vehicle_id}</span>
              {fuelAlerts[0].accumulated_count > 1 && (
                <span className="bg-rose-500 text-white px-1.5 py-0.5 rounded text-[8px] font-black uppercase tracking-wider shadow-sm">
                  {fuelAlerts[0].accumulated_count}x Events
                </span>
              )}
            </p>
            <p className="text-[9px] text-rose-300 font-bold mt-1 flex items-center gap-1">
              <ChevronRight className="w-3 h-3" /> Click to view full details
            </p>
          </div>
          <button
            onClick={(e) => {
              e.stopPropagation();
              setShowAlertToast(false);
              if (!isReplayRunningRef.current) {
                globalMuteRef.current = true;
                if (fuelAlerts[0]) {
                  dismissedToastIdsRef.current.add(`${fuelAlerts[0].driver_id}-${fuelAlerts[0].trip_id}`);
                }
              }
            }}
            className="text-white/60 hover:text-white transition-colors p-0.5 rounded-lg hover:bg-white/10 border-0 outline-none cursor-pointer shrink-0"
          >
            <XCircle className="w-4 h-4" />
          </button>
        </button>
        {fuelAlerts.length > 1 && (
          <div className="mt-1 text-center text-[9px] text-rose-500 font-bold bg-rose-50 border border-rose-100 rounded-xl py-1.5">
            +{fuelAlerts.length - 1} more alert{fuelAlerts.length > 2 ? 's' : ''} pending
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col font-sans bg-[#f8fafc] text-slate-700 select-text">

      {/* -------------------- HEADER NAVBAR -------------------- */}
      <header className="h-16 flex items-center justify-between px-6 bg-white border-b border-slate-200/80 shrink-0 shadow-sm z-10">
        <div className="flex items-center gap-8">
            {/* Logo Container */}
            <div className="flex items-center gap-2 select-none">
              <h1 className="text-2xl font-black font-outfit tracking-tighter text-[#1d4ed8]">
                NAVIGATTO
              </h1>
              <span className="text-[#1d4ed8] font-bold text-[10px] px-2.5 py-0.5 rounded-full bg-blue-50 border border-blue-200 tracking-wide uppercase shadow-sm">
                Live GPS
              </span>
            </div>

          {/* Global Stats Pill Bar - hidden on mobile/tablet */}
          <div className="hidden lg:flex items-center gap-6 text-xs font-semibold border-l border-slate-200 pl-6">
            <button
              onClick={() => fetchDrivers()}
              className={`flex items-center gap-2 px-3.5 py-1.5 border rounded-full shadow-sm transition-all duration-300 cursor-pointer ${
                sqlError
                  ? 'bg-rose-50 border-rose-200 text-rose-700 hover:bg-rose-100/70'
                  : 'bg-blue-50/70 border-blue-200 text-[#1d4ed8] hover:bg-blue-100/70'
              }`}
              title="Click to re-verify live SQL Server database connection"
            >
              <span className={`w-2.5 h-2.5 rounded-full ${sqlError ? 'bg-rose-500 animate-pulse' : 'bg-[#1d4ed8] pulse-glow-green'}`}></span>
              <span className="text-slate-400 font-medium">Status:</span>
              <span className="font-bold uppercase tracking-wider">
                {sqlError ? "SQL Server Disconnected (Retry)" : "Connected (SQL Server)"}
              </span>
              <RefreshCw className={`w-3 h-3 ml-1 opacity-75 ${isLoadingDrivers ? 'animate-spin' : ''}`} />
            </button>
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">Total Trips:</span>
              <span className="text-slate-800 font-bold font-outfit text-sm">{(totalFleetTrips || 13548).toLocaleString()}</span>
            </div>
            <div className="w-1.5 h-1.5 rounded-full bg-slate-300"></div>
            <div className="flex items-center gap-2">
              <span className="text-slate-400 font-medium">Distance Travelled:</span>
              <span className="text-slate-800 font-bold font-outfit text-sm">{(totalFleetDist ? Math.round(totalFleetDist) : 5576000).toLocaleString()} km</span>
            </div>
          </div>
        </div>

        {/* Action controls for Desktop screens */}
        <div className="hidden md:flex items-center gap-3">
          {/* Vehicles Status Button */}
          <button
            onClick={() => {
              setIsMaintDialogOpen(true);
              setActiveMaintTab('fleet');
              openMaintenanceDashboard(null);
            }}
            className="flex items-center gap-2 px-4 py-2 bg-[#1d4ed8] hover:bg-[#1e40af] active:scale-95 text-white text-xs font-bold font-outfit rounded-full transition-all cursor-pointer shadow-md shadow-blue-600/20 border-0 outline-none hover:shadow-lg hover:scale-[1.02]"
            title="Open Vehicles Status Dashboard"
          >
            <Truck className="w-3.5 h-3.5" />
            <span>Vehicles Status</span>
          </button>
          
          {/* Device Simulator Button */}
          <button
            onClick={() => {
              setIsSimDialogOpen(true);
            }}
            className="flex items-center gap-2 px-4 py-2 bg-white hover:bg-slate-50 active:scale-95 text-slate-700 hover:text-[#1d4ed8] text-xs font-bold font-outfit rounded-full transition-all cursor-pointer border border-slate-200 shadow-sm outline-none hover:border-slate-300 hover:scale-[1.02]"
            title="Open IoT Device Simulator Panel"
          >
            <Activity className="w-3.5 h-3.5 text-[#1d4ed8] animate-pulse" />
            <span>Device & Data Simulator</span>
          </button>

          <ReplayControl />
          
          {/* Settings Button */}
          <button
            onClick={() => setIsSettingsOpen(true)}
            className="w-9 h-9 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-500 hover:text-[#1d4ed8] hover:scale-[1.05] transition-all cursor-pointer hover:border-slate-300 outline-none active:scale-95 shadow-sm"
            title="System Settings"
          >
            <Settings className="w-4 h-4" />
          </button>

          <div className="w-9 h-9 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center text-[#1d4ed8] font-bold text-xs shadow-sm cursor-pointer">
            <User className="w-4 h-4" />
          </div>
        </div>

        {/* Hamburger Menu Toggle for Mobile screens */}
        <button
          onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
          className="md:hidden p-2 hover:bg-slate-100 rounded-xl text-slate-600 active:scale-95 transition-all outline-none border-0 bg-transparent cursor-pointer"
          aria-label="Toggle Navigation Menu"
        >
          <Menu className="w-6 h-6" />
        </button>
      </header>

      {/* Mobile Drawer Navigation Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden bg-white border-b border-slate-200/80 p-5 flex flex-col gap-4 animate-slide-down shadow-lg z-20">
          <div className="flex flex-col gap-3 pb-4 border-b border-slate-100">
            <button
              onClick={() => {
                fetchDrivers();
                setIsMobileMenuOpen(false);
              }}
              className={`w-full flex items-center justify-between p-3 border rounded-xl shadow-sm transition-all duration-300 cursor-pointer ${
                sqlError
                  ? 'bg-rose-50 border-rose-200 text-rose-700'
                  : 'bg-blue-50/70 border-blue-200 text-[#1d4ed8]'
              }`}
            >
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${sqlError ? 'bg-rose-500 animate-pulse' : 'bg-[#1d4ed8] pulse-glow-green'}`}></span>
                <span className="text-slate-500 text-xs font-semibold">Status:</span>
                <span className="text-xs font-bold uppercase tracking-wider">
                  {sqlError ? "Disconnected" : "Connected (SQL)"}
                </span>
              </div>
              <RefreshCw className={`w-4 h-4 opacity-75 ${isLoadingDrivers ? 'animate-spin' : ''}`} />
            </button>

            <div className="flex justify-between items-center px-2 py-1 text-xs">
              <span className="text-slate-400 font-semibold">Total Trips:</span>
              <span className="text-slate-800 font-bold font-outfit text-sm">{(totalFleetTrips || 13548).toLocaleString()}</span>
            </div>
            <div className="flex justify-between items-center px-2 py-1 text-xs">
              <span className="text-slate-400 font-semibold">Distance Travelled:</span>
              <span className="text-slate-800 font-bold font-outfit text-sm">{(totalFleetDist ? Math.round(totalFleetDist) : 5576000).toLocaleString()} km</span>
            </div>
          </div>

          <div className="flex flex-col gap-3">
            <button
              onClick={() => {
                setIsMaintDialogOpen(true);
                setActiveMaintTab('fleet');
                openMaintenanceDashboard(null);
                setIsMobileMenuOpen(false);
              }}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-[#1d4ed8] text-white text-xs font-bold font-outfit rounded-xl shadow-md cursor-pointer border-0 outline-none"
            >
              <Truck className="w-4 h-4" />
              <span>Vehicles Status</span>
            </button>

            <button
              onClick={() => {
                setIsSimDialogOpen(true);
                setIsMobileMenuOpen(false);
              }}
              className="w-full flex items-center justify-center gap-2 py-2.5 bg-white text-slate-700 border border-slate-200 text-xs font-bold font-outfit rounded-xl cursor-pointer"
            >
              <Activity className="w-4 h-4 text-[#1d4ed8]" />
              <span>Device & Data Simulator</span>
            </button>

            <div className="flex justify-between items-center gap-2 pt-2 border-t border-slate-100">
              <span className="text-slate-500 text-xs font-semibold">Simulation Control:</span>
              <ReplayControl />
            </div>

            <div className="flex items-center justify-between gap-3 pt-2">
              <button
                onClick={() => {
                  setIsSettingsOpen(true);
                  setIsMobileMenuOpen(false);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-slate-100 border border-slate-200 text-slate-600 rounded-xl text-xs font-bold font-outfit cursor-pointer flex-1 justify-center border-0"
              >
                <Settings className="w-4 h-4" />
                <span>Settings</span>
              </button>
              <div className="w-9 h-9 rounded-full bg-blue-50 border border-blue-200 flex items-center justify-center text-[#1d4ed8] font-bold text-xs shadow-sm">
                <User className="w-4 h-4" />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Global Fuel Theft Toast Banner ── */}
      {!activeFuelAlert && renderToastBanner(true)}

      {/* -------------------- MAIN WORKSPACE -------------------- */}
      <div className="flex-1 flex overflow-hidden">

        {/* -------------------- LEFT SIDEBAR (DRIVERS LIST) -------------------- */}
        <DriverSidebar
          mobileViewTab={mobileViewTab}
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          isLoadingDrivers={isLoadingDrivers}
          filteredDrivers={filteredDrivers}
          activeDriverId={activeDriverId}
          setActiveDriverId={setActiveDriverId}
          setMobileViewTab={setMobileViewTab}
          isSidebarCollapsed={isSidebarCollapsed}
          setIsSidebarCollapsed={setIsSidebarCollapsed}
        />

        {/* -------------------- DYNAMIC MAIN INTERFACE -------------------- */}
        <main className="flex-1 flex overflow-hidden">
          {!activeDriverId ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center bg-slate-50/50 relative overflow-hidden">
              <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[500px] h-[500px] bg-brand-500/5 rounded-full blur-[120px] pointer-events-none"></div>

              <div className="bg-white p-6 rounded-[32px] shadow-premium border border-slate-100/50 mb-6 text-brand-500 relative shrink-0">
                <Truck className="w-16 h-16 animate-pulse" />
                <div className="absolute -bottom-1 -right-1 w-6 h-6 bg-brand-500 text-white rounded-full flex items-center justify-center border-4 border-white">
                  <span className="w-2 h-2 rounded-full bg-white animate-ping"></span>
                </div>
              </div>

              <h3 className="text-2xl font-black font-outfit text-slate-900 mb-2.5 tracking-tight">
                Select a Fleet Driver
              </h3>
              <p className="text-sm text-slate-400 max-w-md leading-relaxed font-medium">
                Choose a driver from the active directory in the left panel to begin monitoring vehicle journey diagnostics, fuel theft alerts, consumption models, and real-time maintenance signals.
              </p>
            </div>
          ) : (
            <>
              <TripSidebar
                mobileViewTab={mobileViewTab}
                setMobileViewTab={setMobileViewTab}
                activeDriver={activeDriver}
                filteredJourneys={filteredJourneys}
                journeys={journeys}
                tripSearchTerm={tripSearchTerm}
                setTripSearchTerm={setTripSearchTerm}
                isLoadingJourneys={isLoadingJourneys}
                activeJourneyId={activeJourneyId}
                setActiveJourneyId={setActiveJourneyId}
                isSidebarCollapsed={isSidebarCollapsed}
                setIsSidebarCollapsed={setIsSidebarCollapsed}
              />
              <TripDiagnostics
                mobileViewTab={mobileViewTab}
                setMobileViewTab={setMobileViewTab}
                isLoadingDetails={isLoadingDetails}
                journeyDetails={journeyDetails}
                isScoreCardFlipped={isScoreCardFlipped}
                setIsScoreCardFlipped={setIsScoreCardFlipped}
                isMaintCardFlipped={isMaintCardFlipped}
                setIsMaintCardFlipped={setIsMaintCardFlipped}
                activeFuelAlert={activeFuelAlert}
                setActiveFuelAlert={setActiveFuelAlert}
                openMaintenanceDashboard={openMaintenanceDashboard}
                maintHealthData={maintHealthData}
                isSidebarCollapsed={isSidebarCollapsed}
                setIsSidebarCollapsed={setIsSidebarCollapsed}
              />
              <MaintenanceDashboardModal
                isOpen={isMaintDialogOpen}
                onClose={() => setIsMaintDialogOpen(false)}
                maintSearchTerm={maintSearchTerm}
                setMaintSearchTerm={setMaintSearchTerm}
                maintHealthData={maintHealthData}
                isLoadingMaintHealth={isLoadingMaintHealth}
                activeMaintTab={activeMaintTab}
                setActiveMaintTab={setActiveMaintTab}
                maintFleetSummary={maintFleetSummary}
                maintHistoryData={maintHistoryData}
                isLoadingMaintHistory={isLoadingMaintHistory}
                openMaintenanceDashboard={openMaintenanceDashboard}
              />
              <DeviceSimulator
                isOpen={isSimDialogOpen}
                onClose={() => setIsSimDialogOpen(false)}
                drivers={drivers}
                setDrivers={setDrivers}
                activeDriverId={activeDriverId}
                setActiveDriverId={setActiveDriverId}
                setJourneys={setJourneys}
                setActiveJourneyId={setActiveJourneyId}
                setFuelAlerts={setFuelAlerts}
                setShowAlertToast={setShowAlertToast}
                isUsingMock={isUsingMock}
              />
            </>
          )}

          <FuelTheftModal
            activeFuelAlert={activeFuelAlert}
            setActiveFuelAlert={setActiveFuelAlert}
            isReplayRunningRef={isReplayRunningRef}
            globalMuteRef={globalMuteRef}
            dismissedToastIdsRef={dismissedToastIdsRef}
            renderToastBanner={renderToastBanner}
          />
        </main>
      </div>

      <SettingsModal
        isOpen={isSettingsOpen}
        onClose={() => setIsSettingsOpen(false)}
        handleSaveSettings={handleSaveSettings}
        settingsEmail={settingsEmail}
        setSettingsEmail={setSettingsEmail}
        isSavingSettings={isSavingSettings}
      />
    </div>
  );
}
