from __future__ import annotations

from queue import Queue
from threading import Lock
from typing import Dict, Set, Any

_lock = Lock()
_subscribers: Set[Queue] = set()


def register_attendance_subscriber() -> Queue:
    queue: Queue = Queue()
    with _lock:
        _subscribers.add(queue)
    return queue


def unregister_attendance_subscriber(queue: Queue) -> None:
    with _lock:
        _subscribers.discard(queue)


def broadcast_attendance_change(payload: Dict[str, Any]) -> None:
    with _lock:
        subscribers = list(_subscribers)

    for queue in subscribers:
        try:
            queue.put_nowait(payload)
        except Exception:
            continue
