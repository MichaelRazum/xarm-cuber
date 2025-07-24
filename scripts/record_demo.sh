#!/bin/bash

TOP_USB_PATH="4.2.3"    # Top camera USB path
FRONT_USB_PATH="14.0"  # Front camera USB path

CAMERAS_CONFIG=$(python3 scripts/find_cameras.py "$TOP_USB_PATH" "$FRONT_USB_PATH")

/home/mira/mambaforge/envs/cube/bin/python scripts/xarm_record.py \
    --robot.cameras="$CAMERAS_CONFIG" \
    --robot.type=xarm_follower \
    --robot.port=/dev/ttyUSB1 \
    --teleop.type=xarm_leader \
    --teleop.port=/dev/ttyUSB0 \
    --dataset.repo_id=MichaelRazum/cube\
    --dataset.single_task="flip" \
    --dataset.num_episodes=50 \
    --dataset.episode_time_s=30 \
    --display_data=true\
    --resume=false
