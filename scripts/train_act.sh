#!/bin/bash

export PYTHONPATH=/home/mira/Projects/cube/src:/home/mira/Projects/cube/thirdparty/lerobot/src

/home/mira/mambaforge/envs/cube/bin/python -m lerobot.scripts.train \
    --dataset.repo_id=MichaelRazum/cube \
    --policy.push_to_hub=false \
    --policy.device=cuda \
    --policy.type=act \
    --wandb.enable=true \
    --wandb.project=xarm-act-training\
    --batch_size=4\
    --steps=100000
