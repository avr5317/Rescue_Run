import { deliverySteps, parseTimestamp, STATUS_LABELS } from '../utils/requestProgress';
import StatusBadge from './StatusBadge';
import LastUpdated from './LastUpdated';

function EventTime({ value }) {
  const date = parseTimestamp(value);
  return date ? <time dateTime={date.toISOString()} title={date.toLocaleString()}>
    {date.toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}
  </time> : <span>Time not recorded</span>;
}

export default function RequestProgress({ request, updating, onAdvance }) {
  const history = request.status_history || [];
  const steps = deliverySteps(request.status, history);
  const nextStatus = request.status === 'claimed' ? 'on_the_way'
    : request.status === 'on_the_way' ? 'delivered' : null;
  return (
    <section className="mb-4 rounded-2xl border border-white/10 bg-white/5 p-4" aria-label="Delivery progress">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold text-white text-sm">Delivery progress</h3>
        <StatusBadge status={request.status} />
      </div>
      <ol className="grid grid-cols-2 sm:grid-cols-4 gap-3 mt-4" aria-label="Delivery stages">
        {steps.map((step, index) => (
          <li key={step.key} aria-current={step.current ? 'step' : undefined} className="min-w-0">
            <span aria-hidden="true" className={`flex items-center justify-center h-7 w-7 rounded-full border text-xs font-bold ${
              step.current ? 'bg-sky-400/20 border-sky-300 text-sky-200'
                : step.reached ? 'bg-emerald-400/15 border-emerald-400/50 text-emerald-200'
                  : 'border-white/20 text-slate-500'
            }`}>{step.reached && !step.current ? '✓' : index + 1}</span>
            <p className={`mt-2 text-xs font-medium ${step.reached ? 'text-slate-100' : 'text-slate-500'}`}>{step.label}</p>
            {step.reached && <p className="mt-1 text-[10px] leading-relaxed text-slate-400"><EventTime value={step.at} /></p>}
          </li>
        ))}
      </ol>
      <div className="mt-4 border-t border-white/10 pt-3">
        <LastUpdated value={request.updated_at || request.created_at} />
        {request.is_claiming_helper && nextStatus && (
          <button type="button" disabled={updating} onClick={() => onAdvance(nextStatus)}
            className="mt-3 w-full rounded-xl bg-sky-500 px-4 py-3 text-sm font-semibold text-white hover:bg-sky-600 disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-sky-300">
            {updating ? 'Updating…' : nextStatus === 'on_the_way' ? 'Mark on the way' : 'Mark delivered'}
          </button>
        )}
        {!request.is_claiming_helper && nextStatus && <p className="mt-2 text-xs text-slate-400">The assigned helper can update delivery progress.</p>}
        {request.status === 'delivered' && <p className="mt-2 text-xs text-emerald-200">Marked delivered by the helper.</p>}
        {request.status === 'cancelled' && <p className="mt-2 text-xs text-slate-400">This request has been cancelled.</p>}
      </div>
      {history.length > 0 && <details className="mt-3 text-xs text-slate-300">
        <summary className="cursor-pointer py-1">Status history</summary>
        <ol className="mt-2 space-y-2 border-l border-white/15 pl-3">
          {history.map((event, index) => <li key={`${event.status}-${index}`} className="flex flex-wrap justify-between gap-1">
            <span>{STATUS_LABELS[event.status] || event.status}</span>
            <span className="text-slate-400"><EventTime value={event.at} /></span>
          </li>)}
        </ol>
      </details>}
    </section>
  );
}
