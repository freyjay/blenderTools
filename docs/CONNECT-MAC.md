# Connect on macOS — the official Blender MCP add-on

Verified 2026-09-07 on macOS 15.7.1 / Apple Silicon / Blender 5.1.2 / Claude Desktop.
Windows: not covered here; the Windows workstream documents its own route.

There are two things to connect, and a third that is optional:

| Channel | What it gives | Needs |
|---|---|---|
| **Live** — `Blender:execute_blender_code` | run Python inside the open Blender; the modeling loop | Blender open, add-on server **running** |
| **Background** — `Blender:*_for_cli` tools | a disposable factory-startup Blender per call; verification, captures | `BLENDER_PATH` set for the connector |
| **Filesystem connector** | read/write repo files directly | connector enabled and scoped to the repo |

## A. Blender side (once per machine, then Auto Start)

1. **Edit → Preferences → Add-ons**, search **MCP**. It must be the Blender Lab extension
   (Website `www.blender.org`, Maintainer *Blender Lab*, file under
   `…/Blender/5.1/extensions/user_default/mcp/`). Tick it enabled.
   *Not* `github.com/ahujasid/blender-mcp` — same port, different protocol, not interchangeable.
2. Still in Preferences: **System → Network → tick "Allow Online Access."**
   Without it the add-on shows *"Online access must be enabled in the system preferences"*
   and the server cannot open its socket. This is the step most likely to be missed.
3. Back in the MCP add-on panel (expand the entry): **Host** `localhost`, **Port** `9876`.
   Tick **Auto Start** so every future session starts the server itself.
   Click **▶ Start MCP Bridge Server**. The status line must read **"Server is running."**
4. There is **no sidebar tab** for this add-on (the N-panel shows only Item/Tool/View/Animation);
   the server is controlled only from Preferences. **Window → Toggle System Console does not exist
   on macOS** — the connection test below is the check.

## B. Claude side

5. In the chat, open the connectors menu (the plug icon) and make sure **Blender** is toggled on.
   Its 26 tools are *deferred*: if none appear, call `tool_search` with "blender execute code".
6. Connectivity test — run first in every session:
   ```python
   import bpy
   result = {"blender": bpy.app.version_string, "objects": len(bpy.data.objects)}
   ```
   A JSON result confirms the link. **The first command after a fresh connection sometimes fails
   once**; retry before troubleshooting.
7. Load the package: `import blendertools as bt; bt.doctor()` — `socket_patch: present` confirms
   the local large-payload patch (docs/PATCHES.md) survived any add-on update.

## C. Background route (optional, recommended)

The `*_for_cli` tools spawn their own Blender and need its path. The connector is a Desktop
extension, not an entry in `claude_desktop_config.json`, so set the variable at login-session level:
```bash
launchctl setenv BLENDER_PATH "/Applications/Blender.app/Contents/MacOS/Blender"
```
then **Cmd+Q Claude Desktop and reopen** (child processes inherit the variable only on relaunch).
`launchctl setenv` lasts until reboot; if the connector's settings panel offers a Blender-path field,
set it there permanently as well.

## D. Filesystem connector (optional, removes the zip-and-script dance)

Enable **filesystem** in the connectors menu and, in **Manage connectors → filesystem**, add
`/Users/<you>/Developer/blenderTools` to the allowed directories. Its tools attach when a
conversation **starts** — toggling it mid-conversation shows the switch on but adds no tools; open a
new conversation to use it.

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Cannot connect to Blender at localhost:9876` | Blender open but server not running | Preferences → Add-ons → MCP → Start; tick Auto Start |
| *Online access must be enabled…* in the add-on panel | Blender network permission off | System → Network → Allow Online Access |
| `Blender executable not found at 'blender'` from a `_for_cli` tool | `BLENDER_PATH` unset for the connector | Section C |
| Connector toggled on, no tools | tools attach at conversation start | new conversation |
| Screenshot tools return unreadable images | limit of this transport, not of images | use text renders (`bt.eye`), or render to disk for a human |
| `bpy.context.object` is `None` over MCP | no UI context in the socket handler | use `bpy.context.view_layer.objects.active` |
