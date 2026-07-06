import os

path = r"c:\Users\Admin\Desktop\communication_craft\FMC_650\Navigatto_modules\project\frontend\src\components\TripDiagnostics.jsx"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("journeyDetails.maintenance.priority", "(journeyDetails?.maintenance?.priority || 'OK')")
content = content.replace("journeyDetails.maintenance.status", "(journeyDetails?.maintenance?.status || 'OK')")
content = content.replace("journeyDetails.maintenance.alerts", "(journeyDetails?.maintenance?.alerts || [])")
content = content.replace("journeyDetails.maintenance.", "(journeyDetails?.maintenance || {}).")
content = content.replace("journeyDetails.driver_score.", "(journeyDetails?.driver_score || {}).")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Replaced unsafe maintenance/driver_score accesses in TripDiagnostics.jsx")
