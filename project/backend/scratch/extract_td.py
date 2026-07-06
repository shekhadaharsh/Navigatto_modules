import os

app_path = r"c:\Users\Admin\Desktop\communication_craft\FMC_650\Navigatto_modules\project\frontend\src\App.jsx"
out_path = r"c:\Users\Admin\Desktop\communication_craft\FMC_650\Navigatto_modules\project\frontend\src\components\TripDiagnostics.jsx"

with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# 1-indexed 1568 to 2364 -> 0-indexed 1567 to 2364
section_lines = lines[1567:2364]

header = """import React from 'react';
import {
  ArrowLeft, Compass, Truck, Navigation, Clock, MapPin, Gauge, Activity,
  TrendingUp, TrendingDown, ShieldAlert, Droplet, AlertTriangle, RefreshCw,
  CheckCircle2, ChevronRight, Wrench, Battery, Thermometer
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
  handleReportAcknowledge,
  openMaintenanceDashboard,
  maintHealthData
}) {
  return (
"""

footer = """  );
}
"""

with open(out_path, "w", encoding="utf-8") as f:
    f.write(header + "".join(section_lines) + footer)

print(f"Extracted {len(section_lines)} lines into {out_path}")
