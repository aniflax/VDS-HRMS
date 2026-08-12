import React, { useState } from 'react';
import { Button, Tooltip, CircularProgress, Box } from '@mui/material';
import api from '../../api/axios';
import { notifyCooldownRemainingMs, formatRelativeFromNow, formatRemainingCooldown } from './leaveNotify';

export default function LeaveNotifyButton({ request, targetRole, onNotified, size = 'small', variant = 'outlined' }) {
  const [busy, setBusy] = useState(false);
  const cooldownMs = notifyCooldownRemainingMs(request);
  const onCooldown = cooldownMs > 0;
  const lastLabel = request?.last_notified_at
    ? formatRelativeFromNow(request.last_notified_at)
    : null;

  const handleClick = async (e) => {
    e.stopPropagation();
    setBusy(true);
    try {
      const res = await api.post(`/api/leave/notify/${request.id}`);
      if (onNotified) onNotified(res.data);
    } catch (err) {
      if (onNotified) onNotified({ error: err.response?.data?.detail || 'Failed to send notification.' });
    } finally {
      setBusy(false);
    }
  };

  if (onCooldown) {
    return (
      <Tooltip title={`Notified ${lastLabel} — available again in ${formatRemainingCooldown(cooldownMs)}`} arrow>
        <span>
          <Button
            size={size}
            variant="outlined"
            color="warning"
            disabled
            sx={{ whiteSpace: 'nowrap' }}
          >
            Notified {lastLabel || 'recently'}
          </Button>
        </span>
      </Tooltip>
    );
  }

  return (
    <Button
      size={size}
      variant={variant}
      color="warning"
      onClick={handleClick}
      disabled={busy}
      sx={{ whiteSpace: 'nowrap' }}
    >
      {busy ? (
        <Box sx={{ display: 'inline-flex', alignItems: 'center', gap: 0.5 }}>
          <CircularProgress size={12} /> Sending...
        </Box>
      ) : (
        `Notify ${targetRole}`
      )}
    </Button>
  );
}
