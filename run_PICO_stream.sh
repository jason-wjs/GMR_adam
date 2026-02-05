#!/usr/bin/env bash
set -euo pipefail

python scripts/xrobot_live_to_robot.py \
  --robot adam_pro_29dof \
  --actual_human_height 1.8 \
  --target_fps 30 \
  --measure_fps \
  # --show_human \
  # --show_human_names \
  # --no_offset_to_ground \
  # --no_rate_limit \
  # --no_follow_camera
