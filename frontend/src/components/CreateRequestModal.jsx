import { useEffect, useRef, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { invokeAI, createRequest } from '../api/requests';

const CATEGORY_ICONS = {
  meds: '💊',
  groceries: '🛒',
  shelter: '🏠',
  transport: '🚗',
  other: '📦',
};

const DEFAULT_LOCATION = { lat: 42.3601, lng: -71.0589 };

export default function CreateRequestModal({ onClose, onCreated, pickedLocation }) {
  const [step, setStep] = useState('input'); // input | summary | done
  const [text, setText] = useState('');
  const [draft, setDraft] = useState(null);
  const [afford, setAfford] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [speechSupported, setSpeechSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const recognitionRef = useRef(null);
  const location = pickedLocation ?? DEFAULT_LOCATION;

  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) return;

    setSpeechSupported(true);
    const recognition = new SpeechRecognition();
    recognition.lang = navigator.language || 'en-US';
    recognition.continuous = true;
    recognition.interimResults = false;

    recognition.onresult = (event) => {
      let chunk = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        if (result.isFinal) {
          chunk += `${result[0]?.transcript ?? ''} `;
        }
      }
      const incoming = chunk.trim();
      if (!incoming) return;
      setText((prev) => {
        if (!prev.trim()) return incoming;
        return `${prev.trim()} ${incoming}`;
      });
    };

    recognition.onerror = (event) => {
      if (event.error === 'not-allowed') {
        setError('Microphone permission denied.');
      } else if (event.error !== 'aborted') {
        setError('Voice input failed. Try again.');
      }
      setListening(false);
    };

    recognition.onend = () => setListening(false);
    recognitionRef.current = recognition;

    return () => {
      recognition.stop();
      recognitionRef.current = null;
    };
  }, []);

  const toggleVoiceInput = () => {
    if (!recognitionRef.current) return;
    if (listening) {
      recognitionRef.current.stop();
      setListening(false);
      return;
    }
    setError(null);
    recognitionRef.current.start();
    setListening(true);
  };

  const handleSubmitText = async () => {
    if (!text.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await invokeAI({
        text: text.trim(),
        location,
        requester_afford: 0,
      });
      setDraft(res.request_draft);
      setAfford('');
      setStep('summary');
    } catch (e) {
      setError(e.response?.data?.detail || 'AI parse failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmitRequest = async () => {
    if (!draft) return;
    const affordNum = parseFloat(afford);
    if (isNaN(affordNum) || affordNum < 0) {
      setError('Enter how much you can afford (0 is ok).');
      return;
    }
    setLoading(true);
    setError(null);
    try {
      await createRequest({
        raw_text: text,
        category: draft.category,
        urgency_window: draft.urgency_window,
        severity: draft.severity,
        items: draft.items || [],
        estimated_total: draft.estimated_total,
        requester_afford: affordNum,
        location,
      });
      setStep('done');
      onCreated?.();
    } catch (e) {
      setError(e.response?.data?.detail || 'Failed to create request');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AnimatePresence>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="fixed inset-0 z-[1100] flex items-end sm:items-center justify-center p-0 sm:p-4 bg-black/60 backdrop-blur-sm"
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
          <div className="p-4 overflow-y-auto max-h-[85vh]">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-xl font-semibold text-white">
                {step === 'input' && 'Request help'}
                {step === 'summary' && 'Confirm request'}
                {step === 'done' && 'Request submitted'}
              </h2>
              <button
                type="button"
                onClick={onClose}
                className="p-2 rounded-full hover:bg-white/10 text-gray-400"
                aria-label="Close"
              >
                ✕
              </button>
            </div>

            <AnimatePresence mode="wait">
              {step === 'input' && (
                <motion.div
                  key="input"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  className="space-y-4"
                >
                  <p className="text-xs text-gray-500">
                    Location: {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
                  </p>
                  <p className="text-sm text-gray-400">
                    Describe what you need (e.g. &quot;Need insulin by tonight, can&apos;t afford full cost&quot;). Tap the map before opening this modal to set request location.
                  </p>
                  <textarea
                    value={text}
                    onChange={(e) => setText(e.target.value)}
                    placeholder="I need..."
                    rows={4}
                    className="w-full rounded-xl bg-white/10 border border-white/20 px-4 py-3 text-white placeholder-gray-500 resize-none"
                  />
                  <div className="flex items-center justify-between gap-3">
                    <button
                      type="button"
                      onClick={toggleVoiceInput}
                      disabled={!speechSupported || loading}
                      className="px-4 py-2 rounded-xl bg-white/10 hover:bg-white/20 disabled:opacity-50 text-white text-sm font-medium"
                    >
                      {listening ? 'Stop voice input' : 'Use voice input'}
                    </button>
                    {!speechSupported && (
                      <span className="text-xs text-gray-500">
                        Voice input is not supported in this browser.
                      </span>
                    )}
                  </div>
                  {error && <p className="text-red-400 text-sm">{error}</p>}
                  <button
                    type="button"
                    disabled={loading || !text.trim()}
                    onClick={handleSubmitText}
                    className="w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-white font-semibold"
                  >
                    {loading ? 'Parsing…' : 'Continue'}
                  </button>
                </motion.div>
              )}

              {step === 'summary' && draft && (
                <motion.div
                  key="summary"
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: 10 }}
                  className="space-y-4"
                >
                  <div className="rounded-2xl border border-white/10 bg-white/5 p-4 space-y-2">
                    <div className="flex items-center gap-2">
                      <span className="text-2xl">
                        {CATEGORY_ICONS[draft.category] || '📦'}
                      </span>
                      <span className="font-medium text-white capitalize">
                        {draft.category}
                      </span>
                      <span className="text-xs text-amber-200 bg-amber-500/20 px-2 py-0.5 rounded">
                        {draft.urgency_window}
                      </span>
                    </div>
                    <p className="text-sm text-gray-400">
                      Severity {draft.severity}/5 · Est. ${draft.estimated_total?.toFixed(0)}
                    </p>
                    {draft.items?.length > 0 && (
                      <ul className="text-sm text-gray-300">
                        {draft.items.map((it, i) => (
                          <li key={i}>
                            {it.qty} {it.unit} {it.name}
                          </li>
                        ))}
                      </ul>
                    )}
                  </div>
                  <div>
                    <label className="block text-sm text-gray-400 mb-1">
                      How much can you afford? ($)
                    </label>
                    <input
                      type="number"
                      min="0"
                      step="1"
                      value={afford}
                      onChange={(e) => setAfford(e.target.value)}
                      placeholder="0"
                      className="w-full rounded-xl bg-white/10 border border-white/20 px-4 py-3 text-white placeholder-gray-500"
                    />
                  </div>
                  {error && <p className="text-red-400 text-sm">{error}</p>}
                  <button
                    type="button"
                    disabled={loading}
                    onClick={handleSubmitRequest}
                    className="w-full py-3 rounded-xl bg-emerald-500 hover:bg-emerald-600 disabled:opacity-50 text-white font-semibold"
                  >
                    {loading ? 'Submitting…' : 'Submit request'}
                  </button>
                </motion.div>
              )}

              {step === 'done' && (
                <motion.div
                  key="done"
                  initial={{ opacity: 0 }}
                  animate={{ opacity: 1 }}
                  className="text-center py-6"
                >
                  <p className="text-4xl mb-2">✅</p>
                  <p className="text-white font-medium">Your request is live.</p>
                  <p className="text-sm text-gray-400 mt-1">
                    Others can see it on the map and donate.
                  </p>
                  <button
                    type="button"
                    onClick={onClose}
                    className="mt-6 px-6 py-2 rounded-xl bg-white/10 hover:bg-white/20 text-white"
                  >
                    Close
                  </button>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  );
}
