import os

app_path = r"c:\Users\Admin\Desktop\communication_craft\FMC_650\Navigatto_modules\project\frontend\src\App.jsx"
out_path = r"c:\Users\Admin\Desktop\communication_craft\FMC_650\Navigatto_modules\project\frontend\src\modals\MaintenanceDashboardModal.jsx"

with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Line 2367 is 1-indexed 2367 -> 0-indexed 2366. Line 2808 is 1-indexed 2808 -> 0-indexed slice up to 2808.
section_lines = lines[2366:2808]

header = """import React from 'react';
import {
  Wrench, XCircle, Search, Filter, AlertTriangle, AlertCircle, CheckCircle2,
  Activity, Thermometer, Battery, Compass, ChevronRight, RefreshCw
} from 'lucide-react';

export default function MaintenanceDashboardModal({
  isOpen,
  onClose,
  maintSearchTerm,
  setMaintSearchTerm,
  maintFilterPriority,
  setMaintFilterPriority,
  maintVehiclesList,
  selectedMaintVehicle,
  setSelectedMaintVehicle,
  maintHealthData,
  isLoadingMaintHealth
}) {
  if (!isOpen) return null;
  return (
"""

footer = """  );
}
"""

content = "".join(section_lines).replace("setIsMaintDialogOpen(false)", "onClose()")

with open(out_path, "w", encoding="utf-8") as f:
    f.write(header + content + footer)

print(f"Extracted {len(section_lines)} lines into {out_path}")
