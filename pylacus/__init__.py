from __future__ import annotations

import argparse
import json
import sys

from typing import Any, TypedDict, Literal

if sys.version_info >= (3, 13):
    from warnings import deprecated
else:
    from deprecated import deprecated

from .api import PyLacus, CaptureStatus, SessionStatus, CaptureResponse, CaptureResponseJson, RemoteHeadedSessionResponse  # noqa


@deprecated("Use lookyloo-models instead, the Pydantic models.")
class CaptureSettings(TypedDict, total=False):
    '''The capture settings that can be passed to Lacus.'''

    url: str | None
    document_name: str | None
    document: str | None
    browser: Literal['chromium', 'firefox', 'webkit'] | None
    device_name: str | None
    user_agent: str | None
    proxy: str | dict[str, str] | None
    general_timeout_in_sec: int | None
    cookies: str | dict[str, str] | list[dict[str, Any]] | None
    storage: str | dict[str, Any] | None
    headers: str | dict[str, str] | None
    http_credentials: dict[str, str] | None
    geolocation: dict[str, str | int | float] | None
    timezone_id: str | None
    locale: str | None
    color_scheme: str | None
    java_script_enabled: bool
    viewport: dict[str, int | str] | None
    referer: str | None
    with_screenshot: bool
    with_favicon: bool
    with_trusted_timestamps: bool
    allow_tracking: bool
    headless: bool
    remote_headfull: bool
    init_script: str

    force: bool | None
    recapture_interval: int | None
    final_wait: int | None
    priority: int | None
    max_retries: int | None
    uuid: str | None

    depth: int
    rendered_hostname_only: bool  # Note: only used if depth is > 0


__all__ = [
    'PyLacus',
    'CaptureStatus',
    'SessionStatus',
    'CaptureResponse',
    'CaptureResponseJson',
    'RemoteHeadedSessionResponse',
    'CaptureSettings'
]


def main() -> None:
    parser = argparse.ArgumentParser(description='Query a Lacus instance.')
    parser.add_argument('--url-instance', type=str, required=True, help='URL of the instance.')
    parser.add_argument('--redis_up', action='store_true', help='Check if redis is up.')

    subparsers = parser.add_subparsers(help='Available commands', dest='command')

    enqueue = subparsers.add_parser('enqueue', help="Enqueue a url for capture")
    enqueue.add_argument('url', help='URL to capture')

    status = subparsers.add_parser('status', help="Get status of a capture")
    status.add_argument('uuid', help="UUID of the capture")

    result = subparsers.add_parser('result', help="Get result of a capture.")
    result.add_argument('uuid', help="UUID of the capture")

    args = parser.parse_args()

    client = PyLacus(args.url_instance)

    response: str | dict[str, Any] | CaptureStatus | CaptureResponse | CaptureResponseJson
    if not client.is_up:
        print(f'Unable to reach {client.root_url}. Is the server up?')
        sys.exit(1)
    if args.redis_up:
        response = client.redis_up()
    elif args.command == 'enqueue':
        response = client.enqueue(url=args.url)
    elif args.command == 'status':
        response = client.get_capture_status(args.uuid)
    elif args.command == 'result':
        response = client.get_capture(args.uuid, decode=False)
    else:
        response = "Invalid request"

    print(json.dumps(response, indent=2))
