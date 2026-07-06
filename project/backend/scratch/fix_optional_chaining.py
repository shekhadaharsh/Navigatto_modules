import os

path = r"c:\Users\Admin\Desktop\communication_craft\FMC_650\Navigatto_modules\project\frontend\src\components\TripDiagnostics.jsx"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

# Replace unsafe accesses
content = content.replace("journeyDetails.fuel_theft.detected", "journeyDetails?.fuel_theft?.detected")
content = content.replace("journeyDetails.fuel_theft.theft_events", "(journeyDetails?.fuel_theft?.theft_events || [])")
content = content.replace("journeyDetails.expected_fuel.actual_liters", "(journeyDetails?.expected_fuel?.actual_liters || 0)")
content = content.replace("journeyDetails.expected_fuel.expected_liters", "(journeyDetails?.expected_fuel?.expected_liters || 0)")
content = content.replace("journeyDetails.expected_fuel.fuel_efficiency_km_per_l", "(journeyDetails?.expected_fuel?.fuel_efficiency_km_per_l || 0)")
content = content.replace("journeyDetails.expected_fuel.status", "(journeyDetails?.expected_fuel?.status || 'Normal')")
content = content.replace("journeyDetails.expected_fuel.", "journeyDetails?.expected_fuel?.")

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("Replaced unsafe nested object accesses in TripDiagnostics.jsx")
