from __future__ import annotations

import html
import json
import os
import socket
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


API_KEY_ENV = "PLANE_BEBEKPINTAR_API_KEY"
BASE_URL_ENV = "PLANE_BEBEKPINTAR_BASE_URL"
WORKSPACE_ENV = "PLANE_BEBEKPINTAR_WORKSPACE_SLUG"
PROJECT_ENV = "PLANE_BEBEKPINTAR_PROJECT_ID"
BASE_URL = os.environ.get(BASE_URL_ENV, "https://plane.bebekpintar.my.id")
DEFAULT_WORKSPACE = os.environ.get(WORKSPACE_ENV, "cybersec-pm")
DEFAULT_PROJECT_ID = os.environ.get(PROJECT_ENV, "c99aa5bb-08c6-4d79-b21a-df117b215b4f")
REQUEST_TIMEOUT_SECONDS = 20
BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/135.0.0.0 Safari/537.36"
)


class PlaneError(Exception):
    pass


class PlaneClient:
    def __init__(self) -> None:
        api_key = os.environ.get(API_KEY_ENV)
        if not api_key:
            raise PlaneError(
                f"Environment variable {API_KEY_ENV} is not set. "
                "Set it before starting the MCP server."
            )
        self.api_key = api_key

    def me(self) -> dict[str, Any]:
        return self._get("/api/v1/users/me/")

    def list_projects(self, workspace_slug: str = DEFAULT_WORKSPACE, per_page: int = 20) -> dict[str, Any]:
        payload = self._get(
            f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/",
            {"per_page": clamp_per_page(per_page)},
        )
        return {
            "workspace_slug": workspace_slug,
            "projects": [summarize_project(item) for item in extract_items(payload)],
            "pagination": extract_pagination(payload),
            "raw_count": len(extract_items(payload)),
        }

    def create_project(
        self,
        name: str,
        identifier: str,
        description: str | None = None,
        workspace_slug: str = DEFAULT_WORKSPACE,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": name,
            "identifier": identifier,
        }
        if description is not None:
            payload["description"] = description
        response = self._request_json(
            "POST",
            f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/",
            body=payload,
        )
        return summarize_project(response)

    def list_states(
        self,
        workspace_slug: str = DEFAULT_WORKSPACE,
        project_id: str = DEFAULT_PROJECT_ID,
        per_page: int = 100,
    ) -> dict[str, Any]:
        payload = self._get(
            f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/{quote_path(project_id)}/states/",
            {"per_page": clamp_per_page(per_page)},
        )
        return {
            "workspace_slug": workspace_slug,
            "project_id": project_id,
            "states": [summarize_state(item) for item in extract_items(payload)],
            "pagination": extract_pagination(payload),
            "raw_count": len(extract_items(payload)),
        }

    def list_modules(
        self,
        workspace_slug: str = DEFAULT_WORKSPACE,
        project_id: str = DEFAULT_PROJECT_ID,
        per_page: int = 100,
    ) -> dict[str, Any]:
        payload = self._get(
            f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/{quote_path(project_id)}/modules/",
            {"per_page": clamp_per_page(per_page)},
        )
        return {
            "workspace_slug": workspace_slug,
            "project_id": project_id,
            "modules": [summarize_module(item) for item in extract_items(payload)],
            "pagination": extract_pagination(payload),
            "raw_count": len(extract_items(payload)),
        }

    def list_issues(
        self,
        workspace_slug: str = DEFAULT_WORKSPACE,
        project_id: str = DEFAULT_PROJECT_ID,
        per_page: int = 20,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        query: dict[str, Any] = {"per_page": clamp_per_page(per_page)}
        if cursor:
            query["cursor"] = cursor
        payload = self._get(
            f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/{quote_path(project_id)}/issues/",
            query,
        )
        return {
            "workspace_slug": workspace_slug,
            "project_id": project_id,
            "issues": [summarize_issue(item) for item in extract_items(payload)],
            "pagination": extract_pagination(payload),
            "raw_count": len(extract_items(payload)),
        }

    def get_issue(
        self,
        issue_id: str,
        workspace_slug: str = DEFAULT_WORKSPACE,
        project_id: str = DEFAULT_PROJECT_ID,
    ) -> dict[str, Any]:
        payload = self._get(
            f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/{quote_path(project_id)}/issues/{quote_path(issue_id)}/"
        )
        return summarize_issue(payload, include_description=True)

    def search_issues(
        self,
        search_query: str,
        workspace_slug: str = DEFAULT_WORKSPACE,
        project_id: str = DEFAULT_PROJECT_ID,
        per_page: int = 20,
    ) -> dict[str, Any]:
        try:
            payload = self._get(
                f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/{quote_path(project_id)}/issues/",
                {"per_page": clamp_per_page(per_page), "search": search_query},
            )
        except PlaneError:
            payload = self._get(
                f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/{quote_path(project_id)}/issues/",
                {"per_page": clamp_per_page(per_page)},
            )

        issues = [item for item in extract_items(payload) if issue_matches(item, search_query)]
        return {
            "workspace_slug": workspace_slug,
            "project_id": project_id,
            "query": search_query,
            "issues": [summarize_issue(item) for item in issues],
            "raw_count": len(issues),
            "note": "Filtered locally from issue fields after querying the legacy issues endpoint.",
        }

    def create_issue(
        self,
        name: str,
        description: str | None = None,
        workspace_slug: str = DEFAULT_WORKSPACE,
        project_id: str = DEFAULT_PROJECT_ID,
        priority: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name}
        if description is not None:
            payload["description_html"] = text_to_html(description)
        if priority:
            payload["priority"] = priority
        response = self._request_json(
            "POST",
            f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/{quote_path(project_id)}/issues/",
            body=payload,
        )
        return summarize_issue(response, include_description=True)

    def update_issue(
        self,
        issue_id: str,
        workspace_slug: str = DEFAULT_WORKSPACE,
        project_id: str = DEFAULT_PROJECT_ID,
        name: str | None = None,
        description: str | None = None,
        priority: str | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {}
        if name is not None:
            payload["name"] = name
        if description is not None:
            payload["description_html"] = text_to_html(description)
        if priority is not None:
            payload["priority"] = priority
        if not payload:
            raise PlaneError("No fields provided for issue update.")
        response = self._request_json(
            "PATCH",
            (
                f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/"
                f"{quote_path(project_id)}/issues/{quote_path(issue_id)}/"
            ),
            body=payload,
        )
        return summarize_issue(response, include_description=True)

    def move_issue_state(
        self,
        issue_id: str,
        workspace_slug: str = DEFAULT_WORKSPACE,
        project_id: str = DEFAULT_PROJECT_ID,
        state_id: str | None = None,
        state_name: str | None = None,
    ) -> dict[str, Any]:
        resolved_state_id = state_id or self.resolve_state_id(
            workspace_slug=workspace_slug,
            project_id=project_id,
            state_name=state_name,
        )
        response = self._request_json(
            "PATCH",
            (
                f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/"
                f"{quote_path(project_id)}/issues/{quote_path(issue_id)}/"
            ),
            body={"state": resolved_state_id},
        )
        return summarize_issue(response, include_description=True)

    def create_module(
        self,
        name: str,
        description: str | None = None,
        workspace_slug: str = DEFAULT_WORKSPACE,
        project_id: str = DEFAULT_PROJECT_ID,
        status: str = "planned",
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"name": name, "status": status}
        if description is not None:
            payload["description"] = description
        response = self._request_json(
            "POST",
            f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/{quote_path(project_id)}/modules/",
            body=payload,
        )
        return summarize_module(response)

    def add_issue_to_modules(
        self,
        issue_id: str,
        workspace_slug: str = DEFAULT_WORKSPACE,
        project_id: str = DEFAULT_PROJECT_ID,
        module_ids: list[str] | None = None,
        module_names: list[str] | None = None,
    ) -> dict[str, Any]:
        resolved_module_ids = list(module_ids or [])
        for module_name in module_names or []:
            resolved_module_ids.append(
                self.resolve_module_id(
                    workspace_slug=workspace_slug,
                    project_id=project_id,
                    module_name=module_name,
                )
            )
        if not resolved_module_ids:
            raise PlaneError("Provide at least one module_id or module_name.")

        links: list[dict[str, Any]] = []
        for module_id in dedupe_preserve_order(resolved_module_ids):
            response = self._request_json(
                "POST",
                (
                    f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/{quote_path(project_id)}/"
                    f"modules/{quote_path(module_id)}/module-issues/"
                ),
                body={"issues": [issue_id]},
            )
            if isinstance(response, list):
                links.extend(item for item in response if isinstance(item, dict))
        return {
            "workspace_slug": workspace_slug,
            "project_id": project_id,
            "issue_id": issue_id,
            "module_ids": dedupe_preserve_order(resolved_module_ids),
            "links": [summarize_module_issue_link(item) for item in links],
            "raw_count": len(links),
        }

    def resolve_state_id(
        self,
        workspace_slug: str,
        project_id: str,
        state_name: str | None,
    ) -> str:
        if not state_name:
            raise PlaneError("Provide either state_id or state_name.")
        states = extract_items(
            self._get(
                f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/{quote_path(project_id)}/states/",
                {"per_page": 100},
            )
        )
        requested = normalize_label(state_name)
        for state in states:
            state_id = str(state.get("id", ""))
            state_name_value = state.get("name")
            state_group_value = state.get("group")
            if state_id == state_name:
                return state_id
            if isinstance(state_name_value, str) and normalize_label(state_name_value) == requested:
                return state_id
            if isinstance(state_group_value, str) and normalize_label(state_group_value) == requested:
                return str(state["id"])
        available = ", ".join(
            f"{state.get('name')} ({state.get('group')})"
            for state in states
            if isinstance(state.get("name"), str)
        )
        raise PlaneError(f"State '{state_name}' not found. Available states: {available}")

    def resolve_module_id(
        self,
        workspace_slug: str,
        project_id: str,
        module_name: str | None,
    ) -> str:
        if not module_name:
            raise PlaneError("Module name is required when module_id is not provided.")
        modules = extract_items(
            self._get(
                f"/api/v1/workspaces/{quote_path(workspace_slug)}/projects/{quote_path(project_id)}/modules/",
                {"per_page": 100},
            )
        )
        requested = normalize_label(module_name)
        for module in modules:
            module_id = str(module.get("id", ""))
            module_name_value = module.get("name")
            if module_id == module_name:
                return module_id
            if isinstance(module_name_value, str) and normalize_label(module_name_value) == requested:
                return str(module["id"])
        available = ", ".join(
            str(module.get("name")) for module in modules if isinstance(module.get("name"), str)
        )
        raise PlaneError(f"Module '{module_name}' not found. Available modules: {available}")

    def _get(self, path: str, query: dict[str, Any] | None = None) -> Any:
        return self._request_json("GET", path, query=query)

    def _request_json(
        self,
        method: str,
        path: str,
        query: dict[str, Any] | None = None,
        body: dict[str, Any] | None = None,
    ) -> Any:
        url = build_url(path, query)
        data = json.dumps(body).encode("utf-8") if body is not None else None
        headers = {
            "Accept": "application/json",
            "X-API-Key": self.api_key,
            "User-Agent": BROWSER_USER_AGENT,
        }
        if body is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, headers=headers, data=data, method=method)
        try:
            with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT_SECONDS) as response:
                content_type = response.headers.get("Content-Type", "")
                body = response.read().decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            raise PlaneError(format_http_error(exc, path)) from exc
        except (urllib.error.URLError, TimeoutError, socket.timeout) as exc:
            raise PlaneError(f"Request to Plane timed out or failed after {REQUEST_TIMEOUT_SECONDS}s: {exc}") from exc

        if "json" not in content_type.lower():
            preview = body[:200].replace("\n", " ")
            raise PlaneError(f"Plane returned a non-JSON response for {path}: {preview}")

        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise PlaneError(f"Plane returned invalid JSON for {path}.") from exc


def build_url(path: str, query: dict[str, Any] | None = None) -> str:
    url = f"{BASE_URL}{path}"
    if query:
        cleaned = {key: value for key, value in query.items() if value is not None}
        url = f"{url}?{urllib.parse.urlencode(cleaned)}"
    return url


def quote_path(value: str) -> str:
    return urllib.parse.quote(str(value), safe="")


def clamp_per_page(value: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = 20
    return max(1, min(parsed, 100))


def format_http_error(exc: urllib.error.HTTPError, path: str) -> str:
    status = exc.code
    if status in (401, 403):
        return "Plane authentication failed. Check the PLANE_BEBEKPINTAR_API_KEY environment variable."
    if status == 404:
        return f"Plane endpoint not found for {path}. This plugin uses the legacy issues endpoint, not work-items."
    body = ""
    try:
        body = exc.read().decode("utf-8", errors="replace")[:300].replace("\n", " ")
    except Exception:
        body = ""
    suffix = f" Response preview: {body}" if body else ""
    return f"Plane HTTP error {status} for {path}.{suffix}"


def extract_items(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("results", "issues", "projects", "data", "items"):
        value = payload.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
        if isinstance(value, dict):
            nested = extract_items(value)
            if nested:
                return nested
    return []


def extract_pagination(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    keys = (
        "count",
        "total_count",
        "next",
        "previous",
        "next_cursor",
        "prev_cursor",
        "cursor",
        "total_pages",
        "page",
        "per_page",
    )
    return {key: payload.get(key) for key in keys if key in payload}


def summarize_project(project: dict[str, Any]) -> dict[str, Any]:
    return pick_fields(
        project,
        (
            "id",
            "name",
            "identifier",
            "description",
            "network",
            "created_at",
            "updated_at",
        ),
    )


def summarize_state(state: dict[str, Any]) -> dict[str, Any]:
    return pick_fields(
        state,
        (
            "id",
            "name",
            "group",
            "color",
            "sequence",
            "default",
            "created_at",
            "updated_at",
        ),
    )


def summarize_module(module: dict[str, Any]) -> dict[str, Any]:
    return pick_fields(
        module,
        (
            "id",
            "name",
            "description",
            "status",
            "lead",
            "total_issues",
            "completed_issues",
            "started_issues",
            "unstarted_issues",
            "backlog_issues",
            "created_at",
            "updated_at",
        ),
    )


def summarize_issue(issue: dict[str, Any], include_description: bool = False) -> dict[str, Any]:
    fields = [
        "id",
        "name",
        "title",
        "identifier",
        "sequence_id",
        "state",
        "priority",
        "assignees",
        "labels",
        "created_at",
        "updated_at",
    ]
    if include_description:
        fields.extend(["description", "description_html", "description_stripped"])
    return pick_fields(issue, tuple(fields))


def summarize_module_issue_link(link: dict[str, Any]) -> dict[str, Any]:
    return pick_fields(
        link,
        (
            "id",
            "module",
            "issue",
            "created_at",
            "updated_at",
        ),
    )


def pick_fields(payload: dict[str, Any], fields: tuple[str, ...]) -> dict[str, Any]:
    output: dict[str, Any] = {}
    for field in fields:
        if field in payload:
            output[field] = payload[field]
    return output


def issue_matches(issue: dict[str, Any], search_query: str) -> bool:
    needle = search_query.casefold()
    haystacks = [
        issue.get("name"),
        issue.get("title"),
        issue.get("description"),
        issue.get("description_stripped"),
        issue.get("identifier"),
        str(issue.get("sequence_id")) if issue.get("sequence_id") is not None else None,
    ]
    return any(isinstance(value, str) and needle in value.casefold() for value in haystacks)


def text_to_html(value: str) -> str:
    paragraphs = [segment.strip() for segment in value.split("\n\n") if segment.strip()]
    if not paragraphs:
        return "<p></p>"
    return "".join(f"<p>{html.escape(paragraph).replace(chr(10), '<br/>')}</p>" for paragraph in paragraphs)


def dedupe_preserve_order(values: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def normalize_label(value: str) -> str:
    normalized = value.strip().casefold()
    for char in ("-", "_", "/", "."):
        normalized = normalized.replace(char, " ")
    return " ".join(normalized.split())
