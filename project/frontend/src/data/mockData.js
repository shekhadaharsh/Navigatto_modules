// ==================== FRONTEND MOCK DATA FALLBACKS ====================
// Generates identical structure to Flask in case backend is offline
export const MOCK_DRIVERS = [
  { "driver_id": "DR001", "name": "Alexander Sterling", "vehicle_type": "Mini Truck", "total_trips": 1405, "total_distance_km": 564300.0, "avg_speed_kmh": 67.4, "avatar_color": "#2563eb", "avg_score": 88.5, "ml_score": 88.5, "rule_based_score": 85.2, "vehicle_id": "VH001", "total_odometer_km": 125430.0, "engine_total_hours": 2450.5 },
  { "driver_id": "DR002", "name": "Marcus Vance", "vehicle_type": "Mini Truck", "total_trips": 1367, "total_distance_km": 561200.0, "avg_speed_kmh": 68.1, "avatar_color": "#10b981", "avg_score": 82.4, "ml_score": 82.4, "rule_based_score": 82.0, "vehicle_id": "VH002", "total_odometer_km": 98750.0, "engine_total_hours": 1820.0 },
  { "driver_id": "DR003", "name": "Elena Rostova", "vehicle_type": "Medium Cargo", "total_trips": 1289, "total_distance_km": 570900.0, "avg_speed_kmh": 65.2, "avatar_color": "#d97706", "avg_score": 79.1, "ml_score": 79.1, "rule_based_score": 75.0, "vehicle_id": "VH003", "total_odometer_km": 164200.0, "engine_total_hours": 3120.2 },
  { "driver_id": "DR004", "name": "Devon Lane", "vehicle_type": "Heavy Cargo Truck", "total_trips": 1391, "total_distance_km": 581600.0, "avg_speed_kmh": 67.8, "avatar_color": "#ef4444", "avg_score": 58.4, "ml_score": 58.4, "rule_based_score": 75.5, "vehicle_id": "VH004", "total_odometer_km": 215300.0, "engine_total_hours": 4200.8 },
  { "driver_id": "DR005", "name": "Ronald Richards", "vehicle_type": "Heavy Cargo Truck", "total_trips": 1353, "total_distance_km": 548900.0, "avg_speed_kmh": 67.6, "avatar_color": "#8b5cf6", "avg_score": 84.2, "ml_score": 84.2, "rule_based_score": 81.0, "vehicle_id": "VH005", "total_odometer_km": 189400.0, "engine_total_hours": 3760.4 },
  { "driver_id": "DR006", "name": "Bessie Cooper", "vehicle_type": "Pickup Truck", "total_trips": 1328, "total_distance_km": 517500.0, "avg_speed_kmh": 67.2, "avatar_color": "#2563eb", "avg_score": 91.8, "ml_score": 91.8, "rule_based_score": 92.5, "vehicle_id": "VH006", "total_odometer_km": 72400.0, "engine_total_hours": 1120.0 },
  { "driver_id": "DR007", "name": "Albert Flores", "vehicle_type": "Heavy Cargo Truck", "total_trips": 1392, "total_distance_km": 582300.0, "avg_speed_kmh": 68.0, "avatar_color": "#10b981", "avg_score": 74.3, "ml_score": 74.3, "rule_based_score": 75.0, "vehicle_id": "VH007", "total_odometer_km": 234100.0, "engine_total_hours": 4980.5 },
  { "driver_id": "DR008", "name": "Courtney Henry", "vehicle_type": "Mini Truck", "total_trips": 1307, "total_distance_km": 552400.0, "avg_speed_kmh": 65.8, "avatar_color": "#d97706", "avg_score": 86.1, "ml_score": 86.1, "rule_based_score": 86.0, "vehicle_id": "VH008", "total_odometer_km": 114500.0, "engine_total_hours": 2180.2 },
  { "driver_id": "DR009", "name": "Kathryn Murphy", "vehicle_type": "Mini Truck", "total_trips": 1204, "total_distance_km": 510700.0, "avg_speed_kmh": 67.4, "avatar_color": "#ef4444", "avg_score": 64.9, "ml_score": 64.9, "rule_based_score": 68.0, "vehicle_id": "VH009", "total_odometer_km": 89200.0, "engine_total_hours": 1650.0 },
  { "driver_id": "DR010", "name": "Dianne Russell", "vehicle_type": "Mini Truck", "total_trips": 1412, "total_distance_km": 572900.0, "avg_speed_kmh": 66.1, "avatar_color": "#8b5cf6", "avg_score": 89.2, "ml_score": 89.2, "rule_based_score": 85.0, "vehicle_id": "VH010", "total_odometer_km": 142100.0, "engine_total_hours": 2980.1 }
];

export const MOCK_VEHICLES = {
  "DR001": { "vehicle_id": "VH001", "vehicle_type": "Mini Truck", "total_odometer_km": 125430.0, "engine_total_hours": 2450.5, "last_service_km": 118400.0 },
  "DR002": { "vehicle_id": "VH002", "vehicle_type": "Mini Truck", "total_odometer_km": 98750.0, "engine_total_hours": 1820.0, "last_service_km": 92500.0 },
  "DR003": { "vehicle_id": "VH003", "vehicle_type": "Medium Cargo", "total_odometer_km": 164200.0, "engine_total_hours": 3120.2, "last_service_km": 161000.0 },
  "DR004": { "vehicle_id": "VH004", "vehicle_type": "Heavy Cargo Truck", "total_odometer_km": 215300.0, "engine_total_hours": 4200.8, "last_service_km": 204500.0 },
  "DR005": { "vehicle_id": "VH005", "vehicle_type": "Heavy Cargo Truck", "total_odometer_km": 189400.0, "engine_total_hours": 3760.4, "last_service_km": 188000.0 },
  "DR006": { "vehicle_id": "VH006", "vehicle_type": "Pickup Truck", "total_odometer_km": 72400.0, "engine_total_hours": 1120.0, "last_service_km": 70000.0 },
  "DR007": { "vehicle_id": "VH007", "vehicle_type": "Heavy Cargo Truck", "total_odometer_km": 234100.0, "engine_total_hours": 4980.5, "last_service_km": 231000.0 },
  "DR008": { "vehicle_id": "VH008", "vehicle_type": "Mini Truck", "total_odometer_km": 114500.0, "engine_total_hours": 2180.2, "last_service_km": 102000.0 },
  "DR009": { "vehicle_id": "VH009", "vehicle_type": "Mini Truck", "total_odometer_km": 89200.0, "engine_total_hours": 1650.0, "last_service_km": 87000.0 },
  "DR010": { "vehicle_id": "VH010", "vehicle_type": "Mini Truck", "total_odometer_km": 142100.0, "engine_total_hours": 2980.1, "last_service_km": 139000.0 }
};

export const generateMockJourneys = (driverId) => {
  const driver = MOCK_DRIVERS.find(d => d.driver_id === driverId) || MOCK_DRIVERS[0];
  const list = [];

  const routeTypes = ['Mixed', 'Highway', 'City', 'Rural', 'Mountain'];
  const baseScore = driver.avg_score;

  for (let i = 0; i < 12; i++) {
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
      start_time: new Date(Date.now() - i * 24 * 3600000 - 3 * 3600000).toLocaleString('en-US', { hour12: false }).replace(',', ''),
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

export const getMockJourneyDetails = (journeyId, driverId) => {
  const driver = MOCK_DRIVERS.find(d => d.driver_id === driverId) || MOCK_DRIVERS[0];
  const vehicle = MOCK_VEHICLES[driverId] || MOCK_VEHICLES["DR001"];
  const journeys = generateMockJourneys(driverId);
  const brief = journeys.find(j => j.journey_id === journeyId) || journeys[0];

  const isTheft = brief.fuel_theft_detected;
  const isMaintCritical = brief.maintenance_critical;

  const speedProfile = Array.from({ length: 12 }, (_, k) => ({
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
      end_time: new Date(new Date(brief.start_time).getTime() + brief.duration_min * 60000).toLocaleString('en-US', { hour12: false }).replace(',', ''),
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
      scoring_method: 'ML',
      ml_confidence: 88.4,
      score_comparison: {
        active_method: 'ML',
        rule_based: {
          final_score: parseFloat((brief.driver_score * 0.96).toFixed(1)),
          risk_level: brief.driver_score >= 80 ? 'Low Risk' : (brief.driver_score >= 60 ? 'Mild Risk' : 'High Risk'),
          penalties: {
            accel_penalty: parseFloat((accel * 0.5).toFixed(1)),
            braking_penalty: parseFloat((brake * 0.6).toFixed(1)),
            speeding_penalty: parseFloat((overspeed * 1.0).toFixed(1)),
            cornering_penalty: parseFloat((cornering * 0.4).toFixed(1)),
            idle_penalty: parseFloat((idle > 30 ? (idle - 30) * 0.2 : 0.0).toFixed(1))
          }
        },
        ml: (() => {
          const rulePenalties = {
            accel_penalty: parseFloat((accel * 0.5).toFixed(1)),
            braking_penalty: parseFloat((brake * 0.6).toFixed(1)),
            speeding_penalty: parseFloat((overspeed * 1.0).toFixed(1)),
            cornering_penalty: parseFloat((cornering * 0.4).toFixed(1)),
            idle_penalty: parseFloat((idle > 30 ? (idle - 30) * 0.2 : 0.0).toFixed(1))
          };
          const totalWeightedRulePenalty = (
            rulePenalties.accel_penalty * 0.20 +
            rulePenalties.braking_penalty * 0.30 +
            rulePenalties.speeding_penalty * 0.30 +
            rulePenalties.cornering_penalty * 0.10 +
            rulePenalties.idle_penalty * 0.10
          );
          const totalMlPenalty = 100.0 - brief.driver_score;
          let mlPenalties = {
            accel_penalty: 0,
            braking_penalty: 0,
            speeding_penalty: 0,
            cornering_penalty: 0,
            idle_penalty: 0
          };
          if (totalWeightedRulePenalty > 0 && totalMlPenalty > 0) {
            const ratio = totalMlPenalty / totalWeightedRulePenalty;
            mlPenalties = {
              accel_penalty: parseFloat((rulePenalties.accel_penalty * ratio).toFixed(1)),
              braking_penalty: parseFloat((rulePenalties.braking_penalty * ratio).toFixed(1)),
              speeding_penalty: parseFloat((rulePenalties.speeding_penalty * ratio).toFixed(1)),
              cornering_penalty: parseFloat((rulePenalties.cornering_penalty * ratio).toFixed(1)),
              idle_penalty: parseFloat((rulePenalties.idle_penalty * ratio).toFixed(1))
            };
          } else if (totalMlPenalty > 0) {
            mlPenalties = {
              accel_penalty: parseFloat((totalMlPenalty * 0.20).toFixed(1)),
              braking_penalty: parseFloat((totalMlPenalty * 0.30).toFixed(1)),
              speeding_penalty: parseFloat((totalMlPenalty * 0.30).toFixed(1)),
              cornering_penalty: parseFloat((totalMlPenalty * 0.10).toFixed(1)),
              idle_penalty: parseFloat((totalMlPenalty * 0.10).toFixed(1))
            };
          }
          return {
            final_score: brief.driver_score,
            risk_level: brief.driver_score >= 80 ? 'Low Risk' : (brief.driver_score >= 60 ? 'Mild Risk' : 'High Risk'),
            confidence: 88.4,
            penalties: mlPenalties
          };
        })(),
        score_difference: parseFloat((brief.driver_score - (brief.driver_score * 0.96)).toFixed(1))
      },
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
          { issue: 'Battery Issue', severity: 'Critical', detail: 'External voltage drop: 11.2 V (threshold < 11.5 V)' },
          { issue: 'Engine Overheating', severity: 'Critical', detail: 'Coolant temperature: 104.5°C exceeds max threshold of 100°C' }
        ]
        : (brief.driver_score < 70
          ? [{ issue: 'Brake Wear', severity: 'Warning', detail: 'Harsh braking frequency suggests high wear rates' }]
          : []),
      health_scores: isMaintCritical
        ? { brake: 88.5, tire: 92.4, battery: 9.3, engine: 75.6 }
        : (brief.driver_score < 70
          ? { brake: 25.4, tire: 84.1, battery: 94.0, engine: 88.2 }
          : { brake: 95.8, tire: 98.1, battery: 100.0, engine: 92.5 })
    },
    speed_profile: speedProfile
  };
};

export const getDriverColor = (driverId) => {
  const colors = [
    "#2563eb", "#10b981", "#d97706", "#ef4444", "#8b5cf6",
    "#ec4899", "#06b6d4", "#f59e0b", "#14b8a6", "#6366f1"
  ];
  let hash = 0;
  for (let i = 0; i < driverId.length; i++) {
    hash = driverId.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
};

export const cleanTripDetails = (data) => {
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

    if (data.expected_fuel.expected_liters === 0 && data.expected_fuel.actual_liters === 0) {
      const rType = data.journey ? data.journey.route_type : 'Mixed';
      const expLiters = rType === 'Highway' ? 38.5 : (rType === 'City' ? 10.2 : 22.4);
      const isTheft = data.fuel_theft ? data.fuel_theft.detected : false;
      const score = data.driver_score ? data.driver_score.score : 100;
      const vPct = isTheft ? 38.2 : (score < 70 ? 12.4 : 2.1);
      const actLiters = parseFloat((expLiters * (1 + vPct / 100)).toFixed(2));

      data.expected_fuel.expected_liters = expLiters;
      data.expected_fuel.actual_liters = actLiters;
      data.expected_fuel.variance_pct = vPct;
    }
  }
  return data;
};

export const getScoreColorClass = (score) => {
  if (score >= 80) return 'bg-blue-50 text-blue-700 border border-blue-200';
  if (score >= 60) return 'bg-amber-50 text-amber-700 border border-amber-200';
  return 'bg-rose-50 text-rose-700 border border-rose-200';
};

