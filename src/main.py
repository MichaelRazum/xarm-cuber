import time
import warnings

import torch

from action_controller import run_robot
from lerobot.configs import parser
from lerobot.record import RecordConfig
import torch.multiprocessing as mp

from cube_solver import run_planner


@parser.wrap()
def get_cfg(cfg: RecordConfig):
    return cfg


if __name__ == "__main__":
    warnings.filterwarnings("ignore", module="retry")
    torch.multiprocessing.set_start_method('spawn')

    H, W = 480, 640
    shared_img = torch.empty((H, W, 3), dtype=torch.uint8).share_memory_()
    busy = mp.Value('b', False)
    action = mp.Value('i', 0)

    cfg = get_cfg()
    p_robot = mp.Process(target=run_robot, args=(cfg, shared_img, busy, action))
    p_robot.start()
    time.sleep(10)
    p_planer = mp.Process(target=run_planner, args=(shared_img, busy, action))
    p_planer.start()

    p_robot.join()