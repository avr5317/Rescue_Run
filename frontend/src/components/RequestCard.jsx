import { motion } from 'framer-motion';
import { CATEGORY_COLORS } from './MapView';
import StatusBadge from './StatusBadge';
import LastUpdated from './LastUpdated';

const CATEGORY_ICONS = {
  meds: '💊',
  groceries: '🛒',
  shelter: '🏠',
  transport: '🚗',
  other: '📦',
};

const URGENCY_LABELS = {
  now: 'NOW',
  today: 'TODAY',
  week: 'WEEK',
};

const URGENCY_STYLES = {
  now: 'bg-red-500/90 text-white',
  today: 'bg-amber-500/90 text-white',
  week: 'bg-slate-500/80 text-white',
};

export default function RequestCard({ request, onClick, isSelected }) {
  const progress = Math.min(1, (request.progress ?? 0));
  const remaining = Math.max(0, (request.funding_goal ?? 0) - (request.funded_amount ?? 0));
  const categoryColor = CATEGORY_COLORS[request.category] || CATEGORY_COLORS.other;

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      style={{ borderLeftColor: categoryColor }}
      className={`
        rounded-2xl border border-white/10 bg-white/10 backdrop-blur-xl p-4 cursor-pointer
        transition-all duration-200 border-l-4
        ${isSelected ? 'ring-2 ring-emerald-400 shadow-lg' : 'hover:bg-white/15'}
      `}
      onClick={() => onClick?.(request)}
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-3 min-w-0">
          <span className="text-2xl flex-shrink-0" title={request.category}>
            {CATEGORY_ICONS[request.category] || CATEGORY_ICONS.other}
          </span>
          <div className="min-w-0">
            <span className="font-medium capitalize text-gray-100 truncate block">
              {request.category}
            </span>
            <span className="text-xs text-gray-400">
              ${(request.funded_amount ?? 0).toFixed(0)} / ${(request.funding_goal ?? 0).toFixed(0)}
            </span>
          </div>
        </div>
        <span
          className={`text-[10px] font-bold px-2 py-0.5 rounded-full flex-shrink-0 ${URGENCY_STYLES[request.urgency_window] ?? URGENCY_STYLES.week}`}
        >
          {URGENCY_LABELS[request.urgency_window] ?? 'WEEK'}
        </span>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <StatusBadge status={request.status} />
        <LastUpdated value={request.updated_at || request.created_at} />
      </div>

      <div className="mt-3">
        <div className="h-1.5 rounded-full bg-white/20 overflow-hidden">
          <motion.div
            className="h-full rounded-full bg-emerald-400"
            initial={false}
            animate={{ width: `${progress * 100}%` }}
            transition={{ duration: 0.5, ease: 'easeOut' }}
          />
        </div>
        <div className="flex flex-wrap items-center gap-1.5 mt-2">
          <span
            className="inline-flex items-center gap-1 text-[10px] text-gray-400 bg-white/10 rounded-full px-2 py-0.5 cursor-help"
            title="AI prioritized this request by urgency, severity, and funding gap — not profit."
          >
            Rank {(request.rank_score ?? 0).toFixed(2)} 💡
          </span>
          {request.severity >= 4 && (
            <span className="text-[10px] bg-amber-500/20 text-amber-200 rounded-full px-2 py-0.5">
              High need
            </span>
          )}
        </div>
        <div className="flex justify-between mt-1 text-xs text-gray-400">
          <span>${remaining.toFixed(0)} left</span>
        </div>
      </div>
    </motion.div>
  );
}

export function RequestCardSkeleton() {
  return (
    <div className="rounded-2xl border border-white/10 bg-white/5 backdrop-blur-xl p-4 animate-pulse">
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-white/20" />
        <div className="flex-1">
          <div className="h-4 w-24 bg-white/20 rounded" />
          <div className="h-3 w-16 mt-2 bg-white/10 rounded" />
        </div>
        <div className="h-5 w-12 rounded-full bg-white/20" />
      </div>
      <div className="mt-3 h-1.5 rounded-full bg-white/20" />
      <div className="flex justify-between mt-2">
        <div className="h-3 w-14 bg-white/10 rounded" />
        <div className="h-3 w-10 bg-white/10 rounded" />
      </div>
    </div>
  );
}
