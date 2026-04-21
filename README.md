# Plane Bebekpintar Codex Plugin

MCP tools for the self-hosted Plane instance at:

```text
https://plane.bebekpintar.my.id
```

The plugin defaults to workspace `cybersec-pm` and the `Super Umbies` project:

```text
c99aa5bb-08c6-4d79-b21a-df117b215b4f
```

This Plane instance uses the legacy `issues` endpoint. The plugin does not call `work-items`.

## Environment

Set the API key before starting Codex or running the MCP server.

PowerShell:

```powershell
$env:PLANE_BEBEKPINTAR_API_KEY = "plane_api_your_key_here"
```

Windows user environment:

```powershell
[Environment]::SetEnvironmentVariable("PLANE_BEBEKPINTAR_API_KEY", "plane_api_your_key_here", "User")
```

Do not commit or store the API key in this plugin.

## Run The MCP Server

From this plugin directory:

```powershell
python .\scripts\plane_mcp_server.py
```

Codex can load the server through `./.mcp.json`.

## Install In Codex

This repo can be installed as a Codex plugin with `Create Plugin`.

Recommended flow for teammates:

1. Open Codex.
2. Use `Create Plugin`.
3. Choose the GitHub repo:

```text
https://github.com/akhmadiponegoro/plane-bebekpintar
```

4. After installation, set the environment variable:

```powershell
[Environment]::SetEnvironmentVariable("PLANE_BEBEKPINTAR_API_KEY", "plane_api_your_key_here", "User")
```

5. Restart Codex so the environment variable is loaded.

This plugin exposes a local `STDIO` MCP server through the plugin manifest, so teammates do not need to set up a separate Streamable HTTP MCP URL.

## Tools

- `plane_me`: Get the current Plane user.
- `plane_list_projects`: List projects in a workspace.
- `plane_list_states`: List available workflow states in a project.
- `plane_list_modules`: List modules in a project.
- `plane_list_issues`: List issues in a project using `/issues/`.
- `plane_get_issue`: Get issue details by issue id.
- `plane_search_issues`: Search issues by text. It queries the legacy issues endpoint and filters locally across fields such as `name`, `title`, `description`, and `identifier`.
- `plane_create_issue`: Create a new issue in the legacy `issues` endpoint.
- `plane_update_issue`: Update an existing issue.
- `plane_move_issue_state`: Move an issue to another state by `state_id` or `state_name`. State lookup accepts names such as `Todo`, `In Progress`, `Done`, and also normalized variants such as `todo`, `in-progress`, or state groups like `started`.
- `plane_create_module`: Create a new module in the project.
- `plane_add_issue_to_modules`: Attach an issue to one or more modules by module id or module name.

`plane_add_comment` is not included yet.

## Examples

List projects:

```json
{
  "workspace_slug": "cybersec-pm",
  "per_page": 20
}
```

List Super Umbies issues:

```json
{
  "workspace_slug": "cybersec-pm",
  "project_id": "c99aa5bb-08c6-4d79-b21a-df117b215b4f",
  "per_page": 5
}
```

Search issues:

```json
{
  "query": "login",
  "per_page": 20
}
```

Move an issue to `In Progress`:

```json
{
  "issue_id": "125e3186-a0a7-4270-8c32-90949f1a2351",
  "state_name": "in-progress"
}
```

Create a module and attach an issue to it:

```json
{
  "name": "Files",
  "description": "Files-related work for Super Umbies"
}
```

```json
{
  "issue_id": "bb6ddc38-c3eb-4d73-920a-452dc1483902",
  "module_names": ["Files"]
}
```

## Smoke Test

```powershell
python .\scripts\smoke_test.py
```

The smoke test calls:

- `plane_me`
- `plane_list_projects` for `cybersec-pm`
- `plane_list_issues` for `Super Umbies`

## Error Handling

The server returns readable MCP tool errors for:

- missing `PLANE_BEBEKPINTAR_API_KEY`
- `401` or `403` authentication failures
- `404` endpoint not found
- request timeout or network failure
- non-JSON or invalid JSON responses

API keys are never logged or included in error messages.
