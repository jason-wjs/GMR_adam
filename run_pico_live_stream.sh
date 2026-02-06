#!/usr/bin/env bash
set -euo pipefail

python scripts/xrobot_live_to_robot.py \
  --robot adam_pro_29dof \
  --actual_human_height 1.69 \
  --target_fps 30 \
  --measure_fps \
  --root_z_comp -0.03 \
  --record_with_controller \
  --session_dir converted_motions/pico_live/adam_pro_29dof/walk
  #--session_dir converted_motions/pico_live/adam_pro_29dof/dance

# Optional:
#   --save_on_exit
#   --show_human
#   --show_human_names
#   --no_offset_to_ground
#   --no_rate_limit
#   --no_follow_camera
