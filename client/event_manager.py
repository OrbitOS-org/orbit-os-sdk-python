"""EventManager: system-wide event subscription."""
from __future__ import annotations

from typing import Generator

import grpc

from api.event_service.v26 import event_service_pb2 as event_pb2
from api.event_service.v26.event_service_pb2_grpc import EventServiceStub

from .config import get_rpc_timeout

# Re-export EventType enum class and all constants for convenience
EventType = event_pb2.EventType

EVENT_TYPE_UNKNOWN = event_pb2.EVENT_TYPE_UNKNOWN
EVENT_APP_INSTALLED = event_pb2.EVENT_APP_INSTALLED
EVENT_APP_REMOVED = event_pb2.EVENT_APP_REMOVED
EVENT_APP_UPDATED = event_pb2.EVENT_APP_UPDATED
EVENT_APP_STARTED = event_pb2.EVENT_APP_STARTED
EVENT_APP_STOPPED = event_pb2.EVENT_APP_STOPPED
EVENT_APP_CRASHED = event_pb2.EVENT_APP_CRASHED
EVENT_APP_REJECTED = event_pb2.EVENT_APP_REJECTED
EVENT_SYSTEM_REBOOT = event_pb2.EVENT_SYSTEM_REBOOT
EVENT_SYSTEM_SHUTDOWN = event_pb2.EVENT_SYSTEM_SHUTDOWN
EVENT_SYSTEM_FACTORY_RESET = event_pb2.EVENT_SYSTEM_FACTORY_RESET
EVENT_SYSTEM_TIME_CHANGED = event_pb2.EVENT_SYSTEM_TIME_CHANGED
EVENT_SYSTEM_TIMEZONE_CHANGED = event_pb2.EVENT_SYSTEM_TIMEZONE_CHANGED
EVENT_NET_UP = event_pb2.EVENT_NET_UP
EVENT_NET_DOWN = event_pb2.EVENT_NET_DOWN
EVENT_NET_WIFI_CONNECTED = event_pb2.EVENT_NET_WIFI_CONNECTED
EVENT_NET_WIFI_DISCONNECTED = event_pb2.EVENT_NET_WIFI_DISCONNECTED
EVENT_NET_ETH_CONNECTED = event_pb2.EVENT_NET_ETH_CONNECTED
EVENT_NET_ETH_DISCONNECTED = event_pb2.EVENT_NET_ETH_DISCONNECTED
EVENT_NET_CELLULAR_CONNECTED = event_pb2.EVENT_NET_CELLULAR_CONNECTED
EVENT_NET_CELLULAR_DISCONNECTED = event_pb2.EVENT_NET_CELLULAR_DISCONNECTED
EVENT_STORAGE_LOW = event_pb2.EVENT_STORAGE_LOW
EVENT_STORAGE_CRITICAL = event_pb2.EVENT_STORAGE_CRITICAL
EVENT_POWER_LOW_BATTERY = event_pb2.EVENT_POWER_LOW_BATTERY
EVENT_POWER_CRITICAL_BATTERY = event_pb2.EVENT_POWER_CRITICAL_BATTERY
EVENT_POWER_CHARGING = event_pb2.EVENT_POWER_CHARGING
EVENT_POWER_DISCHARGING = event_pb2.EVENT_POWER_DISCHARGING
EVENT_THERMAL_THROTTLE = event_pb2.EVENT_THERMAL_THROTTLE
EVENT_THERMAL_CRITICAL = event_pb2.EVENT_THERMAL_CRITICAL
EVENT_UPDATE_AVAILABLE = event_pb2.EVENT_UPDATE_AVAILABLE
EVENT_UPDATE_COMPLETE = event_pb2.EVENT_UPDATE_COMPLETE
EVENT_UPDATE_FAILED = event_pb2.EVENT_UPDATE_FAILED

# EVENT_SYSTEM_UPDATE was removed from the proto; kept as an alias of EVENT_UPDATE_COMPLETE.
EVENT_SYSTEM_UPDATE = EVENT_UPDATE_COMPLETE


class EventManager:
    """Subscribe to system events emitted by the Gravity runtime."""

    def __init__(self, channel: grpc.Channel) -> None:
        self._stub = EventServiceStub(channel)

    def subscribe(self, *event_types: "event_pb2.EventType.ValueType", timeout: float | None = None) -> Generator:
        """Open a server-side event stream and yield ``Event`` proto messages.

        Args:
            *event_types: Filter to specific ``EVENT_*`` constants.
                Pass no arguments to receive all event types.
            timeout: Stream idle timeout in seconds (``None`` = no timeout).

        Example::

            # All events
            for event in client.event_manager.subscribe():
                print(event.type, event.payload)
                if done:
                    break

            # Filtered
            for event in client.event_manager.subscribe(EVENT_APP_CRASHED, EVENT_NET_DOWN):
                alert(event)
        """
        req = event_pb2.SubscribeRequest(types=list(event_types))
        stream = self._stub.Subscribe(req, timeout=timeout)
        try:
            for event in stream:
                yield event
        finally:
            stream.cancel()
