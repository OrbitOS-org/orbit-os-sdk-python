"""MobileNotificationManager: push notifications to the user's phone."""
from __future__ import annotations

from typing import Any, Mapping

import grpc

from api.common import types_pb2
from api.mobile_notification_service.v26 import mobile_notification_service_pb2 as notif_pb2
from api.mobile_notification_service.v26.mobile_notification_service_pb2_grpc import MobileNotificationServiceStub

from .config import get_rpc_timeout


def _check_error(resp: Any, op_name: str) -> None:
    if resp.error.code != types_pb2.ERROR_CODE_NONE:
        raise RuntimeError(f"{op_name}: {resp.error.message or 'unknown error'}")


class MobileNotificationManager:
    """Send push notifications to the mobile devices of the device's user.

    The device never talks to the cloud itself — calls are forwarded through
    the runtime to the Settings app, which holds the credentials.
    """

    def __init__(self, channel: grpc.Channel) -> None:
        self._stub = MobileNotificationServiceStub(channel)

    def send(
        self,
        body: str,
        image_url: str = "",
        data: Mapping[str, str] | None = None,
        collapse_key: str = "",
        ttl_seconds: int = 0,
    ) -> tuple[int, int]:
        """Send a push notification to the user's phone.

        There is no title parameter: the runtime always sets the title itself,
        as ``"<device name> · <this app's display name>"``, resolved from this
        app's identity — one app can never spoof another in a notification.

        Args:
            body: Notification text (required).
            image_url: Optional image shown in the notification.
            data: Key/value payload delivered to the mobile app (deep-linking, etc.).
            collapse_key: Replaces any pending notification with the same key.
            ttl_seconds: How long the notification is held if the phone is offline.

        Returns:
            Tuple of ``(sent, failed)`` recipient device counts.

        Raises:
            RuntimeError: if the runtime reports an error (e.g. notifications disabled).
        """
        req = notif_pb2.SendMobileNotificationRequest(
            body=body,
            image_url=image_url,
            data=dict(data or {}),
            collapse_key=collapse_key,
            ttl_seconds=ttl_seconds,
        )
        resp = self._stub.Send(req, timeout=get_rpc_timeout())
        _check_error(resp, "send")
        return resp.sent, resp.failed

    def set_enabled(self, enabled: bool) -> None:
        """Turn push notifications on/off for the whole device (persisted).

        When disabled, :meth:`send` fails immediately for every app, not just the caller.
        """
        resp = self._stub.SetEnabled(notif_pb2.SetEnabledRequest(enabled=enabled), timeout=get_rpc_timeout())
        _check_error(resp, "set_enabled")

    def is_enabled(self) -> bool:
        """Return the current state set by :meth:`set_enabled`."""
        resp = self._stub.IsEnabled(types_pb2.Empty(), timeout=get_rpc_timeout())
        _check_error(resp, "is_enabled")
        return resp.value
