import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { fetchRequestDetail, donateToRequest, claimRequest, findShops, updateRequestStatus } from '../api/requests';

import RequestProgress from './RequestProgress';

const CATEGORY_ICONS = {
  meds: '💊',
  groceries: '🛒',
  shelter: '🏠',
  transport: '🚗',
  other: '📦',
};

const PRESET_AMOUNTS = [5, 10, 25];

export default function RequestModal({ requestId, onClose, onDonated, onClaimed, onStatusChanged }) {
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(true);
  const [donating, setDonating] = useState(false);
  const [claiming, setClaiming] = useState(false);
  const [customAmount, setCustomAmount] = useState('');
  const [error, setError] = useState(null);
  const [shopData, setShopData] = useState(null);
  const [loadingShops, setLoadingShops] = useState(false);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [refreshError, setRefreshError] = useState(null);
  const mutationPending = useRef(false);
  const mutationVersion = useRef(0);

  useEffect(() => {
    if (!requestId) return;
    let active = true;
    let fetching = false;
    setDetail(null);
    setLoading(true);
    setError(null);
    setRefreshError(null);
    setShopData(null);
    const load = async (initial = false) => {
      if (fetching || mutationPending.current) return;
      fetching = true;
      const version = mutationVersion.current;
      try {
        const result = await fetchRequestDetail(requestId);
        if (!active || mutationPending.current || version !== mutationVersion.current) return;
        setDetail(result.request);
        setRefreshError(null);
        if (initial && result.request.lat != null && result.request.lng != null) {
          findShops(requestId, result.request.lat, result.request.lng)
            .then((shops) => { if (active) setShopData(shops); })
            .catch(() => {});
        }
      } catch (e) {
        if (active) {
          if (initial) setError(e.response?.data?.detail || 'Failed to load');
          else setRefreshError('Could not refresh. Showing the last available update.');
        }
      } finally {
        fetching = false;
        if (active) setLoading(false);
      }
    };
    load(true);
    const timer = setInterval(() => load(), 10000);
    return () => { active = false; clearInterval(timer); };
  }, [requestId]);

  const handleDonate = async (amount) => {
    const num = typeof amount === 'number' ? amount : parseFloat(customAmount);
    if (!num || num <= 0) return;
    mutationPending.current = true;
    mutationVersion.current += 1;
    setDonating(true);
    setError(null);
    try {
      const res = await donateToRequest(requestId, num);
      setDetail((prev) => (prev ? { ...prev, ...res.request } : res.request));
      onDonated?.(res);
    } catch (e) {
      setError(e.response?.data?.detail || 'Donation failed');
    } finally {
      mutationPending.current = false;
      setDonating(false);
      setCustomAmount('');
    }
  };

  const handleFindShops = async () => {
    if (!detail) return;
    setLoadingShops(true);
    setError(null);
    try {
      const res = await findShops(requestId, detail.lat, detail.lng);
      setShopData(res);
    } catch (e) {
      console.error(e);
      setError('Failed to find shops');
    } finally {
      setLoadingShops(false);
    }
  };

  const handleClaim = async () => {
    mutationPending.current = true;
    mutationVersion.current += 1;
    setClaiming(true);
    setError(null);
    try {
      await claimRequest(requestId);
      const res = await fetchRequestDetail(requestId);
      setDetail(res.request);
      onClaimed?.();
    } catch (e) {
      setError(e.response?.data?.detail || 'Claim failed');
    } finally {
      mutationPending.current = false;
      setClaiming(false);
    }
  };



  const handleAdvance = async (status) => {
    if (mutationPending.current) return;
    mutationPending.current = true;
    mutationVersion.current += 1;
    setUpdatingStatus(true);
    setError(null);
    try {
      const result = await updateRequestStatus(requestId, status);
      setDetail((previous) => ({ ...previous, ...result.request }));
      setRefreshError(null);
      onStatusChanged?.();
    } catch (e) {
      setError(e.response?.data?.detail || 'Could not update delivery progress');
      // Refresh after a conflicting claim/status change to remove stale actions.
      try {
        const result = await fetchRequestDetail(requestId);
        setDetail(result.request);
      } catch { /* Keep the existing detail and action error. */ }
    } finally {
      mutationPending.current = false;
      setUpdatingStatus(false);
    }
  };

  const progress = detail ? Math.min(1, detail.progress ?? 0) : 0;
  const isFunded = detail?.status === 'funded';
  const isClaimed = ['claimed', 'on_the_way', 'delivered'].includes(detail?.status);
  const canClaim = isFunded && !isClaimed;
  const googleMapsUrl = detail
    ? `https://www.google.com/maps/dir/?api=1&destination=${detail.lat},${detail.lng}`
    : '#';

  if (!requestId) return null;

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[1100] flex items-end sm:items-center justify-center p-0 sm:p-4"
        onClick={onClose}
      >
        <motion.div
          initial={{ opacity: 0, y: 100 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: 100 }}
          transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          className="w-full max-w-lg rounded-t-3xl sm:rounded-3xl bg-slate-900/95 backdrop-blur-xl border border-white/10 shadow-2xl max-h-[90vh] overflow-hidden"
          onClick={(e) => e.stopPropagation()}
        >
          <div className="flex justify-center pt-3 pb-2 border-b border-white/10">
            <div className="w-12 h-1 rounded-full bg-white/30" />
          </div>
          <div className="overflow-y-auto max-h-[85vh] p-4">
            {loading ? (
              <div className="animate-pulse space-y-4">
                <div className="h-8 w-3/4 bg-white/20 rounded" />
                <div className="h-4 w-full bg-white/10 rounded" />
                <div className="h-20 bg-white/10 rounded" />
              </div>
            ) : error && !detail ? (
              <p className="text-red-400">{error}</p>
            ) : detail ? (
              <>
                <div className="flex items-start justify-between gap-2 mb-4">
                  <div className="flex items-center gap-3">
                    <span className="text-3xl">
                      {CATEGORY_ICONS[detail.category] || '📦'}
                    </span>
                    <div>
                      <h2 className="text-xl font-semibold text-white capitalize">
                        {detail.category}
                      </h2>
                      <p className="text-sm text-gray-400">
                        Urgency: {detail.urgency_window} · Severity {detail.severity}/5
                      </p>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={onClose}
                    className="p-2 rounded-full hover:bg-white/10 text-gray-400"
                    aria-label="Close"
                  >
                    ✕
                  </button>
                </div>

                <p className="text-gray-300 text-sm whitespace-pre-wrap mb-4">
                  {detail.raw_text}
                </p>

                <RequestProgress request={detail} updating={updatingStatus} onAdvance={handleAdvance} />
                {refreshError && <p role="status" className="mb-3 text-xs text-amber-200">{refreshError}</p>}

                {detail.rank_reason && (
                  <div
                    className="flex items-center gap-2 text-xs text-amber-200/90 bg-amber-500/10 rounded-lg px-3 py-2 mb-4"
                    title="AI prioritized this request by urgency, severity, and funding gap — not profit."
                  >
                    <span>💡</span>
                    <span>AI prioritized: {detail.rank_reason}</span>
                  </div>
                )}
                <div className="flex flex-wrap gap-2 mb-4">
                  {detail.severity >= 4 && (
                    <span className="text-xs bg-amber-500/20 text-amber-200 rounded-full px-2 py-1">
                      High need
                    </span>
                  )}
                  <span className="text-xs bg-slate-500/20 text-slate-300 rounded-full px-2 py-1">
                    Vulnerability-aware ranking
                  </span>
                  <span className="text-xs text-gray-500 border border-white/10 rounded-full px-2 py-1">
                    👴 Elderly
                  </span>
                  <span className="text-xs text-gray-500 border border-white/10 rounded-full px-2 py-1">
                    👶 Infant
                  </span>
                  <span className="text-xs text-gray-500 border border-white/10 rounded-full px-2 py-1">
                    ♿ Disabled
                  </span>
                </div>

                {detail.items?.length > 0 && (
                  <ul className="text-sm text-gray-300 mb-4 space-y-3">
                    {detail.items.map((item, i) => {
                      const shopInfo = shopData?.items?.find(
                        (s) => s.item_name.toLowerCase() === item.name.toLowerCase()
                      )?.nearest_shop;
                      return (
                        <li key={i} className="flex flex-col gap-1">
                          <div className="flex justify-between items-start">
                            <span>
                              {item.qty} {item.unit} {item.name}
                              {item.notes ? ` — ${item.notes}` : ''}
                            </span>
                          </div>
                          
                          {/* Show shop info only if funded/claimed/delivered */}
                          {shopData && shopInfo && (isFunded || isClaimed) && (
                            <div className="bg-white/5 rounded-lg p-2 text-xs mt-1 border border-white/5">
                              <div className="flex justify-between items-center mb-1">
                                <span className="text-emerald-400 font-medium">Best option: {shopInfo.name}</span>
                                <span className="text-gray-400">{shopInfo.distance_mi} mi</span>
                              </div>
                              <div className="flex justify-between items-center">
                                <span className="text-gray-400">{shopInfo.address}</span>
                                <a 
                                  href={shopInfo.navigation_link} 
                                  target="_blank" 
                                  rel="noopener noreferrer"
                                  className="text-blue-400 hover:text-blue-300 font-medium flex items-center gap-1"
                                >
                                  📍 Navigate
                                </a>
                              </div>
                              <div className="mt-1 text-gray-400">
                                Est. Price: <span className="text-white">${shopInfo.price}</span>
                              </div>
                            </div>
                          )}
                        </li>
                      );
                    })}
                  </ul>
                )}

                <div className="mb-4">
                  <div className="flex justify-between text-sm text-gray-400 mb-1">
                    <span>Funding progress</span>
                    <span>
                      ${(detail.funded_amount ?? 0).toFixed(0)} / $
                      {(detail.funding_goal ?? 0).toFixed(0)}
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-white/20 overflow-hidden">
                    <motion.div
                      className="h-full rounded-full bg-emerald-400"
                      initial={false}
                      animate={{ width: `${progress * 100}%` }}
                      transition={{ duration: 0.5, ease: 'easeOut' }}
                    />
                  </div>
                </div>

                {error && (
                  <p role="alert" className="text-red-400 text-sm mb-4">{error}</p>
                )}

                {detail.status === 'open' && (
                  <div className="space-y-3">
                     {/* Find Shops Button */}
                    {shopData && (isFunded || isClaimed) && (
                      <div className="mt-4 space-y-2">
                        {shopData.items?.map((item, i) => {
                          const shop = item.nearest_shop;
                          if (!shop) return null;
                          return (
                            <a
                              key={i}
                              href={shop.navigation_link}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="block w-full py-3 rounded-xl bg-blue-600/80 hover:bg-blue-600 text-center text-white font-medium"
                            >
                              Shop for {item.item_name} <span className="text-blue-200 text-xs">({shop.name})</span>
                            </a>
                          );
                        })}
                      </div>
                    )}

                    <p className="text-sm text-gray-400">Donate</p>
                    <div className="flex gap-2 flex-wrap">
                      {PRESET_AMOUNTS.map((amt) => (
                        <button
                          key={amt}
                          type="button"
                          disabled={donating}
                          onClick={() => handleDonate(amt)}
                          className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-white font-medium"
                        >
                          ${amt}
                        </button>
                      ))}
                      <div className="flex gap-2 flex-1 min-w-[120px]">
                        <input
                          type="number"
                          min="1"
                          step="1"
                          placeholder="Other"
                          value={customAmount}
                          onChange={(e) => setCustomAmount(e.target.value)}
                          className="flex-1 rounded-xl bg-white/10 border border-white/20 px-3 py-2 text-white placeholder-gray-500 text-sm"
                        />
                        <button
                          type="button"
                          disabled={donating || !customAmount}
                          onClick={() => handleDonate()}
                          className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-white font-medium text-sm"
                        >
                          Give
                        </button>
                      </div>
                    </div>
                  </div>
                )}

                {canClaim && (
                  <div className="mt-4 space-y-2">
                    <button
                      type="button"
                      disabled={claiming}
                      onClick={handleClaim}
                      className="w-full py-3 rounded-xl bg-amber-500 hover:bg-amber-600 disabled:opacity-50 text-white font-semibold"
                    >
                      {claiming ? 'Claiming…' : 'Claim'}
                    </button>
                    <a
                      href={googleMapsUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="block w-full py-3 rounded-xl bg-white/10 hover:bg-white/20 text-center text-white font-medium"
                    >
                      Open Request Location in Maps
                    </a>
                    {(!shopData || !shopData.items || shopData.items.length === 0) && (
                        <button
                          type="button"
                          onClick={handleFindShops}
                          disabled={loadingShops}
                          className="block w-full py-3 rounded-xl bg-blue-600/80 hover:bg-blue-600 text-center text-white font-medium"
                        >
                          {loadingShops ? 'Finding Shops...' : 'Find Nearest Shops'}
                        </button>
                    )}
                    {shopData?.items?.map((item, i) => {
                        const shop = item.nearest_shop;
                        if (!shop) return null;
                        return (
                          <a
                            key={i}
                            href={shop.navigation_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block w-full py-3 rounded-xl bg-blue-600/80 hover:bg-blue-600 text-center text-white font-medium"
                          >
                            Shop for {item.item_name} <span className="text-blue-200 text-xs">({shop.name})</span>
                          </a>
                        );
                    })}
                  </div>
                )}

                {isClaimed && (
                  <div className="mt-4 space-y-2">
                    <a
                        href={googleMapsUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="block w-full py-3 rounded-xl bg-amber-500 hover:bg-amber-600 text-center text-white font-semibold"
                    >
                        Open Request Location in Maps
                    </a>
                    {(!shopData || !shopData.items || shopData.items.length === 0) && (
                        <button
                          type="button"
                          onClick={handleFindShops}
                          disabled={loadingShops}
                          className="block w-full py-3 rounded-xl bg-blue-600/80 hover:bg-blue-600 text-center text-white font-medium"
                        >
                          {loadingShops ? 'Finding Shops...' : 'Find Nearest Shops'}
                        </button>
                    )}
                    {shopData?.items?.map((item, i) => {
                        const shop = item.nearest_shop;
                        if (!shop) return null;
                        return (
                          <a
                            key={i}
                            href={shop.navigation_link}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="block w-full py-3 rounded-xl bg-blue-600/80 hover:bg-blue-600 text-center text-white font-medium"
                          >
                            Shop for {item.item_name} <span className="text-blue-200 text-xs">({shop.name})</span>
                          </a>
                        );
                    })}
                  </div>
                )}
              </>
            ) : null}
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
