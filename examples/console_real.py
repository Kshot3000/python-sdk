from __future__ import annotations

import json
import os

from octaspace import OctaSpaceClient


def dump(label: str, payload: object) -> None:
    print(f"{label}: {json.dumps(payload, ensure_ascii=False)}")


def main() -> None:
    api_key = os.getenv("OCTA_API_KEY")
    session_uuid = os.getenv("OCTA_SESSION_UUID")
    allow_stop = os.getenv("OCTA_ALLOW_STOP") == "1"

    with OctaSpaceClient(api_key=api_key, keep_alive=True, pool_size=10) as client:
        dump("transport_stats", client.transport_stats())
        dump("network", client.network.info().data)

        if not api_key:
            print("OCTA_API_KEY is not set; authenticated checks skipped.")
            return

        dump("profile", client.accounts.profile().data)
        dump("balance", client.accounts.balance().data)
        dump("nodes_count", len(client.nodes.list().data))
        dump("sessions_count", len(client.sessions.list().data))

        if not session_uuid:
            print("OCTA_SESSION_UUID is not set; session inspection skipped.")
            return

        session = client.services.session(session_uuid)
        dump("session_info", session.info().data)
        logs = session.logs().data
        preview = logs[:5] if isinstance(logs, list) else logs
        dump("session_logs_preview", preview)

        if allow_stop:
            dump("session_stop", session.stop(score=5).data)
        else:
            print("OCTA_ALLOW_STOP is not set; destructive stop call skipped.")


if __name__ == "__main__":
    main()
