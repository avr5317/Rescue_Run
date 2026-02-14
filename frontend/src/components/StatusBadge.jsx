import { STATUS_LABELS } from '../utils/requestProgress';

const STYLES = {
  open: 'bg-slate-500/20 text-slate-200',
  funded: 'bg-emerald-500/15 text-emerald-200',
  claimed: 'bg-amber-500/15 text-amber-200',
  on_the_way: 'bg-sky-500/15 text-sky-200',
  delivered: 'bg-emerald-500/20 text-emerald-200',
  cancelled: 'bg-slate-500/20 text-slate-400',
};

export default function StatusBadge({ status }) {
  return <span className={`inline-flex rounded-full px-2.5 py-1 text-xs font-medium ${STYLES[status] || STYLES.open}`}>
    {STATUS_LABELS[status] || status || 'Unknown status'}
  </span>;
}
