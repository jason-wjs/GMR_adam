#!/usr/bin/env bash
set -euo pipefail


python scripts/fbx_offline_to_robot.py \
    --motion_file /home/humanoid/Downloads/Data/GMR_test/FBX/dance.pkl \
    --robot adam_pro_29dof \
    #--save_path /home/humanoid/Downloads/Data/GMR_test/Robot/dance.pkl \
    #--rate_limit