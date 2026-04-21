from __future__ import annotations

import json
import sys
import traceback
from typing import Any

from plane_client import DEFAULT_PROJECT_ID, DEFAULT_WORKSPACE, PlaneClient, PlaneError


TOOLS: list[dict[str, Any]] = [
    {
        "name": "plane_me",
        "description": "Get the current Plane user.",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        },
    },
    {
        "name": "plane_list_projects",
        "description": "List projects in a Plane workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_slug": {
                    "type": "string",
                    "description": f"Plane workspace slug. Defaults to {DEFAULT_WORKSPACE}.",
                    "default": DEFAULT_WORKSPACE,
                },
                "per_page": {
                    "type": "integer",
                    "description": "Number of projects to request.",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "plane_create_project",
        "description": "Create a new project in a Plane workspace.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Project name (required).",
                },
                "identifier": {
                    "type": "string",
                    "description": "Project identifier/slug (required, uppercase recommended, e.g., 'PROJ').",
                },
                "description": {
                    "type": "string",
                    "description": "Project description (optional).",
                },
                "workspace_slug": {
                    "type": "string",
                    "description": f"Plane workspace slug. Defaults to {DEFAULT_WORKSPACE}.",
                    "default": DEFAULT_WORKSPACE,
                },
            },
            "required": ["name", "identifier"],
            "additionalProperties": False,
        },
    },
    {
        "name": "plane_list_states",
        "description": "List workflow states in a Plane project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_slug": {"type": "string", "default": DEFAULT_WORKSPACE},
                "project_id": {"type": "string", "default": DEFAULT_PROJECT_ID},
                "per_page": {"type": "integer", "default": 100, "minimum": 1, "maximum": 100},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "plane_list_modules",
        "description": "List modules in a Plane project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_slug": {"type": "string", "default": DEFAULT_WORKSPACE},
                "project_id": {"type": "string", "default": DEFAULT_PROJECT_ID},
                "per_page": {"type": "integer", "default": 100, "minimum": 1, "maximum": 100},
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "plane_list_issues",
        "description": "List issues in a Plane project using the legacy issues endpoint.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_slug": {
                    "type": "string",
                    "default": DEFAULT_WORKSPACE,
                },
                "project_id": {
                    "type": "string",
                    "default": DEFAULT_PROJECT_ID,
                },
                "per_page": {
                    "type": "integer",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                },
                "cursor": {
                    "type": "string",
                    "description": "Optional Plane pagination cursor.",
                },
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "plane_get_issue",
        "description": "Get a single issue by issue id.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_slug": {
                    "type": "string",
                    "default": DEFAULT_WORKSPACE,
                },
                "project_id": {
                    "type": "string",
                    "default": DEFAULT_PROJECT_ID,
                },
                "issue_id": {
                    "type": "string",
                    "description": "Plane issue UUID.",
                },
            },
            "required": ["issue_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "plane_search_issues",
        "description": "Search issues by text, falling back to local filtering of the legacy issues endpoint.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_slug": {
                    "type": "string",
                    "default": DEFAULT_WORKSPACE,
                },
                "project_id": {
                    "type": "string",
                    "default": DEFAULT_PROJECT_ID,
                },
                "query": {
                    "type": "string",
                    "description": "Text to search in issue name/title/description/identifier.",
                },
                "per_page": {
                    "type": "integer",
                    "default": 20,
                    "minimum": 1,
                    "maximum": 100,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "plane_create_issue",
        "description": "Create a Plane issue in the default or specified project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_slug": {"type": "string", "default": DEFAULT_WORKSPACE},
                "project_id": {"type": "string", "default": DEFAULT_PROJECT_ID},
                "name": {"type": "string", "description": "Issue title."},
                "description": {"type": "string", "description": "Issue description."},
                "priority": {
                    "type": "string",
                    "description": "Optional Plane priority such as urgent, high, medium, low, none.",
                },
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "plane_update_issue",
        "description": "Update an existing Plane issue.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_slug": {"type": "string", "default": DEFAULT_WORKSPACE},
                "project_id": {"type": "string", "default": DEFAULT_PROJECT_ID},
                "issue_id": {"type": "string", "description": "Plane issue UUID."},
                "name": {"type": "string", "description": "Updated issue title."},
                "description": {"type": "string", "description": "Updated issue description."},
                "priority": {
                    "type": "string",
                    "description": "Updated priority such as urgent, high, medium, low, none.",
                },
            },
            "required": ["issue_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "plane_move_issue_state",
        "description": "Move an issue to another Plane workflow state by state_id or state_name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_slug": {"type": "string", "default": DEFAULT_WORKSPACE},
                "project_id": {"type": "string", "default": DEFAULT_PROJECT_ID},
                "issue_id": {"type": "string", "description": "Plane issue UUID."},
                "state_id": {"type": "string", "description": "Destination state UUID."},
                "state_name": {"type": "string", "description": "Destination state name such as Backlog, Todo, In Progress, Done."},
            },
            "required": ["issue_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "plane_create_module",
        "description": "Create a module in a Plane project.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_slug": {"type": "string", "default": DEFAULT_WORKSPACE},
                "project_id": {"type": "string", "default": DEFAULT_PROJECT_ID},
                "name": {"type": "string", "description": "Module name."},
                "description": {"type": "string", "description": "Module description."},
                "status": {"type": "string", "description": "Optional module status. Defaults to planned."},
            },
            "required": ["name"],
            "additionalProperties": False,
        },
    },
    {
        "name": "plane_add_issue_to_modules",
        "description": "Attach an issue to one or more Plane modules by module id or name.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "workspace_slug": {"type": "string", "default": DEFAULT_WORKSPACE},
                "project_id": {"type": "string", "default": DEFAULT_PROJECT_ID},
                "issue_id": {"type": "string", "description": "Plane issue UUID."},
                "module_ids": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of module UUIDs.",
                },
                "module_names": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "List of module names to resolve automatically.",
                },
            },
            "required": ["issue_id"],
            "additionalProperties": False,
        },
    },
]


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            request = json.loads(line)
            response = handle_request(request)
        except Exception as exc:
            response = json_rpc_error(None, -32603, f"Internal MCP server error: {exc}")
            print(traceback.format_exc(), file=sys.stderr)

        if response is not None:
            sys.stdout.write(json.dumps(response, separators=(",", ":")) + "\n")
            sys.stdout.flush()


def handle_request(request: dict[str, Any]) -> dict[str, Any] | None:
    method = request.get("method")
    request_id = request.get("id")

    if method == "initialize":
        return json_rpc_result(
            request_id,
            {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "plane-bebekpintar",
                    "version": "0.1.0",
                },
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "ping":
        return json_rpc_result(request_id, {})
    if method == "tools/list":
        return json_rpc_result(request_id, {"tools": TOOLS})
    if method == "tools/call":
        params = request.get("params") or {}
        return json_rpc_result(request_id, call_tool(params.get("name"), params.get("arguments") or {}))

    return json_rpc_error(request_id, -32601, f"Method not found: {method}")


def call_tool(name: str, args: dict[str, Any]) -> dict[str, Any]:
    try:
        client = PlaneClient()
        if name == "plane_me":
            payload = client.me()
        elif name == "plane_list_projects":
            payload = client.list_projects(
                workspace_slug=args.get("workspace_slug", DEFAULT_WORKSPACE),
                per_page=args.get("per_page", 20),
            )
        elif name == "plane_create_project":
            project_name = require_arg(args, "name")
            project_identifier = require_arg(args, "identifier")
            payload = client.create_project(
                name=project_name,
                identifier=project_identifier,
                description=args.get("description"),
                workspace_slug=args.get("workspace_slug", DEFAULT_WORKSPACE),
            )
        elif name == "plane_list_states":
            payload = client.list_states(
                workspace_slug=args.get("workspace_slug", DEFAULT_WORKSPACE),
                project_id=args.get("project_id", DEFAULT_PROJECT_ID),
                per_page=args.get("per_page", 100),
            )
        elif name == "plane_list_modules":
            payload = client.list_modules(
                workspace_slug=args.get("workspace_slug", DEFAULT_WORKSPACE),
                project_id=args.get("project_id", DEFAULT_PROJECT_ID),
                per_page=args.get("per_page", 100),
            )
        elif name == "plane_list_issues":
            payload = client.list_issues(
                workspace_slug=args.get("workspace_slug", DEFAULT_WORKSPACE),
                project_id=args.get("project_id", DEFAULT_PROJECT_ID),
                per_page=args.get("per_page", 20),
                cursor=args.get("cursor"),
            )
        elif name == "plane_get_issue":
            issue_id = require_arg(args, "issue_id")
            payload = client.get_issue(
                issue_id=issue_id,
                workspace_slug=args.get("workspace_slug", DEFAULT_WORKSPACE),
                project_id=args.get("project_id", DEFAULT_PROJECT_ID),
            )
        elif name == "plane_search_issues":
            query = require_arg(args, "query")
            payload = client.search_issues(
                search_query=query,
                workspace_slug=args.get("workspace_slug", DEFAULT_WORKSPACE),
                project_id=args.get("project_id", DEFAULT_PROJECT_ID),
                per_page=args.get("per_page", 20),
            )
        elif name == "plane_create_issue":
            issue_name = require_arg(args, "name")
            payload = client.create_issue(
                name=issue_name,
                description=args.get("description"),
                workspace_slug=args.get("workspace_slug", DEFAULT_WORKSPACE),
                project_id=args.get("project_id", DEFAULT_PROJECT_ID),
                priority=args.get("priority"),
            )
        elif name == "plane_update_issue":
            issue_id = require_arg(args, "issue_id")
            payload = client.update_issue(
                issue_id=issue_id,
                workspace_slug=args.get("workspace_slug", DEFAULT_WORKSPACE),
                project_id=args.get("project_id", DEFAULT_PROJECT_ID),
                name=args.get("name"),
                description=args.get("description"),
                priority=args.get("priority"),
            )
        elif name == "plane_move_issue_state":
            issue_id = require_arg(args, "issue_id")
            payload = client.move_issue_state(
                issue_id=issue_id,
                workspace_slug=args.get("workspace_slug", DEFAULT_WORKSPACE),
                project_id=args.get("project_id", DEFAULT_PROJECT_ID),
                state_id=args.get("state_id"),
                state_name=args.get("state_name"),
            )
        elif name == "plane_create_module":
            module_name = require_arg(args, "name")
            payload = client.create_module(
                name=module_name,
                description=args.get("description"),
                workspace_slug=args.get("workspace_slug", DEFAULT_WORKSPACE),
                project_id=args.get("project_id", DEFAULT_PROJECT_ID),
                status=args.get("status", "planned"),
            )
        elif name == "plane_add_issue_to_modules":
            issue_id = require_arg(args, "issue_id")
            payload = client.add_issue_to_modules(
                issue_id=issue_id,
                workspace_slug=args.get("workspace_slug", DEFAULT_WORKSPACE),
                project_id=args.get("project_id", DEFAULT_PROJECT_ID),
                module_ids=args.get("module_ids"),
                module_names=args.get("module_names"),
            )
        else:
            return tool_error(f"Unknown tool: {name}")
    except PlaneError as exc:
        return tool_error(str(exc))
    except Exception as exc:
        return tool_error(f"Unexpected Plane tool error: {exc}")

    return {
        "content": [
            {
                "type": "text",
                "text": json.dumps(payload, indent=2, ensure_ascii=False),
            }
        ],
        "isError": False,
    }


def require_arg(args: dict[str, Any], key: str) -> str:
    value = args.get(key)
    if not value:
        raise PlaneError(f"Missing required argument: {key}")
    return str(value)


def tool_error(message: str) -> dict[str, Any]:
    return {
        "content": [
            {
                "type": "text",
                "text": message,
            }
        ],
        "isError": True,
    }


def json_rpc_result(request_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def json_rpc_error(request_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}}


if __name__ == "__main__":
    main()
