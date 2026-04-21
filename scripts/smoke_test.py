from __future__ import annotations

import json
from typing import Any

from plane_client import DEFAULT_PROJECT_ID, DEFAULT_WORKSPACE, PlaneClient


def main() -> None:
    client = PlaneClient()
    checks: list[tuple[str, Any]] = [
        ("plane_me", client.me()),
        ("plane_list_projects", client.list_projects(DEFAULT_WORKSPACE, per_page=20)),
        ("plane_list_issues", client.list_issues(DEFAULT_WORKSPACE, DEFAULT_PROJECT_ID, per_page=5)),
    ]
    for name, payload in checks:
        print(f"{name}: OK")
        print(json.dumps(compact(payload), indent=2, ensure_ascii=False))


def compact(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {key: compact(value) for key, value in payload.items() if key in wanted_keys()}
    if isinstance(payload, list):
        return [compact(item) for item in payload[:3]]
    return payload


def wanted_keys() -> set[str]:
    return {
        "id",
        "email",
        "display_name",
        "first_name",
        "last_name",
        "workspace_slug",
        "project_id",
        "projects",
        "issues",
        "name",
        "identifier",
        "state",
        "priority",
        "created_at",
        "updated_at",
        "raw_count",
        "pagination",
    }


if __name__ == "__main__":
    main()
