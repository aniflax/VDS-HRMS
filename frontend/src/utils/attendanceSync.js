import { getApiBaseURL } from '../api/axios';

export const ATTENDANCE_SYNC_EVENT = 'attendance:changed';
export const ATTENDANCE_SYNC_STORAGE_KEY = 'hrms.attendance.sync.v1';

export const notifyAttendanceChanged = (detail = {}) => {
  if (typeof window === 'undefined') {
    return;
  }

  const payload = {
    ...detail,
    at: new Date().toISOString(),
  };

  window.dispatchEvent(new CustomEvent(ATTENDANCE_SYNC_EVENT, { detail: payload }));

  try {
    localStorage.setItem(ATTENDANCE_SYNC_STORAGE_KEY, JSON.stringify(payload));
  } catch {
    // Ignore storage failures; the in-tab event still covers the current session.
  }
};

export const connectAttendanceStream = (onEvent) => {
  if (typeof window === 'undefined' || typeof fetch === 'undefined' || typeof ReadableStream === 'undefined') {
    return () => {};
  }

  const controller = new AbortController();
  let stopped = false;
  let retryTimer = null;

  const getToken = () => {
    try {
      return localStorage.getItem('token');
    } catch {
      return null;
    }
  };

  const parseEventBlock = (block) => {
    const event = { event: 'message', data: '' };
    block.replace(/\r\n/g, '\n').split('\n').forEach((line) => {
      if (!line || line.startsWith(':')) {
        return;
      }
      const colonIndex = line.indexOf(':');
      const field = colonIndex === -1 ? line : line.slice(0, colonIndex);
      const value = colonIndex === -1 ? '' : line.slice(colonIndex + 1).replace(/^ /, '');
      if (field === 'event') {
        event.event = value || 'message';
      } else if (field === 'data') {
        event.data = `${event.data}${event.data ? '\n' : ''}${value}`;
      }
    });
    return event;
  };

  const dispatchBlock = (block) => {
    const parsed = parseEventBlock(block);
    if (parsed.event !== 'attendance') {
      return;
    }
    try {
      onEvent(parsed.data ? JSON.parse(parsed.data) : {});
    } catch {
      onEvent({});
    }
  };

  const connect = async () => {
    while (!stopped) {
      try {
        const token = getToken();
        const headers = {
          Accept: 'text/event-stream',
          'Cache-Control': 'no-cache',
        };
        if (token) {
          headers.Authorization = `Bearer ${token}`;
        }

        const streamBase = getApiBaseURL();
        const streamUrl = `${streamBase || ''}/api/attendance/stream`;

        const response = await fetch(streamUrl, {
          method: 'GET',
          headers,
          signal: controller.signal,
          cache: 'no-store',
        });

        if (!response.ok || !response.body) {
          throw new Error(`Attendance stream unavailable (${response.status})`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = '';

        while (!stopped) {
          const { value, done } = await reader.read();
          if (done) {
            break;
          }

          buffer += decoder.decode(value, { stream: true }).replace(/\r\n/g, '\n');
          let boundaryIndex = buffer.indexOf('\n\n');
          while (boundaryIndex !== -1) {
            const block = buffer.slice(0, boundaryIndex).trim();
            buffer = buffer.slice(boundaryIndex + 2);
            if (block) {
              dispatchBlock(block);
            }
            boundaryIndex = buffer.indexOf('\n\n');
          }
        }
      } catch {
        if (stopped) {
          break;
        }
        await new Promise((resolve) => {
          retryTimer = setTimeout(resolve, 3000);
        });
      }
    }
  };

  connect();

  return () => {
    stopped = true;
    controller.abort();
    if (retryTimer) {
      clearTimeout(retryTimer);
    }
  };
};
