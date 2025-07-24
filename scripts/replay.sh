export PYTHONPATH=/home/mira/Projects/cube/src:/home/mira/Projects/cube/thirdparty/lerobot/src
/home/mira/mambaforge/envs/cube/bin/python /home/mira/Projects/cube/scripts/xarm_replay.py \
    --robot.port=/dev/ttyUSB0 \
    --robot.id=my_xarm \
    --dataset.repo_id=MichaelRazum/cube-test \
    --dataset.episode=0