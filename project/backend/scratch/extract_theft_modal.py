import os

app_path = r"c:\Users\Admin\Desktop\communication_craft\FMC_650\Navigatto_modules\project\frontend\src\App.jsx"
out_path = r"c:\Users\Admin\Desktop\communication_craft\FMC_650\Navigatto_modules\project\frontend\src\modals\FuelTheftModal.jsx"

with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

# Line 2831 is 1-indexed 2831 -> 0-indexed 2830. Line 2993 is 1-indexed 2993 -> 0-indexed slice up to 2993.
section_lines = lines[2830:2993]

header = """import React from 'react';
import { ShieldAlert, XCircle, AlertTriangle, Clock, MapPin, Droplet, ArrowRight } from 'lucide-react';

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
"""

footer = """  );
}
"""

with open(out_path, "w", encoding="utf-8") as f:
    f.write(header + "".join(section_lines) + footer)

print(f"Extracted {len(section_lines)} lines into {out_path}")
