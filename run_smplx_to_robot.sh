#!/usr/bin/env bash
set -euo pipefail

python scripts/smplx_to_robot.py \
  --smplx_file /home/humanoid/Downloads/Data/GMR_test/AMASS/General_A6_-_Lift_Box_stageii.npz \
  --robot adam_pro_29dof \
  --loop
  #--rate_limit 
  #--save_path "<OPTIONAL_OUTPUT.pkl>" \
  #--record_video \
