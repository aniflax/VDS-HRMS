export const getIsoDate = (value) => {
  if (!value) return null;
  if (value instanceof Date && !Number.isNaN(value.getTime())) {
    return `${value.getFullYear()}-${String(value.getMonth() + 1).padStart(2, '0')}-${String(value.getDate()).padStart(2, '0')}`;
  }

  const match = String(value).match(/^(\d{4})-(\d{2})-(\d{2})/);
  return match ? match[0] : null;
};

export const formatDisplayDate = (value, fallback = '--') => {
  const isoDate = getIsoDate(value);
  if (!isoDate) return fallback;

  const [year, month, day] = isoDate.split('-');
  return `${day}-${month}-${year}`;
};

export const IST_TIME_ZONE = 'Asia/Kolkata';

/**
 * Treat a backend-supplied timestamp string as Asia/Kolkata (IST). The
 * backend stores everything as a naive datetime in IST, so we have to
 * pin the timezone explicitly — otherwise `new Date(value)` would
 * interpret the naive string in the browser's local timezone (e.g. UTC
 * on a server-rendered page) and the displayed time would be off.
 */
const toIstDate = (value) => {
  const raw = String(value);
  // If the string already carries a timezone designator (Z or ±HH:MM
  // at the end), leave it alone.
  if (/Z$|[+-]\d{2}:?\d{2}$/.test(raw)) return new Date(raw);
  // Normalize a "YYYY-MM-DD HH:MM:SS" backend format to ISO and append
  // the IST offset so the JS Date is unambiguously IST.
  const iso = raw.includes('T') ? raw : raw.replace(' ', 'T');
  return new Date(`${iso}+05:30`);
};

export const formatDisplayDateTime = (value, fallback = '--') => {
  if (!value) return fallback;

  const date = toIstDate(value);
  if (Number.isNaN(date.getTime())) return fallback;

  const displayDate = formatDisplayDate(value, fallback);
  if (displayDate === fallback) return fallback;

  // 12-hour format with AM/PM, explicitly in IST. We also append "IST"
  // so the displayed time is unambiguous in any browser timezone.
  const time = date.toLocaleTimeString('en-IN', {
    timeZone: IST_TIME_ZONE,
    hour: 'numeric',
    minute: '2-digit',
    hour12: true,
  });
  return `${displayDate} ${time} IST`;
};

export const formatDisplayDateRange = (startDate, endDate, fallback = '--') => {
  const start = formatDisplayDate(startDate, fallback);
  const end = formatDisplayDate(endDate, fallback);
  if (start === fallback && end === fallback) return fallback;
  if (start === end) return start;
  return `${start} to ${end}`;
};
