# Plane Bebekpintar Codex Plugin

MCP tools for the self-hosted Plane instance at:

```text
https://plane.bebekpintar.my.id
```

This plugin works for any project in any workspace on the Plane Bebekpintar instance.

The current default values are:

```text
workspace_slug = cybersec-pm
project_id = c99aa5bb-08c6-4d79-b21a-df117b215b4f
```

They are only defaults. Teammates can point the plugin to a different workspace or project by changing `workspace_slug` and `project_id` in tool arguments, or by setting environment variables.

This Plane instance uses the legacy `issues` endpoint. The plugin does not call `work-items`.

## Benefits

In issue-heavy engineering workflows, this plugin usually helps because Codex can fetch Plane data on demand instead of carrying repeated project metadata inside the chat.

Typical practical benefits:

- can reduce repeated project-management context in the conversation by roughly `30%` to `50%`
- can reduce repeated token usage for issue lookup, state lookup, and recap tasks by roughly `20%` to `30%`
- improves accuracy because Codex reads live Plane data instead of relying on older turns
- keeps long development threads cleaner because issue state, module mapping, and project metadata stay in Plane

The exact savings depend on how often your team used to paste issue lists, progress notes, and project status into the conversation manually.

## Environment

Set the API key before starting Codex or running the MCP server.

Required:

```powershell
$env:PLANE_BEBEKPINTAR_API_KEY = "plane_api_your_key_here"
```

Optional default configuration:

```powershell
$env:PLANE_BEBEKPINTAR_BASE_URL = "https://plane.bebekpintar.my.id"
$env:PLANE_BEBEKPINTAR_WORKSPACE_SLUG = "cybersec-pm"
$env:PLANE_BEBEKPINTAR_PROJECT_ID = "c99aa5bb-08c6-4d79-b21a-df117b215b4f"
```

Windows user environment:

```powershell
[Environment]::SetEnvironmentVariable("PLANE_BEBEKPINTAR_API_KEY", "plane_api_your_key_here", "User")
[Environment]::SetEnvironmentVariable("PLANE_BEBEKPINTAR_BASE_URL", "https://plane.bebekpintar.my.id", "User")
[Environment]::SetEnvironmentVariable("PLANE_BEBEKPINTAR_WORKSPACE_SLUG", "cybersec-pm", "User")
[Environment]::SetEnvironmentVariable("PLANE_BEBEKPINTAR_PROJECT_ID", "c99aa5bb-08c6-4d79-b21a-df117b215b4f", "User")
```

Do not commit or store the API key in this plugin.

## Workspace And Project Targeting

To use another workspace, change `workspace_slug` based on the Plane workspace slug.

To use another project, change `project_id` based on the Plane project UUID.

Per-call example:

```json
{
  "workspace_slug": "my-other-workspace",
  "project_id": "my-project-uuid"
}
```

Or set both as environment variables so they become the default values for all tool calls.

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

4. After installation, set the environment variables:

```powershell
[Environment]::SetEnvironmentVariable("PLANE_BEBEKPINTAR_API_KEY", "plane_api_your_key_here", "User")
[Environment]::SetEnvironmentVariable("PLANE_BEBEKPINTAR_WORKSPACE_SLUG", "my-workspace-slug", "User")
[Environment]::SetEnvironmentVariable("PLANE_BEBEKPINTAR_PROJECT_ID", "my-project-id", "User")
```

5. Restart Codex so the environment variables are loaded.

This plugin exposes a local `STDIO` MCP server through the plugin manifest, so teammates do not need to configure a separate Streamable HTTP MCP URL.

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
- `plane_move_issue_state`: Move an issue to another state by `state_id` or `state_name`. State lookup accepts names such as `Todo`, `In Progress`, `Done`, normalized variants such as `todo` and `in-progress`, and state groups such as `started`.
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

List issues for the selected project:

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
  "description": "Files-related work"
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
- `plane_list_projects`
- `plane_list_issues`

The default workspace and project follow the configured environment variables or fall back to the bundled defaults.

## Error Handling

The server returns readable MCP tool errors for:

- missing `PLANE_BEBEKPINTAR_API_KEY`
- `401` or `403` authentication failures
- `404` endpoint not found
- request timeout or network failure
- non-JSON or invalid JSON responses

API keys are never logged or included in error messages.
