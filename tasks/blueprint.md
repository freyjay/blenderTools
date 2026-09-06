# Blueprint -- blender_connect

## Vision
Give an AI agent reliable senses and hands inside Blender, so human + AI can
model 3D scenes collaboratively: the human provides aesthetic judgment and
ground truth; the agent provides exact math, automation, and tireless iteration.

## The 5 Key Questions
1. **What are we building?** Not a web app -- an agent sensory/tooling layer
   for Blender over MCP (Python-in-Blender + local repo of instruments).
2. **Core features:** text-based vision (ray-cast ASCII renders, scanlines),
   spatial verification (occlusion, depth, measurements), calibration
   protocols against human observation, patch management for the MCP stack.
3. **Users / problem:** Francis + Claude. Problem: MCP image transport is
   lossy/unreliable, so the agent needs senses that survive the wire.
4. **Technical:** Blender 5.1.2 (Python 3.13), official Blender MCP addon
   v1.0.0 (patched, see PATCHES.md), pure-Python instruments, no external deps.
5. **Scope:** evolving instrument -- v0.1 proven against human ground truth
   (front-view occlusion of calibration rig reproduced exactly by scanline).

## Principles
- Math is the primary sense; human eyes are the audit.
- Never guess what you cannot see; verify or say so.
- Experiment repo -> promote proven code -> GitHub repo.
