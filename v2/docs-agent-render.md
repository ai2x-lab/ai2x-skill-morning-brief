# v2 Agent Render Contract

## Target flow
1. Skill collects data and builds draft
2. Skill builds agent instruction from configure
3. Agent renders final script (no skill-side API key management)
4. Skill sends rendered script to TTS
5. Delivery is optional adapter (default `delivery.mode=none`)

## Configure key
- `render.mode`: `agent` or `self`
- `render.fallback_mode`: `self` or `none`
- `render.agent_instruction_template`: prompt template built from configure

## Why this design
- Decouples model/API key from skill
- Keeps output style controllable via configure
- Preserves deterministic fallback when agent is unavailable
- Supports richer multi-source candidate packet for agent-level selection
