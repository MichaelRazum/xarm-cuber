/home/mira/mambaforge/envs/cube/bin/python scripts/xarm_teleoperate.py \
    --robot.type=xarm_follower \
    --robot.port=/dev/ttyUSB0 \
    --teleop.type=xarm_leader \
    --teleop.port=/dev/ttyUSB1 \
    --display_data=true
