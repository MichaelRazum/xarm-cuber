#!/bin/bash

TOP_USB_PATH="4.2.3"    # Top camera USB path
FRONT_USB_PATH="14.0"  # Front camera USB path

CAMERAS_CONFIG=$(python3 scripts/find_cameras.py "$TOP_USB_PATH" "$FRONT_USB_PATH")

/home/mira/mambaforge/envs/cube/bin/python scripts/xarm_record.py \
    --robot.cameras="$CAMERAS_CONFIG" \
    --robot.type=xarm_follower \
    --robot.port=/dev/ttyUSB0 \
    --teleop.type=xarm_leader \
    --teleop.port=/dev/ttyUSB1 \
    --dataset.repo_id=MichaelRazum/cube-test\
    --dataset.single_task="flip" \
    --dataset.num_episodes=5 \
    --dataset.episode_time_s=30 \
    --display_data=true\
    --resume=false
