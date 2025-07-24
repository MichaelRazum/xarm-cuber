TOP_USB_PATH="4.2.3"
FRONT_USB_PATH="14.0"

CAMERAS_CONFIG=$(python3 scripts/find_cameras.py "$TOP_USB_PATH" "$FRONT_USB_PATH")

/home/mira/mambaforge/envs/cube/bin/python scripts/xarm_teleoperate.py \
    --robot.cameras="$CAMERAS_CONFIG" \
    --robot.type=xarm_follower \
    --robot.port=/dev/ttyUSB1 \
    --teleop.type=xarm_leader \
    --teleop.port=/dev/ttyUSB0 \
    --display_data=true
