#!/usr/bin/env bash
set -euo pipefail

python scripts/bvh_to_robot.py \
  --bvh_file /home/humanoid/Downloads/Data/GMR_test/lafan1/dance1_subject1.bvh \
  --format lafan1 \
  --robot adam_sp_29dof \
  --motion_fps 30 \
  # --save_path "<OPTIONAL_OUTPUT.pkl>" \
  # --record_video \
  # --video_path "<OPTIONAL_OUTPUT.mp4>" \
  # --rate_limit

