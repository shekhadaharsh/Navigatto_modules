import { useState, useRef, useEffect } from "react";

const ENABLE_MANUAL = true; // set false to hide

export default function ReplayControl() {
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState(null);
  const dropdownRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  // Poll status on mount
  useEffect(() => {
    if (!ENABLE_MANUAL) return;
    fetch("/api/replay/status")
      .then((r) => r.json())
      .then((d) => setStatus(d.running ? "running" : "stopped"))
      .catch(() => setStatus("stopped"));
  }, []);

  if (!ENABLE_MANUAL) return null;

  const handleAction = async (action) => {
    setOpen(false);
    setLoading(true);
    try {
      const res = await fetch(`/api/replay/${action}`, { method: "POST" });
      const data = await res.json();
      if (action === "stop") {
        setStatus("stopped");
        window.dispatchEvent(new Event("replay-stopped"));
      } else if (action === "start" || action === "fresh-start") {
        setStatus(
          data.status === "started" || data.status === "already_running"
            ? "running"
            : "stopped"
        );
        window.dispatchEvent(new Event("replay-started"));
        if (action === "fresh-start") {
          window.location.reload();
        }
      }
    } catch (e) {
      console.error("Replay action failed", e);
    } finally {
      setLoading(false);
    }
  };

  const isRunning = status === "running";

  // Label and color based on status
  const statusLabel = loading
    ? "Please wait…"
    : isRunning
    ? "Replay Running"
    : "Replay Stopped";

  const dotColor = isRunning ? "bg-emerald-500 animate-pulse" : "bg-slate-400";
  const borderColor = isRunning ? "border-emerald-400" : "border-slate-300";
  const bgColor = isRunning ? "bg-emerald-50 text-emerald-700" : "bg-white text-slate-700";
  const dividerColor = isRunning ? "bg-emerald-300" : "bg-slate-200";
  const chevronHover = isRunning ? "hover:bg-emerald-100" : "hover:bg-slate-100";

  return (
    <div className="relative inline-block" ref={dropdownRef}>
      {/* Main pill button */}
      <div className={`flex items-center rounded-lg overflow-hidden shadow-sm border text-sm font-medium ${borderColor} ${bgColor}`}>

        {/* Status label */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 select-none">
          <span className={`w-2 h-2 rounded-full ${dotColor}`} />
          <span>{statusLabel}</span>
        </div>

        {/* Divider */}
        <div className={`w-px self-stretch ${dividerColor}`} />

        {/* Chevron */}
        <button
          onClick={() => !loading && setOpen((o) => !o)}
          disabled={loading}
          className={`px-2 py-1.5 transition-colors ${chevronHover} ${loading ? "opacity-40 cursor-not-allowed" : "cursor-pointer"}`}
          aria-label="Replay options"
        >
          <svg
            className={`w-4 h-4 transition-transform ${open ? "rotate-180" : ""}`}
            fill="none" stroke="currentColor" viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Dropdown menu */}
      {open && (
        <div className="absolute right-0 mt-1 w-44 bg-white border border-slate-200 rounded-lg shadow-lg z-50 py-1 animate-fade-in">
          
          {/* Start */}
          <button
            onClick={() => handleAction("start")}
            disabled={loading || isRunning}
            className={`w-full text-left px-4 py-2 text-sm flex items-center gap-2
              ${isRunning
                ? "text-slate-300 cursor-not-allowed"
                : "text-slate-700 hover:bg-slate-50"}`}
          >
            <span className="text-emerald-500">▶</span> Start Replay
          </button>

          {/* Stop */}
          <button
            onClick={() => handleAction("stop")}
            disabled={loading || !isRunning}
            className={`w-full text-left px-4 py-2 text-sm flex items-center gap-2
              ${!isRunning
                ? "text-slate-300 cursor-not-allowed"
                : "text-orange-600 hover:bg-orange-50"}`}
          >
            <span>⏹</span> Stop Replay
          </button>

          <div className="my-1 border-t border-slate-100" />

          {/* Fresh Start */}
          <button
            onClick={() => handleAction("fresh-start")}
            disabled={loading}
            className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center gap-2"
          >
            <span>↺</span> Fresh Start
          </button>
        </div>
      )}
    </div>
  );
}