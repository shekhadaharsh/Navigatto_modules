import React, { useState, useEffect } from 'react';
import { 
  Compass, Search, Truck, Calendar, Clock, Navigation, MapPin, Gauge, 
  ShieldAlert, ShieldCheck, Droplet, Wrench, RefreshCw, AlertTriangle, 
  AlertCircle, TrendingUp, TrendingDown, ArrowRight, ArrowLeft, User, Settings, 
  Info, CheckCircle2, XCircle, ChevronRight, Activity, Battery, Thermometer
} from 'lucide-react';
import {
  ResponsiveContainer, BarChart, Bar, Cell, LineChart, Line, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, AreaChart, Area
} from 'recharts';

// ==================== FRONTEND MOCK DATA FALLBACKS ====================
// Generates identical structure to Flask in case backend is offline
const MOCK_DRIVERS = [
  {"driver_id": "DR001", "name": "Alexander Sterling", "vehicle_type": "Mini Truck", "total_trips": 1405, "total_distance_km": 564300.0, "avg_speed_kmh": 67.4, "avatar_color": "#2563eb", "avg_score": 88.5, "vehicle_id": "VH001", "total_odometer_km": 125430.0, "engine_total_hours": 2450.5},
  {"driver_id": "DR002", "name": "Marcus Vance", "vehicle_type": "Mini Truck", "total_trips": 1367, "total_distance_km": 561200.0, "avg_speed_kmh": 68.1, "avatar_color": "#10b981", "avg_score": 82.4, "vehicle_id": "VH002", "total_odometer_km": 98750.0, "engine_total_hours": 1820.0},
  {"driver_id": "DR003", "name": "Elena Rostova", "vehicle_type": "Medium Cargo", "total_trips": 1289, "total_distance_km": 570900.0, "avg_speed_kmh": 65.2, "avatar_color": "#d97706", "avg_score": 79.1, "vehicle_id": "VH003", "total_odometer_km": 164200.0, "engine_total_hours": 3120.2},
  {"driver_id": "DR004", "name": "Devon Lane", "vehicle_type": "Heavy Cargo Truck", "total_trips": 1391, "total_distance_km": 581600.0, "avg_speed_kmh": 67.8, "avatar_color": "#ef4444", "avg_score": 58.4, "vehicle_id": "VH004", "total_odometer_km": 215300.0, "engine_total_hours": 4200.8},
  {"driver_id": "DR005", "name": "Ronald Richards", "vehicle_type": "Heavy Cargo Truck", "total_trips": 1353, "total_distance_km": 548900.0, "avg_speed_kmh": 67.6, "avatar_color": "#8b5cf6", "avg_score": 84.2, "vehicle_id": "VH005", "total_odometer_km": 189400.0, "engine_total_hours": 3760.4},
  {"driver_id": "DR006", "name": "Bessie Cooper", "vehicle_type": "Pickup Truck", "total_trips": 1328, "total_distance_km": 517500.0, "avg_speed_kmh": 67.2, "avatar_color": "#2563eb", "avg_score": 91.8, "vehicle_id": "VH006", "total_odometer_km": 72400.0, "engine_total_hours": 1120.0},
  {"driver_id": "DR007", "name": "Albert Flores", "vehicle_type": "Heavy Cargo Truck", "total_trips": 1392, "total_distance_km": 582300.0, "avg_speed_kmh": 68.0, "avatar_color": "#10b981", "avg_score": 74.3, "vehicle_id": "VH007", "total_odometer_km": 234100.0, "engine_total_hours": 4980.5},
  {"driver_id": "DR008", "name": "Courtney Henry", "vehicle_type": "Mini Truck", "total_trips": 1307, "total_distance_km": 552400.0, "avg_speed_kmh": 65.8, "avatar_color": "#d97706", "avg_score": 86.1, "vehicle_id": "VH008", "total_odometer_km": 114500.0, "engine_total_hours": 2180.2},
  {"driver_id": "DR009", "name": "Kathryn Murphy", "vehicle_type": "Mini Truck", "total_trips": 1204, "total_distance_km": 510700.0, "avg_speed_kmh": 67.4, "avatar_color": "#ef4444", "avg_score": 64.9, "vehicle_id": "VH009", "total_odometer_km": 89200.0, "engine_total_hours": 1650.0},
  {"driver_id": "DR010", "name": "Dianne Russell", "vehicle_type": "Mini Truck", "total_trips": 1412, "total_distance_km": 572900.0, "avg_speed_kmh": 66.1, "avatar_color": "#8b5cf6", "avg_score": 89.2, "vehicle_id": "VH010", "total_odometer_km": 142100.0, "engine_total_hours": 2980.1}
];

const MOCK_VEHICLES = {
  "DR001": {"vehicle_id": "VH001", "vehicle_type": "Mini Truck", "total_odometer_km": 125430.0, "engine_total_hours": 2450.5, "last_service_km": 118400.0},
  "DR002": {"vehicle_id": "VH002", "vehicle_type": "Mini Truck", "total_odometer_km": 98750.0, "engine_total_hours": 1820.0, "last_service_km": 92500.0},
  "DR003": {"vehicle_id": "VH003", "vehicle_type": "Medium Cargo", "total_odometer_km": 164200.0, "engine_total_hours": 3120.2, "last_service_km": 161000.0},
  "DR004": {"vehicle_id": "VH004", "vehicle_type": "Heavy Cargo Truck", "total_odometer_km": 215300.0, "engine_total_hours": 4200.8, "last_service_km": 204500.0},
  "DR005": {"vehicle_id": "VH005", "vehicle_type": "Heavy Cargo Truck", "total_odometer_km": 189400.0, "engine_total_hours": 3760.4, "last_service_km": 188000.0},
  "DR006": {"vehicle_id": "VH006", "vehicle_type": "Pickup Truck", "total_odometer_km": 72400.0, "engine_total_hours": 1120.0, "last_service_km": 70000.0},
  "DR007": {"vehicle_id": "VH007", "vehicle_type": "Heavy Cargo Truck", "total_odometer_km": 234100.0, "engine_total_hours": 4980.5, "last_service_km": 231000.0},
  "DR008": {"vehicle_id": "VH008", "vehicle_type": "Mini Truck", "total_odometer_km": 114500.0, "engine_total_hours": 2180.2, "last_service_km": 102000.0},
  "DR009": {"vehicle_id": "VH009", "vehicle_type": "Mini Truck", "total_odometer_km": 89200.0, "engine_total_hours": 1650.0, "last_service_km": 87000.0},
  "DR010": {"vehicle_id": "VH010", "vehicle_type": "Mini Truck", "total_odometer_km": 142100.0, "engine_total_hours": 2980.1, "last_service_km": 139000.0}
};

const generateMockJourneys = (driverId) => {
  const driver = MOCK_DRIVERS.find(d => d.driver_id === driverId) || MOCK_DRIVERS[0];
  const vehicle = MOCK_VEHICLES[driverId] || MOCK_VEHICLES["DR001"];
  const list = [];
  
  const routeTypes = ['Mixed', 'Highway', 'City', 'Rural', 'Mountain'];
  const baseScore = driver.avg_score;
  
  for(let i = 0; i < 12; i++) {
    const num = 9131 + i;
    const isTheft = (i === 4 && driverId === "DR001"); // Fuel theft on trip 4 for Sterling
    const isMaintenanceCritical = (i === 2 && driverId === "DR001"); // Battery issue on trip 2
    
    let dist = 145.2;
    let dur = 135;
    let route = routeTypes[i % 5];
    
    if (route === 'Highway') { dist = 320.5; dur = 240; }
    else if (route === 'City') { dist = 42.1; dur = 95; }
    
    list.push({
      journey_id: `TR00${num}`,
      start_time: new Date(Date.now() - i * 24 * 3600000 - 3 * 3600000).toLocaleString('en-US', {hour12: false}).replace(',', ''),
      route_type: route,
      distance_km: dist,
      duration_min: dur,
      driver_score: isTheft ? 52.0 : Math.round(baseScore + (i % 2 === 0 ? 3 : -3)),
      fuel_theft_detected: isTheft,
      maintenance_critical: isMaintenanceCritical
    });
  }
  return list;
};

const getMockJourneyDetails = (journeyId, driverId) => {
  const driver = MOCK_DRIVERS.find(d => d.driver_id === driverId) || MOCK_DRIVERS[0];
  const vehicle = MOCK_VEHICLES[driverId] || MOCK_VEHICLES["DR001"];
  const journeys = generateMockJourneys(driverId);
  const brief = journeys.find(j => j.journey_id === journeyId) || journeys[0];
  
  const isTheft = brief.fuel_theft_detected;
  const isMaintCritical = brief.maintenance_critical;
  
  // Custom speeds line chart profile
  const speedProfile = Array.from({length: 12}, (_, k) => ({
    time: `${k * 10}m`,
    speed: brief.route_type === 'Highway' 
      ? Math.round(75 + Math.sin(k) * 12 + (k === 5 ? 25 : 0))
      : brief.route_type === 'City'
        ? Math.round(25 + Math.sin(k * 2) * 18)
        : Math.round(55 + Math.sin(k) * 15)
  }));
  
  const accel = brief.driver_score < 70 ? 25 : (brief.driver_score < 85 ? 12 : 3);
  const brake = brief.driver_score < 70 ? 32 : (brief.driver_score < 85 ? 15 : 4);
  const overspeed = brief.driver_score < 70 ? 15 : (brief.driver_score < 85 ? 5 : 0);
  const cornering = brief.driver_score < 70 ? 18 : (brief.driver_score < 85 ? 8 : 2);
  const idle = brief.route_type === 'City' ? 42.5 : 12.8;
  
  const expectedFuel = brief.route_type === 'Highway' ? 38.5 : (brief.route_type === 'City' ? 10.2 : 22.4);
  const variance = isTheft ? 38.2 : (brief.driver_score < 70 ? 12.4 : 2.1);
  const actualFuel = parseFloat((expectedFuel * (1 + variance / 100)).toFixed(2));
  
  return {
    journey: {
      journey_id: brief.journey_id,
      driver_id: driverId,
      vehicle_id: vehicle.vehicle_id,
      start_time: brief.start_time,
      end_time: new Date(new Date(brief.start_time).getTime() + brief.duration_min * 60000).toLocaleString('en-US', {hour12: false}).replace(',', ''),
      route_type: brief.route_type,
      distance_km: brief.distance_km,
      duration_min: brief.duration_min,
      avg_speed_kmh: Math.round(brief.distance_km / (brief.duration_min / 60)),
      max_speed_kmh: brief.route_type === 'Highway' ? 112 : 78,
      load_pct: 68.4,
      idle_time_min: idle,
      stops: brief.route_type === 'City' ? 18 : 2,
      
      acceleration_events: accel,
      brake_events: brake,
      overspeed_count: overspeed,
      cornering_events: cornering,
      avg_engine_rpm: 1680.0,
      avg_engine_load_pct: 58.2,
      avg_fuel_rate_lhr: 8.4,
      fuel_consumed_liters: actualFuel,
      fuel_level_start: 94.5,
      fuel_level_end: parseFloat((94.5 - actualFuel).toFixed(1)),
      external_voltage: isMaintCritical ? 11.2 : 14.1,
      battery_voltage: 3.75,
      battery_current_ma: 145.0,
      dallas_temp_celsius: isMaintCritical ? 104.5 : 82.5,
      pcb_temp_celsius: 42.4
    },
    driver_score: {
      score: brief.driver_score,
      label: brief.driver_score >= 80 ? 'Good' : (brief.driver_score >= 60 ? 'Average' : 'Poor'),
      breakdown: {
        acceleration: -(accel * 0.5 > 20 ? 20 : accel * 0.5),
        braking: -(brake * 0.6 > 20 ? 20 : brake * 0.6),
        overspeed: -(overspeed * 1.0 > 25 ? 25 : overspeed * 1.0),
        cornering: -(cornering * 0.4 > 15 ? 15 : cornering * 0.4),
        idle_time: idle > 30 ? -parseFloat(((idle - 30) * 0.2 > 10 ? 10 : (idle - 30) * 0.2).toFixed(1)) : 0.0
      }
    },
    fuel_theft: {
      detected: isTheft,
      confidence: isTheft ? 85.0 : 12.0,
      status: isTheft ? 'ALERT' : 'NORMAL',
      reasons: isTheft 
        ? ["Sudden drop of 14.2 Liters detected while engine was off", "Variance above 30% against predicted model rates"]
        : []
    },
    expected_fuel: {
      expected_liters: expectedFuel,
      actual_liters: actualFuel,
      variance_pct: variance
    },
    maintenance: {
      priority: isMaintCritical ? 'Critical' : (brief.driver_score < 70 ? 'Warning' : 'OK'),
      alert_count: isMaintCritical ? 2 : (brief.driver_score < 70 ? 1 : 0),
      alerts: isMaintCritical 
        ? [
            {issue: 'Battery Issue', severity: 'Critical', detail: 'External voltage drop: 11.2 V (threshold < 11.5 V)'},
            {issue: 'Engine Overheating', severity: 'Critical', detail: 'Coolant temperature: 104.5°C exceeds max threshold of 100°C'}
          ]
        : (brief.driver_score < 70 
            ? [{issue: 'Brake Wear', severity: 'Warning', detail: 'Harsh braking frequency suggests high wear rates'}]
            : [])
    },
    speed_profile: speedProfile
  };
};

// ==================== DRIVER UTILITIES ====================
const getDriverColor = (driverId) => {
  const colors = [
    "#2563eb", // blue-600
    "#10b981", // emerald-500
    "#d97706", // amber-600
    "#ef4444", // red-500
    "#8b5cf6", // violet-500
    "#ec4899", // pink-500
    "#06b6d4", // cyan-500
    "#f59e0b", // amber-500
    "#14b8a6", // teal-500
    "#6366f1"  // indigo-500
  ];
  let hash = 0;
  for (let i = 0; i < driverId.length; i++) {
    hash = driverId.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
};

// Clean float32/float64 decimal precision issues from SQL Server telemetry
const cleanTripDetails = (data) => {
  if (data && data.journey) {
    data.journey.distance_km = parseFloat(Number(data.journey.distance_km).toFixed(2));
    data.journey.duration_min = parseFloat(Number(data.journey.duration_min).toFixed(1));
    data.journey.avg_speed_kmh = parseFloat(Number(data.journey.avg_speed_kmh).toFixed(1));
    data.journey.max_speed_kmh = parseFloat(Number(data.journey.max_speed_kmh).toFixed(1));
    data.journey.idle_time_min = parseFloat(Number(data.journey.idle_time_min).toFixed(1));
    data.journey.load_pct = parseFloat(Number(data.journey.load_pct).toFixed(1));
    data.journey.fuel_consumed_liters = parseFloat(Number(data.journey.fuel_consumed_liters).toFixed(2));
    data.journey.fuel_level_start = parseFloat(Number(data.journey.fuel_level_start).toFixed(1));
    data.journey.fuel_level_end = parseFloat(Number(data.journey.fuel_level_end).toFixed(1));
    if (data.journey.dallas_temp_celsius !== null && data.journey.dallas_temp_celsius !== undefined) {
      data.journey.dallas_temp_celsius = parseFloat(Number(data.journey.dallas_temp_celsius).toFixed(1));
    }
    if (data.journey.external_voltage !== null && data.journey.external_voltage !== undefined) {
      data.journey.external_voltage = parseFloat(Number(data.journey.external_voltage).toFixed(1));
    }
  }
  if (data && data.driver_score) {
    data.driver_score.score = parseFloat(Number(data.driver_score.score).toFixed(1));
    if (data.driver_score.breakdown) {
      Object.keys(data.driver_score.breakdown).forEach(key => {
        data.driver_score.breakdown[key] = parseFloat(Number(data.driver_score.breakdown[key]).toFixed(1));
      });
    }
    if (data.driver_score.component_scores) {
      Object.keys(data.driver_score.component_scores).forEach(key => {
        data.driver_score.component_scores[key] = parseFloat(Number(data.driver_score.component_scores[key]).toFixed(1));
      });
    }
  }
  if (data && data.expected_fuel) {
    data.expected_fuel.expected_liters = parseFloat(Number(data.expected_fuel.expected_liters).toFixed(2));
    data.expected_fuel.actual_liters = parseFloat(Number(data.expected_fuel.actual_liters).toFixed(2));
    data.expected_fuel.variance_pct = parseFloat(Number(data.expected_fuel.variance_pct).toFixed(1));
  }
  return data;
};

// --- COACHING INSIGHTS GENERATOR FOR FRONTEND ---
const InsightIcon = ({ iconType, className }) => {
  switch (iconType) {
    case 'ShieldAlert':
      return <ShieldAlert className={className} />;
    case 'Gauge':
      return <Gauge className={className} />;
    case 'Clock':
      return <Clock className={className} />;
    case 'TrendingUp':
      return <TrendingUp className={className} />;
    case 'Compass':
      return <Compass className={className} />;
    default:
      return <CheckCircle2 className={className} />;
  }
};

const getDriverInsights = (details) => {
  if (!details) return [];
  const insights = [];
  const score = details.driver_score?.score || 100;
  
  // 1. Check Speeding (highest severity priority)
  const speedEvents = details.journey?.overspeed_count || 0;
  const speedPenalty = Math.abs(details.driver_score?.breakdown?.overspeed || 0);
  if (speedPenalty > 2 || speedEvents > 0) {
    insights.push({
      type: 'speeding',
      text: 'Staying within speed limits improves fuel economy by up to 15% and ensures optimal driver safety ratings.',
      icon: 'Gauge',
      color: 'text-rose-600 bg-rose-50 border-rose-100',
      chipLabel: '⚡ SAFETY RISK',
      chipStyle: 'bg-rose-50 text-rose-700 border-rose-200/50',
      estimate: 'Est. Impact: Prevent speeding alarms & reduce road risk',
      penalty: speedPenalty || 5
    });
  }

  // 2. Check Braking
  const brakeEvents = details.journey?.brake_events || 0;
  const brakePenalty = Math.abs(details.driver_score?.breakdown?.braking || 0);
  if (brakePenalty > 2 || brakeEvents > 3) {
    insights.push({
      type: 'braking',
      text: 'Maintain a 3-second safety gap to avoid harsh braking events, preserving brake pad life and passenger comfort.',
      icon: 'ShieldAlert',
      color: 'text-amber-600 bg-amber-50 border-amber-100',
      chipLabel: '🔧 WEAR WARNING',
      chipStyle: 'bg-amber-50 text-amber-700 border-amber-200/50',
      estimate: 'Est. Impact: Extend brake pad lifecycle by 15-20%',
      penalty: brakePenalty || 4
    });
  }
  
  // 3. Check Idling
  const idleMin = details.journey?.idle_time_min || 0;
  const idlePenalty = Math.abs(details.driver_score?.breakdown?.idle_time || 0);
  if (idlePenalty > 2 || idleMin > 15) {
    insights.push({
      type: 'idling',
      text: 'Turn off the engine during halts longer than 2 minutes to conserve fuel and minimize emissions.',
      icon: 'Clock',
      color: 'text-indigo-600 bg-indigo-50 border-indigo-100',
      chipLabel: '🌱 ECO-DRIVING',
      chipStyle: 'bg-indigo-50 text-indigo-700 border-indigo-200/50',
      estimate: 'Est. Impact: Save ~0.8L fuel/hr during stops',
      penalty: idlePenalty || 3
    });
  }

  // 4. Check Acceleration
  const accelEvents = details.journey?.acceleration_events || 0;
  const accelPenalty = Math.abs(details.driver_score?.breakdown?.acceleration || 0);
  if (accelPenalty > 2 || accelEvents > 3) {
    insights.push({
      type: 'accel',
      text: 'Apply smooth, gradual acceleration inputs to enhance fuel economy and secure transported cargo.',
      icon: 'TrendingUp',
      color: 'text-orange-600 bg-orange-50 border-orange-100',
      chipLabel: '🌱 ECO-DRIVING',
      chipStyle: 'bg-orange-50 text-orange-700 border-orange-200/50',
      estimate: 'Est. Impact: Save fuel and protect cargo suspension',
      penalty: accelPenalty || 2
    });
  }

  // 5. Check Cornering
  const cornerEvents = details.journey?.cornering_events || 0;
  const cornerPenalty = Math.abs(details.driver_score?.breakdown?.cornering || 0);
  if (cornerPenalty > 2 || cornerEvents > 3) {
    insights.push({
      type: 'cornering',
      text: 'Take wide, smooth turns at reduced speeds to control high lateral G-forces and vehicle roll.',
      icon: 'Compass',
      color: 'text-blue-600 bg-blue-50 border-blue-100',
      chipLabel: '🔧 CARGO SECURITY',
      chipStyle: 'bg-blue-50 text-blue-700 border-blue-200/50',
      estimate: 'Est. Impact: Reduce lateral roll & stabilize load',
      penalty: cornerPenalty || 1
    });
  }

  // If no negative insights or excellent score
  if (insights.length === 0 || score >= 92) {
    return [{
      type: 'perfect',
      text: 'Perfect drive! Excellent speed control, minimal idling, and solid defensive handling throughout the journey.',
      icon: 'CheckCircle2',
      color: 'text-emerald-600 bg-emerald-50 border-emerald-100',
      chipLabel: '🏆 CLASS LEADER',
      chipStyle: 'bg-emerald-50 text-emerald-700 border-emerald-200/50',
      estimate: 'Est. Impact: All systems operating at peak safety',
      penalty: 0
    }];
  }

  // Sort insights by penalty severity so that the biggest issue is shown first
  return insights.sort((a, b) => b.penalty - a.penalty);
};

export default function App() {
  // --- UI STATES ---
  const [drivers, setDrivers] = useState([]);
  const [activeDriverId, setActiveDriverId] = useState(null);
  const [journeys, setJourneys] = useState([]);
  const [activeJourneyId, setActiveJourneyId] = useState(null);
  const [journeyDetails, setJourneyDetails] = useState(null);
  const [mobileViewTab, setMobileViewTab] = useState('drivers');
  
  // --- LOADERS / CONTROL ---
  const [searchTerm, setSearchTerm] = useState('');
  const [isLoadingDrivers, setIsLoadingDrivers] = useState(true);
  const [isLoadingJourneys, setIsLoadingJourneys] = useState(false);
  const [isLoadingDetails, setIsLoadingDetails] = useState(false);
  const [isRecomputing, setIsRecomputing] = useState(false);
  const [isUsingMock, setIsUsingMock] = useState(false);

  // --- 1. LOAD DRIVERS ---
  useEffect(() => {
    const fetchDrivers = async () => {
      setIsLoadingDrivers(true);
      try {
        const res = await fetch('/api/drivers/');
        if (!res.ok) throw new Error('API offline');
        const data = await res.json();
        
        const enriched = data.map(d => ({
          ...d,
          name: d.driver_name,
          avatar_color: getDriverColor(d.driver_id),
          vehicle_type: d.vehicle_type,
          vehicle_id: d.vehicle_id
        }));
        
        setDrivers(enriched);
        setIsUsingMock(false);
        if (enriched.length > 0) {
          setActiveDriverId(enriched[0].driver_id);
        }
      } catch (err) {
        console.warn("Backend API not reachable. Switching to high-fidelity frontend fallback mock data.");
        setDrivers(MOCK_DRIVERS);
        setIsUsingMock(true);
        if (MOCK_DRIVERS.length > 0) {
          setActiveDriverId(MOCK_DRIVERS[0].driver_id);
        }
      } finally {
        setIsLoadingDrivers(false);
      }
    };
    fetchDrivers();
  }, []);

  // --- 2. LOAD JOURNEYS (triggers when activeDriverId changes) ---
  useEffect(() => {
    if (!activeDriverId) return;
    
    const fetchJourneys = async () => {
      setIsLoadingJourneys(true);
      setJourneyDetails(null);
      setActiveJourneyId(null);
      
      if (isUsingMock) {
        // Mock execution
        setTimeout(() => {
          const list = generateMockJourneys(activeDriverId);
          setJourneys(list);
          if (list.length > 0) {
            setActiveJourneyId(list[0].journey_id);
          }
          setIsLoadingJourneys(false);
        }, 300);
      } else {
        try {
          // Maps to GET /drivers/{driver_id}/trips on FastAPI
          const res = await fetch(`/api/drivers/${activeDriverId}/trips`);
          if (!res.ok) throw new Error('Network error');
          const list = await res.json();
          // Normalize: backend returns trip_id, frontend uses journey_id
          const normalized = list.map(t => ({
            journey_id:   t.trip_id,
            route_type:   t.route_type,
            start_time:   t.trip_start || '',
            distance_km:  parseFloat(Number(t.distance_km).toFixed(2)),
            duration_min: parseFloat(Number(t.trip_duration_min).toFixed(1)),
            driver_score: parseFloat(Number(t.final_score).toFixed(1)),
            fuel_theft_detected: false,
            maintenance_critical: false,
          }));
          setJourneys(normalized);
          if (normalized.length > 0) {
            setActiveJourneyId(normalized[0].journey_id);
          }
        } catch (err) {
          console.error("Error loading journeys", err);
        } finally {
          setIsLoadingJourneys(false);
        }
      }
    };
    fetchJourneys();
  }, [activeDriverId, isUsingMock]);

  // --- 3. LOAD JOURNEY DETAILS (triggers when activeJourneyId changes) ---
  useEffect(() => {
    if (!activeJourneyId) return;
    
    const fetchDetails = async () => {
      setIsLoadingDetails(true);
      if (isUsingMock) {
        // Mock execution
        setTimeout(() => {
          const data = getMockJourneyDetails(activeJourneyId, activeDriverId);
          setJourneyDetails(data);
          setIsLoadingDetails(false);
        }, 400);
      } else {
        try {
          // Maps to GET /drivers/{driver_id}/trips/{trip_id}/details on FastAPI
          const res = await fetch(`/api/drivers/${activeDriverId}/trips/${activeJourneyId}/details`);
          if (!res.ok) throw new Error('Network error');
          const rawData = await res.json();
          const data = cleanTripDetails(rawData);
          
          // Generate speed profile from avg_speed if backend doesn't have telemetry stream
          if (!data.speed_profile) {
            const avgSpd = data.journey.avg_speed_kmh || 60;
            data.speed_profile = Array.from({length: 12}, (_, k) => ({
              time: `${k * 10}m`,
              speed: data.journey.route_type === 'Highway' 
                ? Math.round(avgSpd + Math.sin(k) * 12 + (k === 5 ? 18 : 0))
                : Math.round(avgSpd * 0.7 + Math.sin(k * 2) * 15)
            }));
          }
          
          setJourneyDetails(data);
        } catch (err) {
          console.error("Error loading journey details", err);
        } finally {
          setIsLoadingDetails(false);
        }
      }
    };
    fetchDetails();
  }, [activeJourneyId, activeDriverId, isUsingMock]);

  // --- 4. RECOMPUTE SAFETY MODELS ---
  const handleRecompute = async () => {
    if (!activeJourneyId) return;
    setIsRecomputing(true);
    
    if (isUsingMock) {
      // Mock recomputation logic
      setTimeout(() => {
        const details = getMockJourneyDetails(activeJourneyId, activeDriverId);
        // Slightly alter the score to show it recomputed successfully!
        details.driver_score.score = Math.min(100, details.driver_score.score + 1);
        setJourneyDetails(details);
        setIsRecomputing(false);
      }, 1000);
    } else {
      try {
        // Re-fetch the details endpoint (scorer always recomputes live)
        const res = await fetch(`/api/drivers/${activeDriverId}/trips/${activeJourneyId}/details`);
        if (!res.ok) throw new Error('Recompute failed');
        const rawData = await res.json();
        const data = cleanTripDetails(rawData);
        
        if (!data.speed_profile) {
          const avgSpd = data.journey.avg_speed_kmh || 60;
          data.speed_profile = Array.from({length: 12}, (_, k) => ({
            time: `${k * 10}m`,
            speed: data.journey.route_type === 'Highway' 
              ? Math.round(avgSpd + Math.sin(k) * 12 + (k === 5 ? 18 : 0))
              : Math.round(avgSpd * 0.7 + Math.sin(k * 2) * 15)
          }));
        }
        
        setJourneyDetails(data);
      } catch (err) {
        console.error("Recompute API failed", err);
      } finally {
        setIsRecomputing(false);
      }
    }
  };

  // --- 5. SEARCH & FILTER ---
  const filteredDrivers = drivers.filter(d => 
    d.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    d.driver_id.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const activeDriver = drivers.find(d => d.driver_id === activeDriverId) || MOCK_DRIVERS[0];

  // Helper colors for Score pill badges
  const getScoreColorClass = (score) => {
    if (score >= 80) return 'bg-emerald-50 text-emerald-700 border border-emerald-200';
    if (score >= 60) return 'bg-amber-50 text-amber-700 border border-amber-200';
    return 'bg-rose-50 text-rose-700 border border-rose-200';
  };

  // Aggregate values
  const totalFleetTrips = drivers.reduce((acc, curr) => acc + curr.total_trips, 0);
  const totalFleetDist = drivers.reduce((acc, curr) => acc + curr.total_distance_km, 0);

  return (
    <div className="h-full flex flex-col font-sans bg-[#f8fafc] text-slate-700 select-text">
      
      {/* -------------------- HEADER NAVBAR -------------------- */}
      <header className="h-16 flex items-center justify-between px-6 bg-white border-b border-slate-200/80 shrink-0 shadow-sm z-10">
        <div className="flex items-center gap-3">
          <div className="bg-brand-500 text-white p-2 rounded-xl shadow-brand-glow">
            <Compass className="w-6 h-6 animate-spin-slow" />
          </div>
          <div>
            <h1 className="text-xl font-extrabold font-outfit text-slate-900 leading-tight tracking-tight">
              FleetIQ <span className="text-brand-500 font-medium text-xs px-2 py-0.5 rounded-full bg-brand-50 ml-1 border border-brand-100">Live</span>
            </h1>
            <p className="text-[10px] text-slate-400 font-medium tracking-wide uppercase">Unified Fleet Intelligence Dashboard</p>
          </div>
        </div>

        {/* Global Stats Pill Bar */}
        <div className="hidden lg:flex items-center gap-6 text-xs font-semibold">
          <div className="flex items-center gap-2.5 px-3 py-1.5 bg-slate-50 border border-slate-200/60 rounded-xl shadow-sm">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 pulse-glow-green"></span>
            <span className="text-slate-400">Status:</span>
            <span className="text-slate-700 uppercase font-bold">{isUsingMock ? "Mock Fallback Demo" : "Connected (SQL Server)"}</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Total Trips:</span>
            <span className="text-slate-800 font-bold font-outfit text-sm">{(totalFleetTrips || 13548).toLocaleString()}</span>
          </div>
          <div className="w-1.5 h-1.5 rounded-full bg-slate-300"></div>
          <div className="flex items-center gap-2">
            <span className="text-slate-400">Distance Travelled:</span>
            <span className="text-slate-800 font-bold font-outfit text-sm">{(totalFleetDist ? Math.round(totalFleetDist) : 5576000).toLocaleString()} km</span>
          </div>
        </div>

        <div className="flex items-center gap-4">
          <div className="w-9 h-9 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-500 hover:text-brand-500 transition-colors cursor-pointer">
            <User className="w-4.5 h-4.5" />
          </div>
        </div>
      </header>

      {/* -------------------- MAIN WORKSPACE -------------------- */}
      <div className="flex-1 flex overflow-hidden">
        
        {/* -------------------- LEFT SIDEBAR (DRIVERS LIST) -------------------- */}
        <aside className={`w-full lg:w-64 xl:w-80 border-r border-slate-200 bg-white flex flex-col shrink-0 z-10 shadow-sm ${
          mobileViewTab === 'drivers' ? 'flex' : 'hidden lg:flex'
        }`}>
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
                    className={`w-full flex items-center gap-3.5 p-3 rounded-xl transition-all text-left relative ${
                      isActive 
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
                        <span className="text-sm font-bold text-slate-900 truncate font-outfit">{d.name}</span>
                        <span className={`text-[10px] px-1.5 py-0.5 rounded font-bold shrink-0 ${getScoreColorClass(d.avg_score)}`}>
                          {d.avg_score}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-[11px] font-medium text-slate-400">
                        <span className="truncate flex items-center gap-1">
                          <Truck className="w-3.5 h-3.5 shrink-0 text-slate-300" /> {d.vehicle_type}
                        </span>
                        <span>{d.total_trips} trips</span>
                      </div>
                    </div>
                  </button>
                );
              })
            )}
          </div>
        </aside>

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
              {/* -------------------- PANEL 1: DRIVER TRIPS (MIDDLE COLUMN) -------------------- */}
              <section className={`w-full lg:w-64 xl:w-80 border-r border-slate-200 bg-white flex flex-col shrink-0 z-0 ${
                mobileViewTab === 'journeys' ? 'flex' : 'hidden lg:flex'
              }`}>
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
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-brand-50 text-brand-600 font-bold border border-brand-100 inline-block mb-1">
                    {activeDriver.driver_id}
                  </span>
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
            <div className="px-5 py-3 border-b border-slate-100 bg-slate-50/50 flex items-center justify-between shrink-0">
              <span className="text-xs font-bold text-slate-900 font-outfit tracking-wide uppercase">Journey History</span>
              <span className="text-[10px] px-2 py-0.5 bg-slate-200/60 text-slate-600 font-bold rounded-full">{journeys.length} Records</span>
            </div>

            {/* Journeys List */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {isLoadingJourneys ? (
                <div className="h-40 flex flex-col items-center justify-center gap-2">
                  <RefreshCw className="w-5 h-5 text-brand-500 animate-spin" />
                  <span className="text-xs text-slate-400 font-medium">Retrieving journeys...</span>
                </div>
              ) : journeys.length === 0 ? (
                <div className="text-center p-6 text-xs text-slate-400 font-medium">No recorded journeys found.</div>
              ) : (
                journeys.map(j => {
                  const isActive = j.journey_id === activeJourneyId;
                  const hasAlert = j.fuel_theft_detected || j.maintenance_critical;
                  
                  return (
                    <button
                      key={j.journey_id}
                      onClick={() => {
                        setActiveJourneyId(j.journey_id);
                        setMobileViewTab('details');
                      }}
                      className={`w-full p-3 rounded-xl transition-all text-left border relative flex flex-col gap-2 ${
                        isActive 
                          ? 'bg-brand-50/30 border-brand-200 shadow-sm' 
                          : 'bg-white border-slate-200/70 hover:border-slate-300'
                      }`}
                    >
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
                        <div className={`mt-1 py-1 px-2 rounded-lg text-[10px] font-bold flex items-center justify-between relative overflow-hidden ${
                          j.fuel_theft_detected 
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

          {/* -------------------- PANEL 2: DRILL-DOWN ANALYTICS (RIGHT WORKSPACE) -------------------- */}
          <section className={`flex-1 bg-slate-50 flex flex-col overflow-hidden relative ${
            mobileViewTab === 'details' ? 'flex' : 'hidden lg:flex'
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
                <div className="p-4 bg-white border-b border-slate-200/80 flex flex-wrap items-center justify-between gap-4 shrink-0 shadow-sm">
                  <div className="flex items-center gap-3">
                    <button
                      onClick={() => setMobileViewTab('journeys')}
                      className="lg:hidden p-1.5 hover:bg-slate-100 rounded-xl text-slate-500 transition-colors shrink-0"
                    >
                      <ArrowLeft className="w-5 h-5" />
                    </button>
                    <span className="text-xs font-black bg-brand-500 text-white px-2.5 py-1 rounded-xl shadow-brand-glow font-outfit tracking-wider">
                      TRIP {journeyDetails.journey.journey_id}
                    </span>
                    <div className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
                      <span className="font-bold text-slate-700">{journeyDetails.journey.start_time}</span>
                      <span>to</span>
                      <span className="font-bold text-slate-700">{journeyDetails.journey.end_time.split(' ')[1]}</span>
                      <span className="w-1 h-1 rounded-full bg-slate-300"></span>
                      <span className="text-slate-500 font-semibold uppercase">{journeyDetails.journey.route_type} route</span>
                    </div>
                  </div>

                  {/* Summary ribbon */}
                  <div className="flex items-center gap-4 text-xs font-bold text-slate-700">
                    <div className="bg-slate-50 border border-slate-200/60 py-1.5 px-3 rounded-xl flex items-center gap-2">
                      <Navigation className="w-4 h-4 text-slate-400" />
                      <span>{journeyDetails.journey.distance_km} km</span>
                    </div>
                    <div className="bg-slate-50 border border-slate-200/60 py-1.5 px-3 rounded-xl flex items-center gap-2">
                      <Clock className="w-4 h-4 text-slate-400" />
                      <span>{journeyDetails.journey.duration_min} mins</span>
                    </div>
                    <div className="bg-slate-50 border border-slate-200/60 py-1.5 px-3 rounded-xl flex items-center gap-2">
                      <MapPin className="w-4 h-4 text-slate-400" />
                      <span>{journeyDetails.journey.stops} stops</span>
                    </div>
                  </div>
                </div>

                {/* Dashboard Cards Grid Container */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                  
                  {/* 2x2 Grid of Modules */}
                  <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                    
                    {/* -------------------- CARD 1: DRIVER SCORE CARD -------------------- */}
                    <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-premium flex flex-col justify-between hover:shadow-premium-lg transition-shadow">
                      <div>
                        <div className="flex items-center justify-between border-b border-slate-100 pb-3.5 mb-4">
                          <h3 className="text-sm font-extrabold text-slate-800 font-outfit tracking-wide flex items-center gap-2 uppercase">
                            <Gauge className="w-4.5 h-4.5 text-brand-500" /> Driver Safety Score
                          </h3>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${
                            journeyDetails.driver_score.score >= 80 
                              ? 'bg-emerald-50 text-emerald-700 border-emerald-200' 
                              : (journeyDetails.driver_score.score >= 60 
                                  ? 'bg-amber-50 text-amber-700 border-amber-200' 
                                  : 'bg-rose-50 text-rose-700 border-rose-200')
                          }`}>
                            {journeyDetails.driver_score.label} Classification
                          </span>
                        </div>

                        {/* Circular Score Gauge & Layout */}
                        <div className="flex flex-col sm:flex-row xl:flex-col 2xl:flex-row items-center gap-8 mb-5 w-full">
                          {/* Circle Progress bar */}
                          <div className="relative w-[130px] h-[130px] sm:ml-6 xl:ml-0 2xl:ml-6 shrink-0 flex items-center justify-center">
                            <svg className="w-full h-full transform -rotate-90" viewBox="0 0 100 100">
                              <defs>
                                {/* Premium Gradients for Score classification */}
                                <linearGradient id="scoreEmerald" x1="0%" y1="0%" x2="100%" y2="100%">
                                  <stop offset="0%" stopColor="#10b981" />
                                  <stop offset="100%" stopColor="#059669" />
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
                                strokeDashoffset={251.2 - (251.2 * journeyDetails.driver_score.score) / 100} 
                                strokeLinecap="round" 
                                stroke={
                                  journeyDetails.driver_score.score >= 80 
                                    ? 'url(#scoreEmerald)' 
                                    : (journeyDetails.driver_score.score >= 60 ? 'url(#scoreAmber)' : 'url(#scoreRose)')
                                }
                                fill="transparent" 
                                r="40" 
                                cx="50" 
                                cy="50" 
                              />
                            </svg>
                            <div className="absolute text-center flex flex-col items-center justify-center">
                              <span className={`text-[38px] font-black font-outfit tracking-tight leading-none ${
                                journeyDetails.driver_score.score >= 80 
                                  ? 'text-emerald-600' 
                                  : (journeyDetails.driver_score.score >= 60 ? 'text-amber-600' : 'text-rose-600')
                              }`}>
                                {journeyDetails.driver_score.score}
                              </span>
                              <span className="text-[8.5px] text-slate-400 font-extrabold uppercase mt-1 tracking-widest select-none">
                                score
                              </span>
                            </div>
                          </div>

                          {/* Quick Stats on events */}
                          <div className="w-full sm:w-auto sm:min-w-[230px] sm:max-w-[250px] xl:w-full xl:max-w-none 2xl:w-auto 2xl:min-w-[230px] 2xl:max-w-[250px] sm:ml-auto xl:ml-0 2xl:ml-auto space-y-1.5 text-[11px]">
                            <div className="flex items-center justify-between gap-2 text-slate-600 p-1 hover:bg-slate-50 rounded-xl transition-all duration-200">
                              <span className="font-bold text-slate-600 flex items-center gap-2 select-none shrink-0">
                                <span className={`w-2 h-2 rounded-full shrink-0 ${
                                  journeyDetails.journey.acceleration_events === 0 ? 'bg-emerald-500 shadow-sm shadow-emerald-400' : (journeyDetails.journey.acceleration_events < 4 ? 'bg-amber-500' : 'bg-rose-500')
                                }`} />
                                Accelerations
                              </span>
                              <span className="font-extrabold text-slate-700 shrink-0 bg-slate-100/80 px-2 py-0.5 rounded-lg text-[9.5px] font-outfit select-none">
                                {journeyDetails.journey.acceleration_events} events
                              </span>
                            </div>
                            <div className="flex items-center justify-between gap-2 text-slate-600 p-1 hover:bg-slate-50 rounded-xl transition-all duration-200">
                              <span className="font-bold text-slate-600 flex items-center gap-2 select-none shrink-0">
                                <span className={`w-2 h-2 rounded-full shrink-0 ${
                                  journeyDetails.journey.brake_events === 0 ? 'bg-emerald-500 shadow-sm shadow-emerald-400' : (journeyDetails.journey.brake_events < 4 ? 'bg-amber-500' : 'bg-rose-500')
                                }`} />
                                Harsh Braking
                              </span>
                              <span className="font-extrabold text-slate-700 shrink-0 bg-slate-100/80 px-2 py-0.5 rounded-lg text-[9.5px] font-outfit select-none">
                                {journeyDetails.journey.brake_events} events
                              </span>
                            </div>
                            <div className="flex items-center justify-between gap-2 text-slate-600 p-1 hover:bg-slate-50 rounded-xl transition-all duration-200">
                              <span className="font-bold text-slate-600 flex items-center gap-2 select-none shrink-0">
                                <span className={`w-2 h-2 rounded-full shrink-0 ${
                                  journeyDetails.journey.overspeed_count === 0 ? 'bg-emerald-500 shadow-sm shadow-emerald-400' : (journeyDetails.journey.overspeed_count < 2 ? 'bg-amber-500' : 'bg-rose-500')
                                }`} />
                                Overspeeding
                              </span>
                              <span className="font-extrabold text-slate-700 shrink-0 bg-slate-100/80 px-2 py-0.5 rounded-lg text-[9.5px] font-outfit select-none">
                                {journeyDetails.journey.overspeed_count} events
                              </span>
                            </div>
                            <div className="flex items-center justify-between gap-2 text-slate-600 p-1 hover:bg-slate-50 rounded-xl transition-all duration-200">
                              <span className="font-bold text-slate-600 flex items-center gap-2 select-none shrink-0">
                                <span className={`w-2 h-2 rounded-full shrink-0 ${
                                  (journeyDetails.journey.idle_time_min || 0) < 10 ? 'bg-emerald-500 shadow-sm shadow-emerald-400' : ((journeyDetails.journey.idle_time_min || 0) < 25 ? 'bg-amber-500' : 'bg-rose-500')
                                }`} />
                                Excessive Idling
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
                          text: "Excellent defensive driving! All safety metrics are within optimal green thresholds.",
                          icon: "CheckCircle2",
                          color: "text-emerald-600 bg-emerald-50 border-emerald-100",
                          chipLabel: "🏆 CLASS LEADER",
                          chipStyle: "bg-emerald-50 text-emerald-700 border-emerald-200/50",
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

                    {/* -------------------- CARD 2: FUEL THEFT CARD -------------------- */}
                    <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-premium flex flex-col justify-between hover:shadow-premium-lg transition-shadow">
                      <div>
                        <div className="flex items-center justify-between border-b border-slate-100 pb-3.5 mb-4">
                          <h3 className="text-sm font-extrabold text-slate-800 font-outfit tracking-wide flex items-center gap-2 uppercase">
                            <Droplet className="w-4.5 h-4.5 text-brand-500" /> Fuel Theft Detection
                          </h3>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${
                            journeyDetails.fuel_theft.detected 
                              ? 'bg-rose-50 text-rose-700 border-rose-200' 
                              : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          }`}>
                            {journeyDetails.fuel_theft.detected ? 'ALERT HIGH RISK' : 'NORMAL SECURED'}
                          </span>
                        </div>

                        {/* Status pulsing bar */}
                        <div className={`p-4 rounded-2xl flex flex-col sm:flex-row xl:flex-col 2xl:flex-row items-start sm:items-center xl:items-start 2xl:items-center gap-4 mb-5 border transition-all ${
                          journeyDetails.fuel_theft.detected
                            ? 'bg-rose-50/50 border-rose-200/50 pulse-glow-red'
                            : 'bg-emerald-50/50 border-emerald-200/50'
                        }`}>
                          <div className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 ${
                            journeyDetails.fuel_theft.detected ? 'bg-rose-500 text-white' : 'bg-emerald-500 text-white'
                          }`}>
                            {journeyDetails.fuel_theft.detected ? <ShieldAlert className="w-5 h-5" /> : <ShieldCheck className="w-5 h-5" />}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="text-xs text-slate-400 font-bold tracking-wide uppercase">Fuel Security Monitor</p>
                            <p className="text-sm font-extrabold text-slate-800 font-outfit break-words">
                              {journeyDetails.fuel_theft.detected 
                                ? `Fuel theft event suspected (Confidence: ${journeyDetails.fuel_theft.confidence}%)`
                                : "No suspicious fuel variations identified."
                              }
                            </p>
                          </div>
                        </div>
                      </div>

                      {/* Theft Forensics Details */}
                      <div className="bg-slate-50 rounded-2xl border border-slate-200/50 p-4 flex-1 flex flex-col justify-center">
                        <span className="text-[9px] text-slate-400 font-bold tracking-wide uppercase block mb-2">Suspected Forensics Check</span>
                        {journeyDetails.fuel_theft.detected ? (
                          <ul className="space-y-2 text-xs font-semibold text-slate-700">
                            {journeyDetails.fuel_theft.reasons.map((r, ri) => (
                              <li key={ri} className="flex items-start gap-2 text-rose-600 bg-rose-50/50 border border-rose-100/50 p-2.5 rounded-xl">
                                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5 text-rose-500" />
                                <span>{r}</span>
                              </li>
                            ))}
                          </ul>
                        ) : (
                          <div className="space-y-2 text-xs font-semibold text-slate-500">
                            <div className="flex items-center gap-2 py-1 border-b border-slate-200/30">
                              <CheckCircle2 className="w-4.5 h-4.5 text-emerald-500 shrink-0" />
                              <span>No drops detected when ignition was OFF</span>
                            </div>
                            <div className="flex items-center gap-2 py-1 border-b border-slate-200/30">
                              <CheckCircle2 className="w-4.5 h-4.5 text-emerald-500 shrink-0" />
                              <span>Fuel consumption levels remain within expected variance thresholds</span>
                            </div>
                            <div className="flex items-center gap-2">
                              <CheckCircle2 className="w-4.5 h-4.5 text-emerald-500 shrink-0" />
                              <span>All fuel level variations trace perfectly to engine load speeds</span>
                            </div>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* -------------------- CARD 3: EXPECTED FUEL CHART -------------------- */}
                    <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-premium flex flex-col justify-between hover:shadow-premium-lg transition-shadow">
                      <div>
                        <div className="flex items-center justify-between border-b border-slate-100 pb-3.5 mb-4">
                          <h3 className="text-sm font-extrabold text-slate-800 font-outfit tracking-wide flex items-center gap-2 uppercase">
                            <Activity className="w-4.5 h-4.5 text-brand-500" /> Predictive Expected Fuel
                          </h3>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${
                            Math.abs(journeyDetails.expected_fuel.variance_pct) > 20
                              ? 'bg-rose-50 text-rose-700 border-rose-200'
                              : 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          }`}>
                            Variance: {journeyDetails.expected_fuel.variance_pct > 0 ? '+' : ''}{(journeyDetails.expected_fuel.variance_pct || 0).toFixed(1)}%
                          </span>
                        </div>

                        {/* Side-by-side Recharts bar chart */}
                        <div className="h-44 w-full mt-3">
                          <ResponsiveContainer width="100%" height="100%">
                            <BarChart
                              data={[
                                {name: 'Predicted Expected', fuel: journeyDetails.expected_fuel.expected_liters, fill: '#3b82f6'},
                                {name: 'Actual Consumed', fuel: journeyDetails.expected_fuel.actual_liters, fill: journeyDetails.fuel_theft.detected ? '#f43f5e' : '#10b981'}
                              ]}
                              margin={{ top: 10, right: 10, left: -25, bottom: 0 }}
                              barSize={40}
                            >
                              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                              <XAxis dataKey="name" stroke="#94a3b8" fontSize={11} fontWeight={600} tickLine={false} />
                              <YAxis stroke="#94a3b8" fontSize={11} fontWeight={600} tickLine={false} />
                              <Tooltip cursor={{fill: 'transparent'}} contentStyle={{ borderRadius: '12px', border: '1px solid #e2e8f0', fontSize: '11px', fontWeight: 'bold' }} />
                              <Bar dataKey="fuel" radius={[8, 8, 0, 0]}>
                                {/* Map fills dynamically */}
                                <svg>
                                  <defs>
                                    <linearGradient id="blueGrad" x1="0" y1="0" x2="0" y2="1">
                                      <stop offset="0%" stopColor="#3b82f6" />
                                      <stop offset="100%" stopColor="#2563eb" />
                                    </linearGradient>
                                    <linearGradient id="greenGrad" x1="0" y1="0" x2="0" y2="1">
                                      <stop offset="0%" stopColor="#10b981" />
                                      <stop offset="100%" stopColor="#059669" />
                                    </linearGradient>
                                    <linearGradient id="redGrad" x1="0" y1="0" x2="0" y2="1">
                                      <stop offset="0%" stopColor="#f43f5e" />
                                      <stop offset="100%" stopColor="#dc2626" />
                                    </linearGradient>
                                  </defs>
                                </svg>
                                {
                                  [
                                    {fill: 'url(#blueGrad)'},
                                    {fill: journeyDetails.fuel_theft.detected ? 'url(#redGrad)' : 'url(#greenGrad)'}
                                  ].map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.fill} />
                                  ))
                                }
                              </Bar>
                            </BarChart>
                          </ResponsiveContainer>
                        </div>
                      </div>

                      {/* Model parameters explanation */}
                      <div className="bg-slate-50 rounded-2xl border border-slate-200/50 p-4 mt-4 grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2 gap-3 text-[11px] font-semibold text-slate-500">
                        <div>
                          <p className="text-[9px] text-slate-400 font-bold uppercase mb-1">Route & Idle Adjustments</p>
                          <div className="space-y-1">
                            <div className="flex justify-between">
                              <span>Route Multiplier:</span>
                              <span className="text-slate-800 font-extrabold">{journeyDetails.journey.route_type === 'Highway' ? '0.90x' : (journeyDetails.journey.route_type === 'City' ? '1.25x' : '1.05x')}</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Idle Fuel Penalty:</span>
                              <span className="text-slate-800 font-extrabold">{(journeyDetails.journey.idle_time_min * 0.08).toFixed(2)} L</span>
                            </div>
                          </div>
                        </div>
                        <div>
                          <p className="text-[9px] text-slate-400 font-bold uppercase mb-1">Load Factor Adjustments</p>
                          <div className="space-y-1">
                            <div className="flex justify-between">
                              <span>Cargo Load %:</span>
                              <span className="text-slate-800 font-extrabold">{(journeyDetails.journey.load_pct || 0).toFixed(1)}%</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Consumption Factor:</span>
                              <span className="text-slate-800 font-extrabold">x{(1 + (journeyDetails.journey.load_pct / 100) * 0.15).toFixed(2)}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* -------------------- CARD 4: VEHICLE MAINTENANCE DIAGNOSTIC -------------------- */}
                    <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-premium flex flex-col justify-between hover:shadow-premium-lg transition-shadow">
                      <div>
                        <div className="flex items-center justify-between border-b border-slate-100 pb-3.5 mb-4">
                          <h3 className="text-sm font-extrabold text-slate-800 font-outfit tracking-wide flex items-center gap-2 uppercase">
                            <Wrench className="w-4.5 h-4.5 text-brand-500" /> Vehicle Maintenance diagnostics
                          </h3>
                          <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold border ${
                            journeyDetails.maintenance.priority === 'Critical' 
                              ? 'bg-rose-50 text-rose-700 border-rose-200' 
                              : (journeyDetails.maintenance.priority === 'Warning'
                                  ? 'bg-amber-50 text-amber-700 border-amber-200'
                                  : 'bg-emerald-50 text-emerald-700 border-emerald-200')
                          }`}>
                            Diagnostic: {journeyDetails.maintenance.priority}
                          </span>
                        </div>

                        {/* Sensory parameters diagnostics */}
                        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-1 2xl:grid-cols-2 gap-4 mb-4">
                          <div className={`p-3 rounded-2xl border transition-all ${
                            journeyDetails.journey.external_voltage < 11.5 ? 'bg-rose-50 border-rose-200' : 'bg-slate-50 border-slate-200/40'
                          }`}>
                            <div className="flex items-center gap-2 text-slate-400 mb-1.5">
                              <Battery className={`w-4.5 h-4.5 ${journeyDetails.journey.external_voltage < 11.5 ? 'text-rose-500 animate-pulse' : 'text-slate-400'}`} />
                              <span className="text-[10px] font-bold uppercase">Battery Voltage</span>
                            </div>
                            <p className={`text-base font-black font-outfit ${journeyDetails.journey.external_voltage < 11.5 ? 'text-rose-700' : 'text-slate-800'}`}>
                              {(journeyDetails.journey.external_voltage || 0).toFixed(1)} V
                            </p>
                          </div>
                          
                          <div className={`p-3 rounded-2xl border transition-all ${
                            journeyDetails.journey.dallas_temp_celsius > 100.0 ? 'bg-rose-50 border-rose-200' : 'bg-slate-50 border-slate-200/40'
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
                      </div>

                      {/* Diagnostics list */}
                      <div className="bg-slate-50 rounded-2xl border border-slate-200/50 p-4 flex-1 flex flex-col justify-center">
                        <span className="text-[9px] text-slate-400 font-bold tracking-wide uppercase block mb-2">Predictive Issue Analyzer</span>
                        {journeyDetails.maintenance.alerts.length > 0 ? (
                          <div className="space-y-2.5">
                            {journeyDetails.maintenance.alerts.map((a, ai) => (
                              <div key={ai} className={`text-xs p-2.5 rounded-xl border flex items-start gap-2.5 ${
                                a.severity === 'Critical' 
                                  ? 'bg-rose-50/50 border-rose-100 text-rose-700' 
                                  : 'bg-amber-50/50 border-amber-100 text-amber-700'
                              }`}>
                                <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                                <div>
                                  <p className="font-extrabold font-outfit leading-none mb-1">{a.issue}</p>
                                  <p className="text-[11px] font-semibold text-slate-500 leading-snug">{a.detail}</p>
                                </div>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-center py-4 space-y-1 text-slate-400">
                            <CheckCircle2 className="w-8 h-8 text-emerald-500 mx-auto" />
                            <p className="text-xs font-bold text-slate-700 font-outfit">All Vehicle Systems Healthy</p>
                            <p className="text-[10px] font-semibold max-w-[200px] mx-auto">Sensors verify braking, cornering forces, and engine heat are optimal.</p>
                          </div>
                        )}
                      </div>
                    </div>

                  </div>


                </div>
              </div>
            )}
          </section>
            </>
          )}

        </main>
      </div>

    </div>
  );
}
