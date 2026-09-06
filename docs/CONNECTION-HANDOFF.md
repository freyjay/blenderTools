# Blender Connection Handoff

Read this before doing anything else in a new session that needs Blender.
It covers only the CONNECTION itself -- how to get from "Claude in a chat"
to "Claude can run code inside a live Blender instance." For how to actually
WORK once connected (vision, measurement, calibration doctrine), read
`skills/blender-connect/SKILL.md` instead -- this document assumes you'll
go there next.

## What's actually running

- **Blender 5.1.2**, macOS (Apple Silicon), Python 3.13.9 embedded interpreter.
- The **official Blender MCP** addon -- from blender.org/lab/mcp-server,
  source at projects.blender.org/lab/blender_mcp.
- **This is NOT the popular community repo `ahujasid/blender-mcp`.** That is
  a different project with a different `addon.py`, a different tool surface,
  and is NOT interchangeable with what this project uses. If you find
  yourself reading ahujasid's source to understand a tool call, stop --
  you're looking at the wrong codebase.
- Addon name inside Blender: **"MCP"**, version 1.0.0.
- Installed at:
  `~/Library/Application Support/Blender/5.1/extensions/user_default/mcp`
- Communicates over a local socket on **localhost:9876**.

## Verifying the correct addon is installed (human-side, in Blender)

1. Edit > Preferences > Add-ons/Extensions, search "MCP".
2. Confirm the entry's source/homepage points to
   `projects.blender.org/lab/blender_mcp`, not `github.com/ahujasid/blender-mcp`.
3. Confirm it's enabled. The addon's panel (or Blender's System Console)
   should show the socket server listening on port 9876.

## Connecting from Claude's side

- Once the MCP connector for Blender is active in the chat, tools appear
  with a `Blender:` prefix. If they're not visible, call `tool_search` with
  a query like "blender execute code" to load them -- this MCP's tools are
  deferred by default, same as any other connector.
- Available tools (26 total), grouped by purpose:
  - **Code execution**: `execute_blender_code`, `execute_blender_code_for_cli`
    -- this is the workhorse; nearly everything in this project runs through it.
  - **File/scene summaries**: `get_blendfile_summary_datablocks`,
    `get_blendfile_summary_missing_files`,
    `get_blendfile_summary_of_linked_libraries`,
    `get_blendfile_summary_path_info`, `get_blendfile_summary_usage_guess`
    (each has a `_for_cli` twin)
  - **Object introspection**: `get_objects_summary`, `get_object_detail_summary`
  - **Navigation**: `jump_to_tab_by_name`, `jump_to_tab_by_space_type`,
    `jump_to_view3d_object_by_name`, `jump_to_view3d_object_data_by_name`
  - **Screenshots**: `get_screenshot_of_area_as_image`,
    `get_screenshot_of_window_as_image`, `get_screenshot_of_window_as_json`,
    `render_thumbnail_to_path`, `render_viewport_to_path` -- see the pitfall
    below before reaching for any of these.
  - **Docs**: `get_python_api_docs`, `search_api_docs`, `search_manual_docs`
- **The first command after a fresh connection sometimes fails or times out
  silently.** This is a known quirk, not a sign the connection is broken.
  Retry once before troubleshooting further.
- Minimal connectivity test -- run this via `execute_blender_code` first in
  any new session:
  ```python
  import bpy
  result = {"blender_version": bpy.app.version_string, "objects": len(bpy.data.objects)}
  ```
  A JSON result coming back confirms the link is live.

## The screenshot pitfall (read this before trying to "see" the scene)

Screenshots return as PNG, budgeted at roughly 786KB (a ~1MB message limit
at ~3/4 efficiency once base64-encoded), further halved for HiDPI displays,
then iteratively downscaled again if still oversized. **In practice this
means anything but the simplest scene arrives too degraded for Claude to
read reliably** -- even though the transport succeeds and the image looks
perfectly fine on the human's own screen. Reference images the user uploads
directly (not screenshots Claude requests from Blender) are unaffected and
arrive fine.

Do not rely on the screenshot tools for verifying geometry. This project
exists specifically to route around this limitation: `eye.py` renders the
scene as text (ASCII), which always survives transport intact. Use that
instead. See `skills/blender-connect/SKILL.md`.

## The socket patch (large-payload fix)

- Upstream bug: projects.blender.org/lab/blender_mcp/issues/21 --
  `sendall()` on a non-blocking socket silently truncates large sends
  (observed failure around ~61 bytes) on macOS, corrupting large responses
  (symptom: `Unterminated string` JSON parse errors on the Claude side).
- Fix applied locally: a `_sendall_blocking()` helper added at the 3 call
  sites in `mcp_to_blender_server.py` (inside the addon's install folder,
  path above) that previously called the raw non-blocking `sendall()`.
- A backup of the pre-patch file is kept alongside it:
  `mcp_to_blender_server.py.bak`.
- **This patch does not survive an addon reinstall or update** -- Blender's
  extension manager will overwrite the file and silently revert it. If large
  payloads start failing again after an update, that's the first thing to
  check. The exact change is documented in `PATCHES.md` in this repo, and can
  be diffed against the `.bak` file.
- Given the screenshot pitfall above, most day-to-day work doesn't depend on
  large payloads anyway -- but keep the patch in place regardless, since any
  sufficiently large `execute_blender_code` response (e.g., large mesh
  summaries) can hit the same bug.

## What lives on top of the connection

Once connected, this project layers a full toolkit over raw
`execute_blender_code`. This document stops here on purpose -- for how to
actually work (vision, measurement, calibration doctrine, the part-graph
system), go to `skills/blender-connect/SKILL.md` and its `references/`
folder next. In brief, what's there:

- `eye.py` -- text-based scene rendering (id / edges / depth / shade modes)
- `senses.py` -- proportion, contour-angle, rotation, hardness, silhouette,
  cavity, and occupancy-grid senses
- `mesh_mind.py` -- part-graph / continuity-contract layer for structured,
  non-destructive multi-part edits
- `masterwork_ledger.md` -- running log of calibration loops and findings

## Quick troubleshooting checklist

1. Tools not appearing? -> `tool_search` for "blender".
2. First call fails or times out? -> retry once, it's a known quirk.
3. Screenshots illegible or garbled? -> expected; don't use them, use the
   text-vision toolkit instead.
4. Truncated/corrupted JSON on a large response? -> the socket patch may
   have reverted after an addon update; check `PATCHES.md`.
5. Repo or toolkit files not found where expected? -> confirm which repo:
   `~/Developer/blenderTools` (GitHub-connected, promoted/stable code) vs
   `~/Developer/blender-connect-experiment` (local sandbox, git-uncommittable
   -- not in the account allowlist).
6. Unsure which addon is running? -> confirm it's the official Blender MCP
   (blender.org/lab/mcp-server). If Python errors reference `addon.py`
   directly or method names don't match what's documented here, it may be
   the wrong (ahujasid) addon installed instead.

## Repo locations

- **Promoted / GitHub-connected**: `~/Developer/blenderTools`
  (remote: `git@github-personal:freyjay/blender_connect.git`)
- **Local experiment sandbox**: `~/Developer/blender-connect-experiment`
  (proven code gets promoted from here to the repo above; not itself
  committable under the current git-hook allowlist)
