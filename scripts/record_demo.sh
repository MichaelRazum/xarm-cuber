#!/bin/bash

export PYTHONPATH=/home/mira/Projects/cube/src:/home/mira/Projects/cube/thirdparty/lerobot/src

# Camera USB paths - adjust these to match your setup
TOP_USB_PATH="4.2.3"    # Top camera USB path
FRONT_USB_PATH="6.1.4"  # Front camera USB path

# Find cameras by USB path
CAMERAS_CONFIG=$(python3 scripts/find_cameras.py "$TOP_USB_PATH" "$FRONT_USB_PATH")

if [ $? -ne 0 ]; then
    echo "Failed to find cameras. Please check USB paths in script."
    exit 1
fi

echo "Found cameras: $CAMERAS_CONFIG"

# Generate unique repo_id with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
REPO_ID="xarm_demo_${TIMESTAMP}"

echo "Dataset repo_id: $REPO_ID"

# Run recording with camera configuration
/home/mira/mambaforge/envs/cube/bin/python scripts/xarm_record.py \
    --robot.type=xarm_follower \
    --robot.cameras="$CAMERAS_CONFIG" \
    --teleop.type=xarm_leader \
    --dataset.repo_id="$REPO_ID" \
    --dataset.single_task="Pick and place demonstration" \
    --dataset.num_episodes=5 \
    --dataset.episode_time_s=30 \
    --display_data=true