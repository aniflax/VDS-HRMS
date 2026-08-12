const NOTIFY_COOLDOWN_MS = 24 * 60 * 60 * 1000;

export function notifyCooldownRemainingMs(request) {
  if (!request?.last_notified_at) return 0;
  const t = new Date(request.last_notified_at);
  if (Number.isNaN(t.getTime())) return 0;
  return Math.max(0, NOTIFY_COOLDOWN_MS - (Date.now() - t.getTime()));
}

export function formatRelativeFromNow(value) {
  if (!value) return null;
  const t = new Date(value);
  if (Number.isNaN(t.getTime())) return null;
  const diffMs = Date.now() - t.getTime();
  if (diffMs < 0) return 'just now';
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? '' : 's'} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? '' : 's'} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? '' : 's'} ago`;
}

export function formatRemainingCooldown(ms) {
  if (ms <= 0) return null;
  const minutes = Math.floor(ms / 60000);
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  const remMin = minutes % 60;
  if (hours < 24) return remMin ? `${hours}h ${remMin}m` : `${hours}h`;
  const days = Math.floor(hours / 24);
  const remH = hours % 24;
  return remH ? `${days}d ${remH}h` : `${days}d`;
}

export const LEAVE_NOTIFY_COOLDOWN_MS = NOTIFY_COOLDOWN_MS;
