# AGENT.md

## Purpose

This plugin lets an agent use Codex with the self-hosted Plane Bebekpintar instance through MCP tools.

Use it when the task needs live Plane data instead of relying on chat memory, especially for:

- reading issues, states, projects, and modules
- creating or updating issues
- moving issues across workflow states
- organizing issues into Plane modules

The plugin is not tied to one project. It works across workspaces and projects by changing `workspace_slug` and `project_id`.

## Why Use This Plugin

In issue-heavy workflows, this plugin usually helps by keeping operational data in Plane and pulling it only when needed.

Typical practical benefits:

- can reduce repeated project-management context in chat by roughly `30%` to `50%`
- can reduce repeated token usage for issue lookup and recap work by roughly `20%` to `30%`
- improves accuracy because the agent reads live Plane data
- keeps long coding threads cleaner and more stable

These figures are directional estimates, not guarantees.

## Configuration

Required environment variable:

- `PLANE_BEBEKPINTAR_API_KEY`

Optional default environment variables:

- `PLANE_BEBEKPINTAR_BASE_URL`
- `PLANE_BEBEKPINTAR_WORKSPACE_SLUG`
- `PLANE_BEBEKPINTAR_PROJECT_ID`

If the optional variables are not set, the plugin falls back to bundled defaults.

Per-call overrides are supported through tool arguments:

- `workspace_slug`
- `project_id`

## Important Instance Notes

- Base URL defaults to `https://plane.bebekpintar.my.id`
- This instance uses the legacy `issues` endpoint
- Do not use `work-items` for this instance
- Authentication uses the `X-API-Key` header
- Never hard-code or log the API key

## Tool Map

Use these tools for the following jobs:

- `plane_me`
  Get the current authenticated Plane user.

- `plane_list_projects`
  List projects in a workspace.

- `plane_list_states`
  List valid workflow states for a project before moving issues.

- `plane_list_modules`
  List available modules before attaching issues to them.

- `plane_list_issues`
  Read issues in a project.

- `plane_get_issue`
  Inspect one issue in detail.

- `plane_search_issues`
  Find issues by text.

- `plane_create_issue`
  Create a new issue.

- `plane_update_issue`
  Update title, description, or priority.

- `plane_move_issue_state`
  Move an issue by `state_id` or `state_name`.
  Prefer `state_name` when possible.
  Accepted values are forgiving, for example:
  - `Todo`
  - `todo`
  - `In Progress`
  - `in-progress`
  - `started`

- `plane_create_module`
  Create a new module in the project.

- `plane_add_issue_to_modules`
  Attach an issue to one or more modules by module id or name.

## Recommended Agent Workflow

For task intake:

1. Call `plane_list_projects` if the target project is unclear.
2. Call `plane_list_issues` or `plane_search_issues` to find the work item.
3. Call `plane_get_issue` if deeper context is needed.

For status changes:

1. Call `plane_list_states` if the project state names are unknown.
2. Call `plane_move_issue_state` with `state_name`.

For module organization:

1. Call `plane_list_modules` if module names are unknown.
2. If needed, call `plane_create_module`.
3. Call `plane_add_issue_to_modules`.

For new work capture:

1. Call `plane_create_issue`.
2. Optionally call `plane_move_issue_state`.
3. Optionally call `plane_add_issue_to_modules`.

## Guardrails

- Do not assume one workspace or project unless the user asked for the defaults.
- When the user references another workspace, pass `workspace_slug` explicitly.
- When the user references another project, pass `project_id` explicitly.
- Prefer reading states and modules first when there is ambiguity.
- Do not claim exact efficiency savings as guarantees; treat them as approximate operational benefits.
- Keep issue descriptions concise but actionable.
- Do not expose credentials in chat, logs, files, or error messages.

## Installation Note

This repository can be installed in Codex using `Create Plugin` from:

```text
https://github.com/akhmadiponegoro/plane-bebekpintar
```

After installation, each user should set their own environment variables and restart Codex.
