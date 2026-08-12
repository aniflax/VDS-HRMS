import { describe, expect, it } from 'vitest';
import { formatDisplayDate, formatDisplayDateRange, formatDisplayDateTime, getIsoDate } from '../../src/utils/dateFormat.js';

describe('dateFormat', () => {
  it('extracts an ISO date from date-only and datetime values', () => {
    expect(getIsoDate('2026-05-02')).toBe('2026-05-02');
    expect(getIsoDate('2026-05-02T10:30:00Z')).toBe('2026-05-02');
  });

  it('formats screen dates as DD-MM-YYYY', () => {
    expect(formatDisplayDate('2026-05-02')).toBe('02-05-2026');
    expect(formatDisplayDate('2026-05-02T10:30:00Z')).toBe('02-05-2026');
  });

  it('formats date ranges with the same DD-MM-YYYY standard', () => {
    expect(formatDisplayDateRange('2026-05-02', '2026-05-04')).toBe('02-05-2026 to 04-05-2026');
    expect(formatDisplayDateRange('2026-05-02', '2026-05-02')).toBe('02-05-2026');
  });

  it('keeps datetime displays date-first', () => {
    expect(formatDisplayDateTime('2026-05-02T10:30:00')).toMatch(/^02-05-2026 /);
  });
});
