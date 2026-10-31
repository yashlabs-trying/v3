#!/bin/bash
P=/home/yashs/.local/share/uv/tools/harbor/lib/python3.12/site-packages/harbor/agents/installed/mini_swe_agent.py
sed -n '1,220p' "$P"
