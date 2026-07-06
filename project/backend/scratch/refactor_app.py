import os

app_path = r"c:\Users\Admin\Desktop\communication_craft\FMC_650\Navigatto_modules\project\frontend\src\App.jsx"

with open(app_path, "r", encoding="utf-8") as f:
    lines = f.readlines()

top_imports = """import ReplayControl from './ReplayControl';
import DeviceSimulator from './DeviceSimulator';
import React, { useState, useEffect, useRef } from 'react';
import {
  Compass, Search, Truck, Calendar, Clock, Navigation, MapPin, Gauge,
  ShieldAlert, ShieldCheck, Droplet, Wrench, RefreshCw, AlertTriangle,
  AlertCircle, TrendingUp, TrendingDown, ArrowRight, ArrowLeft, User, Settings,
  Info, CheckCircle2, XCircle, ChevronRight, Activity, Battery, Thermometer
} from 'lucide-react';
import DriverSidebar from './components/DriverSidebar';
import TripSidebar from './components/TripSidebar';
import TripDiagnostics from './components/TripDiagnostics';
import MaintenanceDashboardModal from './modals/MaintenanceDashboardModal';
import SettingsModal from './modals/SettingsModal';
import FuelTheftModal from './modals/FuelTheftModal';
import { MOCK_DRIVERS, MOCK_VEHICLES, generateMockJourneys, getMockJourneyDetails, getDriverColor, cleanTripDetails } from './data/mockData';
"""

# Find line where "export default function App()" begins (1-indexed line 499 -> index 498)
app_fn_start = 498
# Verify
if "export default function App()" not in lines[app_fn_start]:
    for idx, l in enumerate(lines):
        if "export default function App()" in l:
            app_fn_start = idx
            break

# Find line where "{/* -------------------- LEFT SIDEBAR (DRIVERS LIST) -------------------- */}" is
sidebar_start = -1
for idx, l in enumerate(lines):
    if "LEFT SIDEBAR (DRIVERS LIST)" in l:
        sidebar_start = idx
        break

state_and_handlers = lines[app_fn_start:sidebar_start]

render_body = """        {/* -------------------- LEFT SIDEBAR (DRIVERS LIST) -------------------- */}
        <DriverSidebar
          mobileViewTab={mobileViewTab}
          searchTerm={searchTerm}
          setSearchTerm={setSearchTerm}
          isLoadingDrivers={isLoadingDrivers}
          filteredDrivers={filteredDrivers}
          activeDriverId={activeDriverId}
          setActiveDriverId={setActiveDriverId}
          setMobileViewTab={setMobileViewTab}
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
                handleReportAcknowledge={handleReportAcknowledge}
                openMaintenanceDashboard={openMaintenanceDashboard}
                maintHealthData={maintHealthData}
              />
              <MaintenanceDashboardModal
                isOpen={isMaintDialogOpen}
                onClose={() => setIsMaintDialogOpen(false)}
                maintSearchTerm={maintSearchTerm}
                setMaintSearchTerm={setMaintSearchTerm}
                maintFilterPriority={maintFilterPriority}
                setMaintFilterPriority={setMaintFilterPriority}
                maintVehiclesList={maintVehiclesList}
                selectedMaintVehicle={selectedMaintVehicle}
                setSelectedMaintVehicle={setSelectedMaintVehicle}
                maintHealthData={maintHealthData}
                isLoadingMaintHealth={isLoadingMaintHealth}
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
"""

new_app_content = top_imports + "\n" + "".join(state_and_handlers) + render_body

with open(app_path, "w", encoding="utf-8") as f:
    f.write(new_app_content)

print(f"Refactored App.jsx down to {len(new_app_content.splitlines())} lines.")
