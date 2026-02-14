export const STATUS_LABELS = {
  open: 'Open', funded: 'Funded · awaiting helper', claimed: 'Claimed',
  on_the_way: 'On the way', delivered: 'Delivered', cancelled: 'Cancelled',
};

export function parseTimestamp(value) {
  if (!value) return null;
  // Historical MongoDB values may be serialized as naive UTC datetimes.
  const normalized = typeof value === 'string' && !/(Z|[+-]\d{2}:?\d{2})$/i.test(value)
    ? `${value}Z` : value;
  const date = new Date(normalized);
  return Number.isNaN(date.getTime()) ? null : date;
}

export function relativeTime(value, now = Date.now()) {
  const date = parseTimestamp(value);
  if (!date) return 'time unavailable';
  const seconds = Math.max(0, Math.floor((now - date.getTime()) / 1000));
  if (seconds < 60) return 'just now';
  const minutes = Math.floor(seconds / 60);
  if (minutes < 60) return `${minutes} ${minutes === 1 ? 'minute' : 'minutes'} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} ${hours === 1 ? 'hour' : 'hours'} ago`;
  const days = Math.floor(hours / 24);
  return `${days} ${days === 1 ? 'day' : 'days'} ago`;
}

export function deliverySteps(status, history = []) {
  const current = status === 'funded' ? 'open' : status;
  return [
    ['open', 'Posted'], ['claimed', 'Claimed'],
    ['on_the_way', 'On the way'], ['delivered', 'Delivered'],
  ].map(([key, label]) => {
    const event = history.find((item) => item.status === key);
    return { key, label, at: event?.at, reached: Boolean(event) || current === key,
      current: current === key };
  });
}
