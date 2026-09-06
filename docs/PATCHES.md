# PATCHES.md

## 1. mcp_to_blender_server.py -- sendall on non-blocking socket (upstream #21)
File: Blender extension `user_default/mcp/mcp_to_blender_server.py`
Backup: `mcp_to_blender_server.py.bak` (same folder)

Stock v1.0.0 sets client sockets non-blocking, then uses `sendall()`;
on macOS the kernel send buffer fills (~61 bytes observed), `BlockingIOError`
is swallowed by `except OSError: pass`, and large responses (screenshots)
are silently truncated. Fix: `_sendall_blocking()` helper -- temporarily
blocking send, restore non-blocking after. Applied at 3 call sites.
NOTE: reinstalling/updating the extension reverts this patch.

## 2. Screenshot toolcode findings (server-side, not patchable locally)
Captured via request interceptor: tool sends PNG, budget = (1MB * 3/4) b64,
HiDPI images halved to logical pixels, then downscaled ITERATIVELY until
the PNG fits. Complex content (grids, many small objects) -> aggressive
downscale -> illegible to the agent. Countermeasure abandoned in favor of
`eye.py` (text-based vision).
