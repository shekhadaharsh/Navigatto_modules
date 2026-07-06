import React from 'react';

// ── Free OpenStreetMap Mini-Map for Fuel Theft Modal ──
export default function TheftLocationMap({ lat, lng }) {
  const mapRef = React.useRef(null);
  const mapInstanceRef = React.useRef(null);

  React.useEffect(() => {
    if (!lat || !lng || !mapRef.current || typeof L === 'undefined') return;
    if (mapInstanceRef.current) {
      mapInstanceRef.current.remove();
      mapInstanceRef.current = null;
    }
    const map = L.map(mapRef.current, {
      center: [lat, lng],
      zoom: 14,
      zoomControl: true,
      scrollWheelZoom: false,
    });
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution: '© <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
      maxZoom: 19,
    }).addTo(map);
    const redIcon = L.divIcon({
      className: "",
      html: `<div style="width:22px;height:22px;background:#ef4444;border:3px solid white;border-radius:50% 50% 50% 0;transform:rotate(-45deg);box-shadow:0 2px 6px rgba(0,0,0,0.4);"></div>`,
      iconSize: [22, 22],
      iconAnchor: [11, 22],
    });
    L.marker([lat, lng], { icon: redIcon })
      .addTo(map)
      .bindPopup("⛽ Theft Location")
      .openPopup();
    mapInstanceRef.current = map;
    return () => {
      if (mapInstanceRef.current) {
        mapInstanceRef.current.remove();
        mapInstanceRef.current = null;
      }
    };
  }, [lat, lng]);

  if (!lat || !lng) return <div className="text-xs text-slate-400 italic">No GPS data available</div>;
  return (
    <div style={{ borderRadius: "10px", overflow: "hidden", border: "1px solid #e2e8f0" }}>
      <div ref={mapRef} style={{ height: "160px", width: "100%" }} />
      <div style={{ fontSize: "11px", color: "#64748b", padding: "4px 8px", background: "#f8fafc", borderTop: "1px solid #e2e8f0" }}>
        📍 {lat.toFixed(5)}, {lng.toFixed(5)}
      </div>
    </div>
  );
}
