import React from 'react';
import { ShieldAlert, Gauge, Clock, TrendingUp, Compass, CheckCircle2 } from 'lucide-react';

export const InsightIcon = ({ iconType, className }) => {
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

export const getDriverInsights = (details) => {
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
      text: 'Maintain a 3-second safety gap to avoid harsh braking events, preserving brake pad life and securing fleet cargo integrity.',
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
      color: 'text-blue-600 bg-blue-50 border-blue-100',
      chipLabel: '🏆 CLASS LEADER',
      chipStyle: 'bg-blue-50 text-blue-700 border-blue-200/50',
      estimate: 'Est. Impact: All systems operating at peak safety',
      penalty: 0
    }];
  }

  return insights.sort((a, b) => b.penalty - a.penalty);
};
