import { useState, useEffect, useCallback } from 'react';
import { ensureDeviceToken } from './api/device';
import { fetchRequests } from './api/requests';
import MapView from './components/MapView';
import Sidebar from './components/Sidebar';
import RequestModal from './components/RequestModal';
import CreateRequestModal from './components/CreateRequestModal';
import FloatingButtons from './components/FloatingButtons';

const POLL_MS = 10000;

function isHighPriority(request) {
  const severity = Number(request?.severity ?? 0);
  const rankScore = Number(request?.rank_score ?? 0);
  const urgency = request?.urgency_window;
  return severity >= 4 || urgency === 'now' || rankScore >= 0.75;
}

export default function App() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [bbox, setBbox] = useState(null);
  const [selectedRequestId, setSelectedRequestId] = useState(null);
  const [pickedLocation, setPickedLocation] = useState(null);
  const [createModalOpen, setCreateModalOpen] = useState(false);
  const [crisisMode, setCrisisMode] = useState(false);

  const loadRequests = useCallback(async () => {
    if (!bbox) return;
    setLoading(true);
    try {
      const data = await fetchRequests({
        bbox,
        sort: 'rank',
      });
      const visible = (data.requests || []).filter((r) => {
        if (crisisMode) {
          const isActionable = r.status === 'open' || r.status === 'funded';
          return isActionable && isHighPriority(r);
        }
        return r.status !== 'cancelled';
      });
      setRequests(visible);
    } catch {
      setRequests([]);
    } finally {
      setLoading(false);
    }
  }, [bbox, crisisMode]);

  useEffect(() => {
    ensureDeviceToken().catch(console.error);
  }, []);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  useEffect(() => {
    if (!bbox) return;
    const id = setInterval(loadRequests, POLL_MS);
    return () => clearInterval(id);
  }, [bbox, loadRequests]);

  const handleBoundsChange = useCallback((newBbox) => {
    setBbox(newBbox);
  }, []);

  const handleRequestClick = useCallback((request) => {
    setSelectedRequestId(request?.id ?? null);
  }, []);

  const handleDonated = useCallback(() => {
    loadRequests();
  }, [loadRequests]);

  const handleCreated = useCallback(() => {
    setCreateModalOpen(false);
    loadRequests();
  }, [loadRequests]);

  return (
    <div className="h-screen w-screen overflow-hidden bg-slate-950 text-white flex flex-col">
      <div className="w-full z-[1200] flex justify-center px-4 py-2 bg-amber-500/90 text-black text-center text-sm font-medium shadow-md">
        Ranked by urgency and vulnerability, not profit.
      </div>

      <div className="flex-1 flex overflow-hidden relative">
        {/* Left Sidebar - 1/3 width */}
        <div className="w-1/3 h-full relative z-[1000]">
          <Sidebar
            requests={requests}
            loading={loading}
            selectedRequestId={selectedRequestId}
            onRequestClick={handleRequestClick}
            crisisMode={crisisMode}
          />
        </div>

        {/* Right Map - 2/3 width */}
        <div className="w-2/3 h-full relative">
          <MapView
            requests={requests}
            onBoundsChange={handleBoundsChange}
            onRequestClick={handleRequestClick}
            pickedLocation={pickedLocation}
            onMapPick={setPickedLocation}
            selectedRequestId={selectedRequestId}
          />
        </div>

        <FloatingButtons
          onCreateRequest={() => setCreateModalOpen(true)}
          crisisMode={crisisMode}
          onCrisisModeToggle={() => setCrisisMode((v) => !v)}
        />
      </div>

      <RequestModal
        key={selectedRequestId || "closed"}
        requestId={selectedRequestId}
        onClose={() => setSelectedRequestId(null)}
        onDonated={handleDonated}
        onClaimed={handleDonated}
        onStatusChanged={handleDonated}
      />

      {createModalOpen && (
        <CreateRequestModal
          onClose={() => setCreateModalOpen(false)}
          onCreated={handleCreated}
          pickedLocation={pickedLocation}
        />
      )}
    </div>
  );
}
