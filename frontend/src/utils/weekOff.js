const DAY_NAME_TO_NUM = { Sunday: 0, Monday: 1, Tuesday: 2, Wednesday: 3, Thursday: 4, Friday: 5, Saturday: 6 };

const formatLocalDate = (value) => {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
};

export const getWeekSunday = (dateStr) => {
  const [y, m, d] = dateStr.split('-').map(Number);
  if (![y, m, d].every(Boolean)) return null;
  const dt = new Date(y, m - 1, d);
  return formatLocalDate(new Date(y, m - 1, d - dt.getDay()));
};

export const getDefaultWeekOffDate = (anchorDateStr, defaultWeekOff) => {
  const sunday = getWeekSunday(anchorDateStr);
  if (!sunday) return null;
  const [sy, sm, sd] = sunday.split('-').map(Number);
  const dayOffset = DAY_NAME_TO_NUM[defaultWeekOff || 'Sunday'] ?? 0;
  return formatLocalDate(new Date(sy, sm - 1, sd + dayOffset));
};

export const getTargetDefaultForSwap = (swapDateStr, defaultWeekOff) => {
  const sameWeekDefault = getDefaultWeekOffDate(swapDateStr, defaultWeekOff);
  if (!sameWeekDefault) return null;
  if (swapDateStr < sameWeekDefault) return sameWeekDefault;
  const [y, m, d] = sameWeekDefault.split('-').map(Number);
  return formatLocalDate(new Date(y, m - 1, d + 7));
};
