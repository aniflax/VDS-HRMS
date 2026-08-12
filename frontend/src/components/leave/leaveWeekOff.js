const DAY_NAME_TO_NUM = { Sunday: 0, Monday: 1, Tuesday: 2, Wednesday: 3, Thursday: 4, Friday: 5, Saturday: 6 };

export function getEffectiveWeekOffDay(dateStr, fallbackWeekOff, weekOffHistory = []) {
  const sortedHistory = [...(weekOffHistory || [])]
    .filter((entry) => entry?.week_off_day && entry?.effective_from)
    .sort((a, b) => String(a.effective_from).localeCompare(String(b.effective_from)));
  let effectiveDay = fallbackWeekOff || 'Sunday';
  sortedHistory.forEach((entry) => {
    const effectiveFrom = String(entry.effective_from).slice(0, 10);
    if (effectiveFrom && effectiveFrom <= dateStr) {
      effectiveDay = entry.week_off_day;
    }
  });
  return effectiveDay;
}

export const WEEK_OFF_DAY_NAME_TO_NUM = DAY_NAME_TO_NUM;
