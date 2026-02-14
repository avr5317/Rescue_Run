import { useEffect, useState } from 'react';
import { parseTimestamp, relativeTime } from '../utils/requestProgress';

export default function LastUpdated({ value, className = '' }) {
  const [now, setNow] = useState(Date.now());
  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 30000);
    return () => clearInterval(timer);
  }, []);
  const date = parseTimestamp(value);
  return (
    <span className={`text-xs text-slate-400 ${className}`}>
      Last updated{' '}
      {date ? <time dateTime={date.toISOString()} title={date.toLocaleString()}>
        {relativeTime(value, now)}
      </time> : 'time unavailable'}
    </span>
  );
}
