import React, { useState, useEffect } from 'react';
import {
  Activity, UserPlus, Truck, Info, Terminal, Calendar, Clock,
  ArrowRight, ShieldAlert, CheckCircle2, Navigation, AlertTriangle
} from 'lucide-react';

const getDriverColor = (driverId) => {
  const colors = [
    "#2563eb", // blue-600
    "#10b981", // emerald-500
    "#d97706", // amber-600
    "#ef4444", // red-500
    "#8b5cf6", // violet-500
    "#ec4899", // pink-500
    "#06b6d4", // cyan-500
    "#f97316", // orange-500
  ];
  const num = parseInt(driverId.replace(/\D/g, ""), 10) || 0;
  return colors[num % colors.length];
};

export default function DeviceSimulator({
  isOpen,
  onClose,
  drivers,
  setDrivers,
  activeDriverId,
  setActiveDriverId,
  setJourneys,
  setActiveJourneyId,
  setFuelAlerts,
  setShowAlertToast,
  isUsingMock
}) {
  const [activeTab, setActiveTab] = useState('trip'); // 'trip', 'driver', 'vehicle'
  const [simStatusMsg, setSimStatusMsg] = useState('');
  const [isSimSubmitting, setIsSimSubmitting] = useState(false);


  
  // Simulator logs state
  const [simLogs, setSimLogs] = useState([
    '[System] Simulator Control Panel initialized.',
    '[System] Ready for manual inputs and live device telemetry simulation.'
  ]);

  // Vehicles list — loaded from DB when live, or derived from drivers in mock mode
  const [vehicles, setVehicles] = useState([]);

  // Load vehicles from DB (live mode) or seed from drivers (mock mode)
  useEffect(() => {
    if (isUsingMock) {
      // Derive vehicles from drivers list for mock mode
      const derived = drivers.map(d => ({
        vehicle_id: d.vehicle_id || `VH0${d.driver_id.replace('DR', '')}`,
        reg_no: `GJ-01-XX-${Math.floor(1000 + Math.random() * 9000)}`,
        vehicle_name: `${d.vehicle_type || 'Mini Truck'} Engine`,
        vehicle_type: d.vehicle_type || 'Mini Truck',
        make: 'Tata',
        model: '2024',
        is_active: true
      }));
      const unique = [];
      const seen = new Set();
      for (const v of derived) {
        if (!seen.has(v.vehicle_id)) { seen.add(v.vehicle_id); unique.push(v); }
      }
      setVehicles(unique);
    } else {
      // Fetch vehicles from DB via API
      fetch('/api/simulation/vehicles')
        .then(r => r.ok ? r.json() : [])
        .then(data => {
          if (data && data.length > 0) {
            setVehicles(data);
          }
        })
        .catch(() => {}); // Silently ignore if API not ready yet
    }
  }, [isUsingMock, drivers]);

  // Trip simulation state
  const [simForm, setSimForm] = useState({
    driver_id: '',
    vehicle_id: '',
    vehicle_type: 'Mini Truck',
    route_type: 'Mixed',
    distance_km: 120,
    duration_min: 90,
    avg_speed_kmh: 80,
    max_speed_kmh: 110,
    num_stops: 3,
    avg_engine_rpm: 1800,
    accel_events: 2,
    brake_events: 3,
    over_speed_count: 1,
    cornering_events: 1,
    idle_time_min: 8.5,
    actual_fuel_used_l: 15.2,
    battery_voltage: 14.1,
    coolant_temp: 85.0
  });

  const [simInterval, setSimInterval] = useState(10); // seconds
  const [isSimRunning, setIsSimRunning] = useState(false);

  // New Driver state
  const [newDriver, setNewDriver] = useState({
    driver_id: '',
    name: '',
    vehicle_type: 'Mini Truck',
    vehicle_id: '',
    is_active: true
  });

  // New Vehicle state
  const [newVehicle, setNewVehicle] = useState({
    vehicle_id: '',
    reg_no: '',
    vehicle_name: '',
    vehicle_type: 'Mini Truck',
    make: '',
    model: '',
    is_active: true,
    brake_life: 50000,
    engine_life: 10000,
    tire_life: 80000,
    battery_life: 5000,
    clutch_life: 60000
  });

  // Sync default driver and vehicle selection when drivers list or vehicles list changes
  useEffect(() => {
    if (drivers && drivers.length > 0) {
      const defaultDriver = drivers[0];
      const defaultVehicleId = defaultDriver.vehicle_id || (vehicles.length > 0 ? vehicles[0].vehicle_id : '');
      setSimForm(prev => ({
        ...prev,
        driver_id: prev.driver_id || defaultDriver.driver_id,
        vehicle_id: prev.vehicle_id || defaultVehicleId
      }));
    }
  }, [drivers, vehicles]);

  // Set default sequential Driver ID when opening Driver tab
  useEffect(() => {
    if (activeTab === 'driver' && drivers) {
      const nextNum = drivers.length + 1;
      const paddedNum = nextNum.toString().padStart(3, '0');
      const defaultVehicleId = vehicles.length > 0 ? vehicles[0].vehicle_id : `VH${paddedNum}`;
      setNewDriver(prev => ({
        ...prev,
        driver_id: `DR${paddedNum}`,
        vehicle_id: defaultVehicleId
      }));
    }
  }, [activeTab, drivers, vehicles]);

  // Set default Vehicle ID when opening Vehicle tab
  useEffect(() => {
    if (activeTab === 'vehicle') {
      const nextNum = vehicles.length + 1;
      const paddedNum = nextNum.toString().padStart(3, '0');
      setNewVehicle(prev => ({
        ...prev,
        vehicle_id: `VH${paddedNum}`
      }));
    }
  }, [activeTab, vehicles]);

  // Live streaming effect (matches existing App.jsx live stream logic)
  useEffect(() => {
    let intervalId = null;
    if (isSimRunning) {
      setSimStatusMsg(`Streaming active (Interval: ${simInterval}s)...`);
      setSimLogs(prev => [
        `[${new Date().toLocaleTimeString()}] 🚀 Automated Telemetry Streaming started.`,
        ...prev
      ].slice(0, 20));
      
      intervalId = setInterval(async () => {
        if (drivers.length === 0) return;
        const randomDriver = drivers[Math.floor(Math.random() * drivers.length)];
        const routeTypes = ['Mixed', 'Highway', 'City', 'Mountain', 'Rural'];
        const randomRoute = routeTypes[Math.floor(Math.random() * routeTypes.length)];
        
        const distance = parseFloat((30 + Math.random() * 250).toFixed(1));
        const duration = parseFloat((distance * 0.8 + Math.random() * 30).toFixed(1));
        const accel = Math.floor(Math.random() * 5);
        const brake = Math.floor(Math.random() * 6);
        const speeding = Math.floor(Math.random() * 3);
        const cornering = Math.floor(Math.random() * 4);
        const idle = parseFloat((2 + Math.random() * 10).toFixed(1));
        const actualFuel = parseFloat((distance * 0.14 + Math.random() * 3).toFixed(1));
        const battery = parseFloat((11.2 + Math.random() * 3).toFixed(1));
        const coolant = parseFloat((78 + Math.random() * 28).toFixed(1));

        const timestampStr = new Date().toLocaleTimeString();

        const newTripData = {
          driver_id: randomDriver.driver_id,
          vehicle_id: randomDriver.vehicle_id || `VH0${randomDriver.driver_id.replace('DR', '')}`,
          route_type: randomRoute,
          distance_km: distance,
          duration_min: duration,
          avg_speed_kmh: Math.round(distance / (duration / 60)),
          max_speed_kmh: Math.round(80 + Math.random() * 45),
          num_stops: Math.floor(Math.random() * 6),
          avg_engine_rpm: Math.round(1600 + Math.random() * 500),
          accel_events: accel,
          brake_events: brake,
          over_speed_count: speeding,
          cornering_events: cornering,
          idle_time_min: idle,
          actual_fuel_used_l: actualFuel,
          battery_voltage: battery,
          coolant_temp: coolant
        };

        if (isUsingMock) {
          const computedScore = Math.max(30, Math.min(100, Math.round(
            100 - (accel * 4 + brake * 3.5 + speeding * 9 + cornering * 3.2 + (idle > 10 ? 4 : 0))
          )));
          
          const newTripId = `TR00${Math.floor(9500 + Math.random() * 500)}`;
          const newTrip = {
            journey_id: newTripId,
            start_time: new Date().toLocaleString(),
            route_type: randomRoute,
            distance_km: distance,
            duration_min: duration,
            driver_score: computedScore,
            fuel_theft_detected: Math.random() > 0.82, // 18% chance of mock siphoning
            maintenance_critical: battery < 11.5 || coolant > 100
          };

          if (randomDriver.driver_id === activeDriverId) {
            setJourneys(prev => [newTrip, ...prev]);
            setActiveJourneyId(newTripId);
          }

          setDrivers(prev => prev.map(d => {
            if (d.driver_id === randomDriver.driver_id) {
              const currentTrips = d.total_trips + 1;
              const newAvg = parseFloat(((d.avg_score * d.total_trips + computedScore) / currentTrips).toFixed(1));
              const prevDist = d.total_distance ?? d.total_distance_km ?? 0.0;
              const newDist = parseFloat((prevDist + distance).toFixed(2));
              return {
                ...d,
                total_trips: currentTrips,
                avg_score: newAvg,
                ml_score: newAvg,
                total_distance: newDist,
                total_distance_km: newDist
              };
            }
            return d;
          }));

          setSimLogs(prev => [
            `[${timestampStr}] 📡 [Streaming] Auto-injected trip ${newTripId} for driver ${randomDriver.driver_id}. ML Safety Score: ${computedScore}`,
            ...prev
          ].slice(0, 20));

          if (newTrip.fuel_theft_detected) {
            const mockTheftAlert = {
              alert_id: Math.floor(Math.random() * 10000),
              driver_id: randomDriver.driver_id,
              driver_name: randomDriver.name,
              trip_id: newTripId,
              vehicle_id: randomDriver.vehicle_id,
              event_time: new Date().toLocaleString(),
              theft_type: 'RUNNING_THEFT',
              theft_amount_liters: 11.5,
              fuel_diff_liters: -11.5,
              speed_kmh: 42,
              gps_lat: 22.312,
              gps_lng: 70.805,
              message: `Fuel Theft Alert! ${randomDriver.name} siphoned 11.5L on the route.`
            };
            setFuelAlerts(prev => [mockTheftAlert, ...prev]);
            setShowAlertToast(true);
            setSimLogs(prev => [`[${timestampStr}] 🚨 [Streaming Alert] Fuel Theft siphoning detected!`, ...prev].slice(0, 20));
          }
        } else {
          try {
            const response = await fetch('/api/simulation/inject-trip', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify(newTripData)
            });
            if (response.ok) {
              setSimLogs(prev => [`[${timestampStr}] 📡 [Streaming] Injected live packet for driver ${randomDriver.driver_id} directly into DB.`, ...prev].slice(0, 20));
              
              if (randomDriver.driver_id === activeDriverId) {
                const current = activeDriverId;
                setActiveDriverId(null);
                setTimeout(() => setActiveDriverId(current), 100);
              }
              
              const res = await fetch('/api/drivers/');
              if (res.ok) {
                const data = await res.json();
                setDrivers(data.map(d => ({
                  ...d,
                  name: d.driver_name || d.name || `Driver ${d.driver_id}`,
                  avatar_color: getDriverColor(d.driver_id),
                  vehicle_type: d.vehicle_type || "Mini Truck",
                  vehicle_id: d.vehicle_id || `VH0${d.driver_id.replace('DR', '')}`
                })));
              }
            } else {
              setSimLogs(prev => [`[${timestampStr}] ⚠️ [Streaming Alert] API error: response code ${response.status}`, ...prev].slice(0, 20));
            }
          } catch (_) {
            setSimLogs(prev => [`[${timestampStr}] ⚠️ [Streaming Alert] Connection failed to simulator intake.`, ...prev].slice(0, 20));
          }
        }
      }, simInterval * 1000);
    } else {
      setSimStatusMsg('');
    }

    return () => {
      if (intervalId) clearInterval(intervalId);
    };
  }, [isSimRunning, simInterval, isUsingMock, activeDriverId, drivers]);

  if (!isOpen) return null;

  // Handler for adding manually injected trip
  const handleInjectTrip = async (e) => {
    if (e) e.preventDefault();
    setIsSimSubmitting(true);
    setSimStatusMsg('Injecting telemetry event...');
    
    const timestampStr = new Date().toLocaleTimeString();

    if (isUsingMock) {
      setTimeout(() => {
        // Calculate ML Score for the mock trip
        const computedScore = Math.max(30, Math.min(100, Math.round(
          100 - (
            simForm.accel_events * 3.5 +
            simForm.brake_events * 4.2 +
            simForm.over_speed_count * 8.5 +
            simForm.cornering_events * 2.8 +
            (simForm.idle_time_min > 15 ? 5 : 0)
          )
        )));
        
        const newTripId = `TR00${Math.floor(9500 + Math.random() * 500)}`;
        const newTrip = {
          journey_id: newTripId,
          start_time: new Date().toLocaleString(),
          route_type: simForm.route_type,
          distance_km: parseFloat(simForm.distance_km),
          duration_min: parseFloat(simForm.duration_min),
          driver_score: computedScore,
          fuel_theft_detected: simForm.actual_fuel_used_l > (simForm.distance_km * 0.25), // Mock theft logic
          maintenance_critical: simForm.battery_voltage < 11.5 || simForm.coolant_temp > 100
        };

        if (simForm.driver_id === activeDriverId) {
          setJourneys(prev => [newTrip, ...prev]);
          setActiveJourneyId(newTripId);
        }

        setDrivers(prev => prev.map(d => {
          if (d.driver_id === simForm.driver_id) {
            const currentTrips = d.total_trips + 1;
            const newAvg = parseFloat(((d.avg_score * d.total_trips + computedScore) / currentTrips).toFixed(1));
            const prevDist = d.total_distance ?? d.total_distance_km ?? 0.0;
            const newDist = parseFloat((prevDist + parseFloat(simForm.distance_km)).toFixed(2));
            return {
              ...d,
              total_trips: currentTrips,
              avg_score: newAvg,
              ml_score: newAvg,
              total_distance: newDist,
              total_distance_km: newDist
            };
          }
          return d;
        }));

        setSimLogs(prev => [
          `[${timestampStr}] 📥 Manually injected trip ${newTripId} for driver ${simForm.driver_id}. ML Safety Score: ${computedScore}`,
          ...prev
        ].slice(0, 20));

        if (newTrip.fuel_theft_detected) {
          const mockTheftAlert = {
            alert_id: Math.floor(Math.random() * 10000),
            driver_id: simForm.driver_id,
            driver_name: drivers.find(d => d.driver_id === simForm.driver_id)?.name || 'Driver',
            trip_id: newTripId,
            vehicle_id: simForm.vehicle_id,
            event_time: new Date().toLocaleString(),
            theft_type: 'IGNITION_OFF_DROP',
            theft_amount_liters: 14.5,
            fuel_diff_liters: -14.5,
            speed_kmh: 0,
            gps_lat: 22.30715,
            gps_lng: 70.8007,
            message: `Fuel Theft Alert! ${simForm.driver_id} siphoned 14.5L at rest.`
          };
          setFuelAlerts(prev => [mockTheftAlert, ...prev]);
          setShowAlertToast(true);
          setSimLogs(prev => [`[${timestampStr}] 🚨 Live Alert generated: Fuel Theft detected!`, ...prev].slice(0, 20));
        }

        setIsSimSubmitting(false);
        setSimStatusMsg('✓ Trip injected successfully! (In-Memory)');
        setTimeout(() => setSimStatusMsg(''), 3000);
      }, 800);
    } else {
      try {
        const response = await fetch('/api/simulation/inject-trip', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(simForm)
        });
        if (response.ok) {
          setSimStatusMsg('✓ Trip injected into database!');
          setSimLogs(prev => [`[${timestampStr}] 📡 Database update triggered. Trip injected into SQL Server!`, ...prev].slice(0, 20));
          
          if (simForm.driver_id === activeDriverId) {
            const currentDriver = activeDriverId;
            setActiveDriverId(null);
            setTimeout(() => setActiveDriverId(currentDriver), 100);
          }
          
          const res = await fetch('/api/drivers/');
          if (res.ok) {
            const data = await res.json();
            setDrivers(data.map(d => ({
              ...d,
              name: d.driver_name || d.name || `Driver ${d.driver_id}`,
              avatar_color: getDriverColor(d.driver_id),
              vehicle_type: d.vehicle_type || "Mini Truck",
              vehicle_id: d.vehicle_id || `VH0${d.driver_id.replace('DR', '')}`
            })));
          }
          
          setTimeout(() => setSimStatusMsg(''), 3000);
        } else {
          setSimStatusMsg('✗ Failed to insert telemetry. Check API config.');
          setSimLogs(prev => [`[${timestampStr}] ❌ Backend error: Failed to save trip. API returned status ${response.status}`, ...prev].slice(0, 20));
        }
      } catch (err) {
        setSimStatusMsg('✗ API offline. Backend simulation route not ready.');
        setSimLogs(prev => [`[${timestampStr}] ⚠️ Backend connection failed. Add API route '/api/simulation/inject-trip' first.`, ...prev].slice(0, 20));
      } finally {
        setIsSimSubmitting(false);
      }
    }
  };

  // Handler for adding driver manually
  const handleAddDriver = async (e) => {
    e.preventDefault();
    if (!newDriver.name) {
      alert('Please enter driver name');
      return;
    }

    setIsSimSubmitting(true);
    setSimStatusMsg('Registering driver...');
    const timestampStr = new Date().toLocaleTimeString();

    if (isUsingMock) {
      // In-memory mock path (unchanged)
      setTimeout(() => {
        const driverId = newDriver.driver_id || `DR${(drivers.length + 1).toString().padStart(3, '0')}`;
        const driverObj = {
          driver_id: driverId,
          name: newDriver.name,
          driver_name: newDriver.name,
          vehicle_type: 'Mini Truck',
          vehicle_id: `VH0${driverId.replace('DR', '')}`,
          total_trips: 0,
          total_distance: 0,
          total_distance_km: 0,
          avg_speed_kmh: 0,
          avatar_color: getDriverColor(driverId),
          avg_score: 100.0,
          ml_score: 100.0,
          rule_based_score: 100.0,
          total_odometer_km: 0,
          engine_total_hours: 0,
          is_active: newDriver.is_active
        };
        setDrivers(prev => [...prev, driverObj]);
        setSimLogs(prev => [
          `[${timestampStr}] 👤 [Mock] Added Driver: ${newDriver.name} (${driverId}).`,
          ...prev
        ].slice(0, 20));
        setIsSimSubmitting(false);
        setSimStatusMsg('✓ Driver added (In-Memory)!');
        setNewDriver({ driver_id: '', name: '', vehicle_type: 'Mini Truck', vehicle_id: '', is_active: true });
        setTimeout(() => setSimStatusMsg(''), 3000);
      }, 600);
    } else {
      // Live DB path
      try {
        const response = await fetch('/api/simulation/add-driver', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            driver_id: newDriver.driver_id,
            name: newDriver.name,
            is_active: newDriver.is_active
          })
        });
        const data = await response.json();
        if (response.ok) {
          setSimLogs(prev => [
            `[${timestampStr}] 👤 [DB] Registered Driver: ${newDriver.name} (${newDriver.driver_id}).`,
            ...prev
          ].slice(0, 20));
          setSimStatusMsg('✓ Driver registered in Database!');
          setNewDriver({ driver_id: '', name: '', vehicle_type: 'Mini Truck', vehicle_id: '', is_active: true });
          // Refresh drivers list from DB
          const res = await fetch('/api/drivers/');
          if (res.ok) {
            const driverData = await res.json();
            setDrivers(driverData.map(d => ({
              ...d,
              name: d.driver_name || d.name || `Driver ${d.driver_id}`,
              avatar_color: getDriverColor(d.driver_id),
              vehicle_type: d.vehicle_type || 'Mini Truck',
              vehicle_id: d.vehicle_id || `VH0${d.driver_id.replace('DR', '')}`,
              total_distance_km: d.total_distance_km ?? d.total_distance ?? 0.0
            })));
          }
        } else if (response.status === 409) {
          setSimStatusMsg(`✗ Driver ID '${newDriver.driver_id}' already exists.`);
          setSimLogs(prev => [`[${timestampStr}] ⚠️ Driver ID conflict: ${data.detail}`, ...prev].slice(0, 20));
        } else {
          setSimStatusMsg('✗ Failed to register driver.');
          setSimLogs(prev => [`[${timestampStr}] ❌ API error: ${data.detail || response.status}`, ...prev].slice(0, 20));
        }
      } catch (err) {
        setSimStatusMsg('✗ API offline. Check backend connection.');
        setSimLogs(prev => [`[${timestampStr}] ⚠️ Backend connection failed.`, ...prev].slice(0, 20));
      } finally {
        setIsSimSubmitting(false);
        setTimeout(() => setSimStatusMsg(''), 4000);
      }
    }
  };

  // Handler for adding vehicle
  const handleAddVehicle = async (e) => {
    e.preventDefault();
    if (!newVehicle.vehicle_id || !newVehicle.reg_no) {
      alert('Please fill in Vehicle ID and Registration Number');
      return;
    }

    setIsSimSubmitting(true);
    setSimStatusMsg('Registering vehicle...');
    const timestampStr = new Date().toLocaleTimeString();

    if (isUsingMock) {
      // In-memory mock path (unchanged)
      setTimeout(() => {
        const vehicleObj = {
          vehicle_id: newVehicle.vehicle_id,
          reg_no: newVehicle.reg_no,
          vehicle_name: newVehicle.vehicle_name || `${newVehicle.make} ${newVehicle.model}`,
          vehicle_type: newVehicle.vehicle_type,
          make: newVehicle.make || 'Tata',
          model: newVehicle.model || '2024',
          is_active: newVehicle.is_active
        };
        setVehicles(prev => [...prev, vehicleObj]);
        setSimLogs(prev => [
          `[${timestampStr}] 🚚 [Mock] Registered Vehicle: ${vehicleObj.vehicle_name} [${vehicleObj.vehicle_id}] (In-Memory)`,
          ...prev
        ].slice(0, 20));
        setIsSimSubmitting(false);
        setSimStatusMsg('✓ Vehicle registered (In-Memory)!');
        setNewVehicle({ vehicle_id: '', reg_no: '', vehicle_name: '', vehicle_type: 'Mini Truck', make: '', model: '', is_active: true, brake_life: 50000, engine_life: 10000, tire_life: 80000, battery_life: 5000, clutch_life: 60000 });
        setTimeout(() => setSimStatusMsg(''), 3000);
      }, 600);
    } else {
      // Live DB path
      try {
        const response = await fetch('/api/simulation/add-vehicle', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            vehicle_id:   newVehicle.vehicle_id,
            reg_no:       newVehicle.reg_no,
            vehicle_name: newVehicle.vehicle_name || '',
            vehicle_type: newVehicle.vehicle_type,
            make:         newVehicle.make || '',
            model:        newVehicle.model || '',
            is_active:    newVehicle.is_active,
            brake_life:   Number(newVehicle.brake_life),
            engine_life:  Number(newVehicle.engine_life),
            tire_life:    Number(newVehicle.tire_life),
            battery_life: Number(newVehicle.battery_life),
            clutch_life:  Number(newVehicle.clutch_life)
          })
        });
        const data = await response.json();
        if (response.ok) {
          setSimLogs(prev => [
            `[${timestampStr}] 🚚 [DB] Registered Vehicle: ${newVehicle.vehicle_id} [${newVehicle.reg_no}] Type: ${newVehicle.vehicle_type}`,
            ...prev
          ].slice(0, 20));
          setSimStatusMsg('✓ Vehicle registered in Database!');
          setNewVehicle({ vehicle_id: '', reg_no: '', vehicle_name: '', vehicle_type: 'Mini Truck', make: '', model: '', is_active: true, brake_life: 50000, engine_life: 10000, tire_life: 80000, battery_life: 5000, clutch_life: 60000 });
          // Refresh vehicles list from DB
          const res = await fetch('/api/simulation/vehicles');
          if (res.ok) setVehicles(await res.json());
        } else if (response.status === 409) {
          setSimStatusMsg(`✗ Vehicle ID '${newVehicle.vehicle_id}' already exists.`);
          setSimLogs(prev => [`[${timestampStr}] ⚠️ Vehicle ID conflict: ${data.detail}`, ...prev].slice(0, 20));
        } else {
          setSimStatusMsg('✗ Failed to register vehicle.');
          setSimLogs(prev => [`[${timestampStr}] ❌ API error: ${data.detail || response.status}`, ...prev].slice(0, 20));
        }
      } catch (err) {
        setSimStatusMsg('✗ API offline. Check backend connection.');
        setSimLogs(prev => [`[${timestampStr}] ⚠️ Backend connection failed.`, ...prev].slice(0, 20));
      } finally {
        setIsSimSubmitting(false);
        setTimeout(() => setSimStatusMsg(''), 4000);
      }
    }
  };

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-md z-50 flex items-center justify-center p-4 transition-all">
      <div className="bg-white rounded-[32px] border border-slate-200/80 shadow-2xl w-full max-w-6xl h-[85vh] flex flex-col overflow-hidden animate-fade-in">

        {/* Modal Header */}
        <div className="px-6 py-5 bg-slate-50 border-b border-slate-200/80 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-violet-600 text-white rounded-2xl shadow-brand-glow">
              <Activity className="w-6 h-6 animate-pulse" />
            </div>
            <div>
              <h2 className="text-lg font-black font-outfit text-slate-900 tracking-tight flex items-center gap-2">
                Simulator & Manual Inputs Control
              </h2>
              <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider">
                Simulate FMC650 OBD packets and manage drivers/vehicles metadata
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-slate-200/60 hover:bg-slate-200 flex items-center justify-center text-slate-500 hover:text-slate-700 transition-colors border-0 outline-none cursor-pointer"
          >
            <span className="font-extrabold text-sm">✕</span>
          </button>
        </div>

        {/* Workspace Layout */}
        <div className="flex-1 flex overflow-hidden min-h-0">
          
          {/* Navigation Bar (Left Sidebar / Tab bar) */}
          <div className="w-64 bg-slate-50/50 border-r border-slate-100 flex flex-col p-4 space-y-2 shrink-0">
            <span className="text-[10px] font-black uppercase text-slate-400 tracking-widest px-3 mb-2 block">
              Simulation Actions
            </span>

            {/* Tab: Trip/Telemetry */}
            <button
              onClick={() => setActiveTab('trip')}
              className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl text-xs font-bold transition-all border-0 outline-none cursor-pointer text-left
                ${activeTab === 'trip'
                  ? 'bg-violet-600 text-white shadow-premium-sm font-black'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-800'}`}
            >
              <Activity className="w-4 h-4" />
              <span>1. Trip & Telemetry</span>
            </button>

            {/* Tab: Add Driver */}
            <button
              onClick={() => setActiveTab('driver')}
              className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl text-xs font-bold transition-all border-0 outline-none cursor-pointer text-left
                ${activeTab === 'driver'
                  ? 'bg-violet-600 text-white shadow-premium-sm font-black'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-800'}`}
            >
              <UserPlus className="w-4 h-4" />
              <span>2. Register Driver</span>
            </button>

            {/* Tab: Add Vehicle */}
            <button
              onClick={() => setActiveTab('vehicle')}
              className={`w-full flex items-center gap-3 px-4 py-3.5 rounded-2xl text-xs font-bold transition-all border-0 outline-none cursor-pointer text-left
                ${activeTab === 'vehicle'
                  ? 'bg-violet-600 text-white shadow-premium-sm font-black'
                  : 'text-slate-600 hover:bg-slate-100 hover:text-slate-800'}`}
            >
              <Truck className="w-4 h-4" />
              <span>3. Add Vehicle</span>
            </button>



            <div className="flex-1" />

            {/* Active Status Badge */}
            <div className="p-4 bg-slate-100/80 rounded-2xl border border-slate-200/40">
              <span className="text-[10px] font-extrabold uppercase text-slate-400 tracking-wider block mb-1">Status Panel</span>
              <div className="flex items-center gap-2">
                <span className={`w-2.5 h-2.5 rounded-full ${isSimRunning ? 'bg-emerald-500 animate-pulse' : 'bg-slate-400'}`} />
                <span className="text-xs font-bold text-slate-700">
                  {isSimRunning ? 'Live Stream Active' : 'Idle Mode'}
                </span>
              </div>
            </div>
          </div>

          {/* Form Content Area (Right side) */}
          <div className="flex-1 overflow-y-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 min-h-0">
            
            {/* Left side of workspace: The active form (Trip, Driver, or Vehicle) */}
            <div className="lg:col-span-7 flex flex-col justify-between">
              
              {/* Render Tab: TRIP SIMULATION FORM */}
              {activeTab === 'trip' && (
                <form onSubmit={handleInjectTrip} className="flex flex-col justify-between h-full space-y-4">
                  <div className="space-y-4 overflow-y-auto pr-1" style={{ maxHeight: 'calc(85vh - 220px)' }}>
                    <h3 className="text-sm font-extrabold text-slate-800 uppercase tracking-wider font-outfit border-b border-slate-100 pb-2 flex items-center gap-2">
                      <Activity className="w-4 h-4 text-violet-500" />
                      1. Manual Trip Telemetry Injector
                    </h3>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Driver Context (Select Driver)</label>
                        <select
                          value={simForm.driver_id}
                          onChange={e => {
                            const dId = e.target.value;
                            setSimForm(prev => ({
                              ...prev,
                              driver_id: dId
                            }));
                          }}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        >
                          {drivers.map(d => (
                            <option key={d.driver_id} value={d.driver_id}>
                              {d.name} ({d.driver_id})
                            </option>
                          ))}
                        </select>
                      </div>
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Vehicle Context (Select Vehicle)</label>
                        <select
                          value={simForm.vehicle_id}
                          onChange={e => {
                            const vId = e.target.value;
                            const selectedVeh = vehicles.find(v => v.vehicle_id === vId);
                            setSimForm(prev => ({
                              ...prev,
                              vehicle_id: vId,
                              vehicle_type: selectedVeh ? selectedVeh.vehicle_type : prev.vehicle_type
                            }));
                          }}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        >
                          {vehicles.map(v => (
                            <option key={v.vehicle_id} value={v.vehicle_id}>
                              {v.vehicle_name || v.vehicle_id} ({v.vehicle_id})
                            </option>
                          ))}
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Route Type</label>
                        <select
                          value={simForm.route_type}
                          onChange={e => setSimForm(prev => ({ ...prev, route_type: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                        >
                          <option value="Mixed">Mixed</option>
                          <option value="Highway">Highway</option>
                          <option value="City">City</option>
                          <option value="Mountain">Mountain</option>
                          <option value="Rural">Rural</option>
                        </select>
                      </div>
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Distance (km)</label>
                        <input
                          type="number"
                          step="0.1"
                          value={simForm.distance_km}
                          onChange={e => setSimForm(prev => ({ ...prev, distance_km: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Duration (mins)</label>
                        <input
                          type="number"
                          value={simForm.duration_min}
                          onChange={e => setSimForm(prev => ({ ...prev, duration_min: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-4 gap-4">
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Avg Speed</label>
                        <input
                          type="number"
                          value={simForm.avg_speed_kmh}
                          onChange={e => setSimForm(prev => ({ ...prev, avg_speed_kmh: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Max Speed</label>
                        <input
                          type="number"
                          value={simForm.max_speed_kmh}
                          onChange={e => setSimForm(prev => ({ ...prev, max_speed_kmh: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Stops Count</label>
                        <input
                          type="number"
                          value={simForm.num_stops}
                          onChange={e => setSimForm(prev => ({ ...prev, num_stops: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Avg Engine RPM</label>
                        <input
                          type="number"
                          value={simForm.avg_engine_rpm}
                          onChange={e => setSimForm(prev => ({ ...prev, avg_engine_rpm: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-5 gap-3">
                      <div>
                        <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1.5" title="Harsh Acceleration Events">Harsh Accel</label>
                        <input
                          type="number"
                          value={simForm.accel_events}
                          onChange={e => setSimForm(prev => ({ ...prev, accel_events: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-2.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1.5" title="Harsh Braking Events">Harsh Brake</label>
                        <input
                          type="number"
                          value={simForm.brake_events}
                          onChange={e => setSimForm(prev => ({ ...prev, brake_events: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-2.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1.5" title="Overspeeding Events">Overspeed</label>
                        <input
                          type="number"
                          value={simForm.over_speed_count}
                          onChange={e => setSimForm(prev => ({ ...prev, over_speed_count: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-2.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1.5" title="Harsh Cornering Events">Cornering</label>
                        <input
                          type="number"
                          value={simForm.cornering_events}
                          onChange={e => setSimForm(prev => ({ ...prev, cornering_events: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-2.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1.5" title="Total Engine Idling duration (minutes)">Idle Mins</label>
                        <input
                          type="number"
                          step="0.1"
                          value={simForm.idle_time_min}
                          onChange={e => setSimForm(prev => ({ ...prev, idle_time_min: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-2.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Actual Fuel Used (L)</label>
                        <input
                          type="number"
                          step="0.1"
                          value={simForm.actual_fuel_used_l}
                          onChange={e => setSimForm(prev => ({ ...prev, actual_fuel_used_l: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Battery Voltage (V)</label>
                        <input
                          type="number"
                          step="0.1"
                          value={simForm.battery_voltage}
                          onChange={e => setSimForm(prev => ({ ...prev, battery_voltage: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        />
                      </div>
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Coolant Temp (°C)</label>
                        <input
                          type="number"
                          step="0.1"
                          value={simForm.coolant_temp}
                          onChange={e => setSimForm(prev => ({ ...prev, coolant_temp: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          required
                        />
                      </div>
                    </div>
                  </div>

                  {/* Form actions */}
                  <div className="pt-4 flex items-center justify-between border-t border-slate-100 shrink-0">
                    <div className="text-xs font-medium">
                      {simStatusMsg && (
                        <span className={`font-bold transition-all animate-pulse ${simStatusMsg.includes('✓') ? 'text-emerald-600' : simStatusMsg.includes('✗') ? 'text-rose-600' : 'text-violet-600'}`}>
                          {simStatusMsg}
                        </span>
                      )}
                    </div>
                    <button
                      type="submit"
                      disabled={isSimSubmitting}
                      className="px-6 py-3 bg-violet-600 hover:bg-violet-700 active:scale-95 text-white text-xs font-bold font-outfit rounded-xl transition-all cursor-pointer shadow-premium-sm border-0 outline-none flex items-center gap-2 disabled:opacity-50"
                    >
                      {isSimSubmitting ? 'Injecting...' : 'Inject Telemetry Trip'}
                    </button>
                  </div>
                </form>
              )}

              {/* Render Tab: REGISTER DRIVER FORM */}
              {activeTab === 'driver' && (
                <form onSubmit={handleAddDriver} className="flex flex-col justify-between h-full space-y-4">
                  <div className="space-y-4 overflow-y-auto pr-1" style={{ maxHeight: 'calc(85vh - 220px)' }}>
                    <h3 className="text-sm font-extrabold text-slate-800 uppercase tracking-wider font-outfit border-b border-slate-100 pb-2 flex items-center gap-2">
                      <UserPlus className="w-4 h-4 text-violet-500" />
                      2. Add / Register New Driver
                    </h3>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Driver ID (Code)</label>
                        <input
                          type="text"
                          value={newDriver.driver_id}
                          onChange={e => setNewDriver(prev => ({ ...prev, driver_id: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          placeholder="e.g. DR011"
                          required
                        />
                      </div>
                      
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Driver Full Name</label>
                        <input
                          type="text"
                          value={newDriver.name}
                          onChange={e => setNewDriver(prev => ({ ...prev, name: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          placeholder="e.g. Jane Doe"
                          required
                        />
                      </div>
                    </div>



                    <div className="flex items-center gap-2.5 pt-2">
                      <input
                        type="checkbox"
                        id="driver_active"
                        checked={newDriver.is_active}
                        onChange={e => setNewDriver(prev => ({ ...prev, is_active: e.target.checked }))}
                        className="w-4.5 h-4.5 accent-violet-600 rounded cursor-pointer"
                      />
                      <label htmlFor="driver_active" className="text-xs font-bold text-slate-600 select-none cursor-pointer">
                        Mark Driver as Active (Ready to receive trips)
                      </label>
                    </div>
                  </div>

                  {/* Form actions */}
                  <div className="pt-4 flex items-center justify-between border-t border-slate-100 shrink-0">
                    <div className="text-xs font-medium">
                      {simStatusMsg && (
                        <span className={`font-bold transition-all animate-pulse ${simStatusMsg.includes('✓') ? 'text-emerald-600' : simStatusMsg.includes('✗') ? 'text-rose-600' : 'text-violet-600'}`}>
                          {simStatusMsg}
                        </span>
                      )}
                    </div>
                    <button
                      type="submit"
                      disabled={isSimSubmitting}
                      className="px-6 py-3 bg-violet-600 hover:bg-violet-700 active:scale-95 text-white text-xs font-bold font-outfit rounded-xl transition-all cursor-pointer shadow-premium-sm border-0 outline-none flex items-center gap-2 disabled:opacity-50"
                    >
                      {isSimSubmitting ? 'Creating...' : 'Register Driver'}
                    </button>
                  </div>
                </form>
              )}

              {/* Render Tab: ADD VEHICLE FORM */}
              {activeTab === 'vehicle' && (
                <form onSubmit={handleAddVehicle} className="flex flex-col justify-between h-full space-y-4">
                  <div className="space-y-4 overflow-y-auto pr-1" style={{ maxHeight: 'calc(85vh - 220px)' }}>
                    <h3 className="text-sm font-extrabold text-slate-800 uppercase tracking-wider font-outfit border-b border-slate-100 pb-2 flex items-center gap-2">
                      <Truck className="w-4 h-4 text-violet-500" />
                      3. Add New Fleet Vehicle
                    </h3>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Vehicle ID (Code)</label>
                        <input
                          type="text"
                          value={newVehicle.vehicle_id}
                          onChange={e => setNewVehicle(prev => ({ ...prev, vehicle_id: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          placeholder="e.g. VH011"
                          required
                        />
                      </div>
                      
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Registration Number</label>
                        <input
                          type="text"
                          value={newVehicle.reg_no}
                          onChange={e => setNewVehicle(prev => ({ ...prev, reg_no: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          placeholder="e.g. GJ-01-XX-1234"
                          required
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Vehicle Model Name</label>
                        <input
                          type="text"
                          value={newVehicle.vehicle_name}
                          onChange={e => setNewVehicle(prev => ({ ...prev, vehicle_name: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          placeholder="e.g. Volvo FMX 460"
                        />
                      </div>

                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Vehicle Category Type</label>
                        <select
                          value={newVehicle.vehicle_type}
                          onChange={e => setNewVehicle(prev => ({ ...prev, vehicle_type: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                        >
                          <option value="Mini Truck">Mini Truck</option>
                          <option value="Medium Cargo">Medium Cargo</option>
                          <option value="Heavy Cargo Truck">Heavy Cargo Truck</option>
                          <option value="Pickup Truck">Pickup Truck</option>
                        </select>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Make / Manufacturer</label>
                        <input
                          type="text"
                          value={newVehicle.make}
                          onChange={e => setNewVehicle(prev => ({ ...prev, make: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          placeholder="e.g. Volvo"
                        />
                      </div>

                      <div>
                        <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">Model Year / Specs</label>
                        <input
                          type="text"
                          value={newVehicle.model}
                          onChange={e => setNewVehicle(prev => ({ ...prev, model: e.target.value }))}
                          className="w-full rounded-xl border border-slate-200 px-3.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                          placeholder="e.g. 2024 V2"
                        />
                      </div>
                    </div>

                    <div className="pt-2 border-t border-slate-100">
                      <h4 className="text-[10px] font-extrabold text-slate-800 uppercase tracking-wider mb-3">Maintenance Baseline</h4>
                      <div className="grid grid-cols-5 gap-3">
                        <div>
                          <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1.5" title="Brake Base Life (km)">Brake (km)</label>
                          <input
                            type="number"
                            value={newVehicle.brake_life}
                            onChange={e => setNewVehicle(prev => ({ ...prev, brake_life: e.target.value }))}
                            className="w-full rounded-xl border border-slate-200 px-2.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1.5" title="Engine Base Life (hours)">Engine (hrs)</label>
                          <input
                            type="number"
                            value={newVehicle.engine_life}
                            onChange={e => setNewVehicle(prev => ({ ...prev, engine_life: e.target.value }))}
                            className="w-full rounded-xl border border-slate-200 px-2.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1.5" title="Tire Base Life (km)">Tire (km)</label>
                          <input
                            type="number"
                            value={newVehicle.tire_life}
                            onChange={e => setNewVehicle(prev => ({ ...prev, tire_life: e.target.value }))}
                            className="w-full rounded-xl border border-slate-200 px-2.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1.5" title="Battery Base Life (cycles)">Battery (cyc)</label>
                          <input
                            type="number"
                            value={newVehicle.battery_life}
                            onChange={e => setNewVehicle(prev => ({ ...prev, battery_life: e.target.value }))}
                            className="w-full rounded-xl border border-slate-200 px-2.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                            required
                          />
                        </div>
                        <div>
                          <label className="block text-[9px] font-bold text-slate-400 uppercase tracking-wider mb-1.5" title="Clutch Base Life (km)">Clutch (km)</label>
                          <input
                            type="number"
                            value={newVehicle.clutch_life}
                            onChange={e => setNewVehicle(prev => ({ ...prev, clutch_life: e.target.value }))}
                            className="w-full rounded-xl border border-slate-200 px-2.5 py-2 text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-violet-500 bg-slate-50/50"
                            required
                          />
                        </div>
                      </div>
                    </div>

                    <div className="flex items-center gap-2.5 pt-2">
                      <input
                        type="checkbox"
                        id="vehicle_active"
                        checked={newVehicle.is_active}
                        onChange={e => setNewVehicle(prev => ({ ...prev, is_active: e.target.checked }))}
                        className="w-4.5 h-4.5 accent-violet-600 rounded cursor-pointer"
                      />
                      <label htmlFor="vehicle_active" className="text-xs font-bold text-slate-600 select-none cursor-pointer">
                        Mark Vehicle as Active in Fleet List
                      </label>
                    </div>
                  </div>

                  {/* Form actions */}
                  <div className="pt-4 flex items-center justify-between border-t border-slate-100 shrink-0">
                    <div className="text-xs font-medium">
                      {simStatusMsg && (
                        <span className={`font-bold transition-all animate-pulse ${simStatusMsg.includes('✓') ? 'text-emerald-600' : simStatusMsg.includes('✗') ? 'text-rose-600' : 'text-violet-600'}`}>
                          {simStatusMsg}
                        </span>
                      )}
                    </div>
                    <button
                      type="submit"
                      disabled={isSimSubmitting}
                      className="px-6 py-3 bg-violet-600 hover:bg-violet-700 active:scale-95 text-white text-xs font-bold font-outfit rounded-xl transition-all cursor-pointer shadow-premium-sm border-0 outline-none flex items-center gap-2 disabled:opacity-50"
                    >
                      {isSimSubmitting ? 'Registering...' : 'Add Vehicle'}
                    </button>
                  </div>
                </form>
              )}

            </div>

            {/* Right Column: Console Logs & Streaming Controls (lg:col-span-5) */}
            <div className="lg:col-span-5 border-l border-slate-100 lg:pl-6 flex flex-col justify-between space-y-4">
              <div className="space-y-4">
                <h3 className="text-sm font-extrabold text-slate-800 uppercase tracking-wider font-outfit border-b border-slate-100 pb-2 flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-violet-500 animate-pulse" />
                  Streaming Feed Controller
                </h3>

                {/* Stream Controller */}
                <div className="bg-slate-50/80 rounded-2xl p-4 border border-slate-200/50 flex flex-col gap-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <span className="text-xs font-bold text-slate-800 block">Streaming Feed Status</span>
                      <span className="text-[10px] text-slate-400 font-semibold uppercase">Simulate continuous OBD packets</span>
                    </div>
                    <button
                      type="button"
                      onClick={() => setIsSimRunning(!isSimRunning)}
                      className={`px-4 py-2 text-xs font-bold font-outfit rounded-xl transition-all border-0 outline-none cursor-pointer active:scale-95 ${isSimRunning 
                        ? 'bg-rose-500 text-white shadow-sm hover:bg-rose-600' 
                        : 'bg-emerald-500 text-white shadow-sm hover:bg-emerald-600'}`}
                    >
                      {isSimRunning ? 'Stop Stream' : 'Start Stream'}
                    </button>
                  </div>

                  <div>
                    <label className="flex items-center justify-between text-[10px] font-bold text-slate-400 uppercase tracking-wide mb-1.5">
                      <span>Packet Interval</span>
                      <span className="text-slate-600 font-extrabold">{simInterval} seconds</span>
                    </label>
                    <input
                      type="range"
                      min="3"
                      max="60"
                      step="1"
                      value={simInterval}
                      onChange={e => setSimInterval(parseInt(e.target.value))}
                      disabled={isSimRunning}
                      className="w-full accent-violet-600 disabled:opacity-50"
                    />
                  </div>
                </div>

                {/* Terminal-like Logs Box */}
                <div className="space-y-1.5">
                  <label className="block text-[10px] font-bold text-slate-400 uppercase tracking-wide">Simulator Console Logs</label>
                  <div className="bg-slate-950 rounded-2xl p-4 font-mono text-[10.5px] text-emerald-400 h-64 overflow-y-auto border border-slate-800 shadow-inner flex flex-col gap-1.5">
                    {simLogs.map((log, index) => (
                      <div key={index} className="leading-relaxed">
                        <span className="text-slate-500 mr-2">›</span>
                        {log}
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Console Action */}
              <div className="pt-4 flex items-center justify-end border-t border-slate-100 shrink-0">
                <button
                  type="button"
                  onClick={() => setSimLogs([`[${new Date().toLocaleTimeString()}] Console logs cleared.`])}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-600 text-xs font-bold font-outfit rounded-xl transition-all cursor-pointer border-0 outline-none shadow-sm"
                >
                  Clear Console
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer */}
        <div className="px-6 py-4 bg-slate-50 border-t border-slate-200/80 flex items-center justify-between shrink-0">
          <div className="text-[10px] text-slate-400 font-bold uppercase tracking-wider flex items-center gap-1.5">
            <Info className="w-3.5 h-3.5 text-slate-400" />
            <span>FMC650 simulator generates dynamic G-force wear markers, battery signals, and fuel telemetry siphoning.</span>
          </div>
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-slate-800 hover:bg-slate-900 active:scale-95 text-white text-xs font-bold font-outfit rounded-xl transition-all cursor-pointer shadow-sm border-0 outline-none"
          >
            Close Control Panel
          </button>
        </div>

      </div>
    </div>
  );
}
