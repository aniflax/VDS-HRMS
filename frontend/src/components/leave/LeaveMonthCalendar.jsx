import React, { useMemo } from 'react';
import {
  Box,
  Paper,
  Typography,
  IconButton,
  Select,
  MenuItem,
  Tooltip,
} from '@mui/material';
import ChevronLeftIcon from '@mui/icons-material/ChevronLeft';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import CalendarMonthIcon from '@mui/icons-material/CalendarMonth';
import { getTargetDefaultForSwap } from '../../utils/weekOff';
import { getEffectiveWeekOffDay } from './leaveWeekOff';

const DAY_NAME_TO_NUM = { Sunday: 0, Monday: 1, Tuesday: 2, Wednesday: 3, Thursday: 4, Friday: 5, Saturday: 6 };
const MONTHS = [
  'January', 'February', 'March', 'April', 'May', 'June',
  'July', 'August', 'September', 'October', 'November', 'December',
];

const WEEK_OFF_COLOR_APPROVED = '#8d6e63';
const WEEK_OFF_COLOR_PENDING = '#a1887f';

const LEAVE_STATUS_COLOR = {
  APPROVED: '#2e7d32',
  PENDING: '#e65100',
  HOD_APPROVED: '#e65100',
  REJECTED: '#c62828',
  CANCELLED: '#455a64',
};

const LEGEND = [
  [LEAVE_STATUS_COLOR.APPROVED, 'Approved'],
  [LEAVE_STATUS_COLOR.PENDING, 'Pending'],
  [LEAVE_STATUS_COLOR.REJECTED, 'Rejected'],
  [LEAVE_STATUS_COLOR.CANCELLED, 'Cancelled'],
  [WEEK_OFF_COLOR_APPROVED, 'Week Off'],
  [WEEK_OFF_COLOR_PENDING, 'Week Off (Pending)'],
];

function isWeekOffRequest(request) {
  return (request?.leave_type_name || '').toLowerCase() === 'week off';
}

function formatLocalDate(value) {
  const year = value.getFullYear();
  const month = String(value.getMonth() + 1).padStart(2, '0');
  const day = String(value.getDate()).padStart(2, '0');
  return `${year}-${month}-${day}`;
}

function buildWeekOffState(requests, defaultWeekOff, weekOffHistory = []) {
  const approvedWeekOffDates = new Set();
  const pendingWeekOffDates = new Set();
  const approvedReplacedDefaultDates = new Set();
  const weekOffRequestsByDate = {};

  const addDates = (r, targetSet) => {
    if (!r.start_date || !r.end_date) return;
    const [sy, sm, sd] = r.start_date.split('-').map(Number);
    const [ey, em, ed] = r.end_date.split('-').map(Number);
    if (![sy, sm, sd, ey, em, ed].every((n) => Number.isFinite(n))) return;
    let cur = new Date(sy, sm - 1, sd);
    const end = new Date(ey, em - 1, ed);
    while (cur <= end) {
      const ds = formatLocalDate(cur);
      targetSet.add(ds);
      if (!weekOffRequestsByDate[ds]) weekOffRequestsByDate[ds] = [];
      weekOffRequestsByDate[ds].push(r);
      cur.setDate(cur.getDate() + 1);
    }
  };

  requests.filter(isWeekOffRequest).forEach((r) => {
    if (r.status === 'APPROVED') {
      addDates(r, approvedWeekOffDates);
      const replacedDefault = getTargetDefaultForSwap(r.start_date, defaultWeekOff);
      if (replacedDefault) approvedReplacedDefaultDates.add(replacedDefault);
    } else if (r.status === 'PENDING' || r.status === 'HOD_APPROVED') {
      addDates(r, pendingWeekOffDates);
    }
  });

  const isWeekOffDate = (dateStr) => {
    if (approvedWeekOffDates.has(dateStr)) return 'approved';
    if (pendingWeekOffDates.has(dateStr)) return 'pending';
    if (approvedReplacedDefaultDates.has(dateStr)) return false;
    const [y, m, d] = dateStr.split('-').map(Number);
    if (![y, m, d].every((n) => Number.isFinite(n))) return false;
    const dt = new Date(y, m - 1, d);
    const defaultWONum = DAY_NAME_TO_NUM[getEffectiveWeekOffDay(dateStr, defaultWeekOff, weekOffHistory)] ?? 0;
    if (dt.getDay() !== defaultWONum) return false;
    const sunOffset = dt.getDay();
    for (let i = 0; i < 7; i += 1) {
      const check = new Date(y, m - 1, d - sunOffset + i);
      const ds = formatLocalDate(check);
      if (approvedWeekOffDates.has(ds)) return false;
    }
    return 'approved';
  };

  return { isWeekOffDate, weekOffRequestsByDate };
}

function buildDateMap(requests) {
  const dateMap = {};
  [...requests]
    .filter((r) => r && r.start_date && r.end_date)
    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
    .forEach((r) => {
      const [sy, sm, sd] = r.start_date.split('-').map(Number);
      const [ey, em, ed] = r.end_date.split('-').map(Number);
      if (![sy, sm, sd, ey, em, ed].every((n) => Number.isFinite(n))) return;
      let cur = new Date(sy, sm - 1, sd);
      const end = new Date(ey, em - 1, ed);
      while (cur <= end) {
        const key = formatLocalDate(cur);
        if (!dateMap[key]) dateMap[key] = [];
        dateMap[key].push(r);
        cur.setDate(cur.getDate() + 1);
      }
    });
  return dateMap;
}

function getLeaveTypeAbbrev(name) {
  if (!name) return 'LV';
  const normalized = name.toLowerCase();
  if (normalized.includes('casual')) return 'CL';
  if (normalized.includes('sick')) return 'SL';
  if (normalized.includes('earned') || normalized.includes('privilege')) return 'EL';
  if (normalized.includes('maternity')) return 'ML';
  if (normalized.includes('paternity')) return 'PL';
  if (normalized.includes('week off')) return 'WO';
  const words = name.split(/\s+/).filter(Boolean);
  return (words.length > 1 ? words.map((word) => word[0]).join('') : name.slice(0, 2)).toUpperCase();
}

export default function LeaveMonthCalendar({
  requests = [],
  viewDate,
  setViewDate,
  defaultWeekOff = 'Sunday',
  weekOffHistory = [],
  onCellClick,
  renderLabel,
  showLegend = true,
}) {
  const year = viewDate.getFullYear();
  const month = viewDate.getMonth();
  const today = new Date();
  const todayIso = formatLocalDate(today);

  const dateMap = useMemo(() => buildDateMap(requests), [requests]);
  const { isWeekOffDate, weekOffRequestsByDate } = useMemo(
    () => buildWeekOffState(requests, defaultWeekOff, weekOffHistory),
    [requests, defaultWeekOff, weekOffHistory],
  );

  const firstDay = new Date(year, month, 1).getDay();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const totalCells = firstDay + daysInMonth;
  const totalWeeks = Math.ceil(totalCells / 7);

  const prevMonth = () => {
    const d = new Date(year, month - 1, 1);
    setViewDate(d);
  };
  const nextMonth = () => {
    const d = new Date(year, month + 1, 1);
    setViewDate(d);
  };

  const renderTooltip = (dayReqs, isWO, woStatus) => {
    if (isWO) {
      return (
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, p: 0.5 }}>
          <Typography sx={{ fontSize: '0.75rem', fontWeight: 600 }}>
            • Week Off{woStatus === 'pending' ? ' (Pending)' : ''}
          </Typography>
          {/* {onCellClick && (
            <Typography sx={{ fontSize: '0.7rem', opacity: 0.85 }}>
              Click to view leave request
            </Typography>
          )} */}
        </Box>
      );
    }
    return (
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 0.5, p: 0.5 }}>
        {dayReqs.map((r, i) => (
          <Typography key={i} sx={{ fontSize: '0.75rem', fontWeight: 600 }}>
            • {r.leave_type_name}: {r.status}
          </Typography>
        ))}
      </Box>
    );
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems={{ xs: 'stretch', sm: 'center' }} mb={3} flexWrap="wrap" gap={2} flexDirection={{ xs: 'column', sm: 'row' }}>
        <Box display="flex" alignItems="center" gap={1} flexWrap="wrap">
          <CalendarMonthIcon color="primary" />
          <Typography variant="h6" fontWeight="bold">{MONTHS[month]} {year}</Typography>
          <IconButton size="small" onClick={prevMonth} sx={{ border: '1px solid #eee', ml: 1 }}><ChevronLeftIcon /></IconButton>
          <IconButton size="small" onClick={nextMonth} sx={{ border: '1px solid #eee' }}><ChevronRightIcon /></IconButton>
        </Box>
        <Box display="flex" gap={1} sx={{ '& .MuiInputBase-root': { flex: 1 } }}>
          <Select size="small" value={month} onChange={(e) => setViewDate(new Date(year, Number(e.target.value), 1))} sx={{ borderRadius: 2, bgcolor: 'white', minWidth: { xs: 0, sm: 150 } }}>
            {MONTHS.map((m, i) => <MenuItem key={i} value={i}>{m}</MenuItem>)}
          </Select>
          <Select size="small" value={year} onChange={(e) => setViewDate(new Date(Number(e.target.value), month, 1))} sx={{ borderRadius: 2, bgcolor: 'white', minWidth: { xs: 0, sm: 100 } }}>
            {[year - 1, year, year + 1].map((y) => <MenuItem key={y} value={y}>{y}</MenuItem>)}
          </Select>
        </Box>
      </Box>

      <Paper sx={{ p: 0, borderRadius: 3, border: '1px solid #e0e0e0', boxShadow: '0 4px 16px rgba(0,0,0,0.06)', mb: 4, overflow: 'hidden' }}>
        <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(7, minmax(0, 1fr))', background: 'linear-gradient(135deg, #f47c20 0%, #d66a18 100%)' }}>
          {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map((d, idx) => {
            const isTodayCol = today.getDay() === idx && month === today.getMonth() && year === today.getFullYear();
            return (
              <Box key={d} sx={{ textAlign: 'center', py: 1.25, bgcolor: isTodayCol ? 'rgba(255,255,255,0.18)' : 'transparent', borderRight: idx < 6 ? '1px solid rgba(255,255,255,0.12)' : 'none' }}>
                <Typography sx={{ fontSize: '0.72rem', fontWeight: 800, color: 'rgba(255,255,255,0.8)', letterSpacing: '0.08em', textTransform: 'uppercase' }}>{d}</Typography>
              </Box>
            );
          })}
        </Box>

        <Box sx={{ p: 1.5 }}>
          {Array.from({ length: totalWeeks }).map((_, week) => (
            <Box key={week} sx={{ display: 'grid', gridTemplateColumns: 'repeat(7, minmax(0, 1fr))' }}>
              {Array.from({ length: 7 }).map((_, dow) => {
                const cellIdx = week * 7 + dow;
                const day = cellIdx - firstDay + 1;
                const isValid = day >= 1 && day <= daysInMonth;

                if (!isValid) {
                  return <Box key={dow} sx={{ p: 0.5 }}><Box sx={{ height: 85, bgcolor: '#fafafa', borderRadius: 1.5 }} /></Box>;
                }

                const dateStr = `${year}-${String(month + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
                const dayReqs = (dateMap[dateStr] || []).filter((r) => r.leave_type_name !== 'Week Off');
                const isToday = dateStr === todayIso && month === today.getMonth() && year === today.getFullYear();
                const woStatus = isWeekOffDate(dateStr);
                const isWO = !!woStatus;

                const primaryReq = dayReqs[0] ?? null;
                const primaryWeekOffReq = isWO ? (weekOffRequestsByDate[dateStr]?.[0] ?? null) : null;
                const cellColor = isWO
                  ? (woStatus === 'pending' ? WEEK_OFF_COLOR_PENDING : WEEK_OFF_COLOR_APPROVED)
                  : primaryReq ? LEAVE_STATUS_COLOR[primaryReq.status] || '#607d8b' : null;
                const hasCell = !!primaryReq || isWO;
                const clickableReq = primaryReq || primaryWeekOffReq;
                const isClickable = !!onCellClick && !!clickableReq;

                return (
                  <Box key={dow} sx={{ p: 0.375, minWidth: 0 }}>
                    <Tooltip
                      title={hasCell ? renderTooltip(dayReqs, isWO, woStatus) : ''}
                      arrow
                      disableHoverListener={!hasCell}
                    >
                      <Box
                        role={isClickable ? 'button' : undefined}
                        tabIndex={isClickable ? 0 : -1}
                        onClick={isClickable ? () => onCellClick(clickableReq) : undefined}
                        onKeyDown={isClickable ? (e) => {
                          if (e.key === 'Enter' || e.key === ' ') {
                            e.preventDefault();
                            onCellClick(clickableReq);
                          }
                        } : undefined}
                        sx={{
                          height: 85, borderRadius: 1.5, p: 0.75,
                          display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
                          bgcolor: hasCell ? cellColor : isToday ? 'rgba(244,124,32,0.08)' : 'transparent',
                          border: isToday
                            ? `2.5px solid ${hasCell ? '#fff8' : '#f47c20'}`
                            : hasCell ? `1px solid ${cellColor}cc` : '1px solid transparent',
                          cursor: isClickable ? 'pointer' : 'default',
                          transition: 'all 0.15s',
                          boxShadow: hasCell ? 'inset 0 0 0 1000px rgba(0,0,0,0.08)' : 'none',
                          overflow: 'hidden',
                          '&:hover': hasCell ? {
                            boxShadow: 'inset 0 0 0 1000px rgba(0,0,0,0.18)',
                            transform: 'scale(1.02)',
                          } : {},
                          '&:focus-visible': isClickable ? {
                            outline: '2px solid #f47c20',
                            outlineOffset: 2,
                          } : {},
                        }}
                      >
                        <Box sx={{ width: 26, height: 26, borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: isToday && !hasCell ? '#f47c20' : 'transparent', mb: 0.5 }}>
                          <Typography sx={{ fontSize: '0.85rem', fontWeight: 'bold', color: hasCell || isToday ? 'white' : 'text.primary' }}>{day}</Typography>
                        </Box>
                        {isWO ? (
                          <Typography sx={{ fontSize: '0.65rem', fontWeight: 800, color: 'rgba(255,255,255,0.9)', textAlign: 'center', lineHeight: 1.3, maxWidth: '100%', overflowWrap: 'anywhere' }}>
                            {woStatus === 'pending' ? 'Week Off?' : 'Week Off'}
                          </Typography>
                        ) : primaryReq ? (
                          <Typography sx={{ fontSize: '0.68rem', fontWeight: 800, color: 'white', textAlign: 'center', lineHeight: 1.3, px: 0.5, maxWidth: '100%', overflowWrap: 'anywhere' }}>
                            {renderLabel ? renderLabel(primaryReq) : getLeaveTypeAbbrev(primaryReq.leave_type_name)}
                          </Typography>
                        ) : (
                          <Box sx={{ height: '1.3em' }} />
                        )}
                      </Box>
                    </Tooltip>
                  </Box>
                );
              })}
            </Box>
          ))}
        </Box>

        {showLegend && (
          <Box display="flex" gap={2} mt={0} px={2} pb={2} flexWrap="wrap" justifyContent="center">
            {LEGEND.map(([color, label]) => (
              <Box key={label} display="flex" alignItems="center" gap={0.75}>
                <Box sx={{ width: 14, height: 14, borderRadius: '3px', bgcolor: color }} />
                <Typography variant="caption" color="text.secondary" fontWeight={500}>{label}</Typography>
              </Box>
            ))}
          </Box>
        )}
      </Paper>
    </Box>
  );
}
