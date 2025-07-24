from dataclasses import asdict, dataclass
from pathlib import Path
from pprint import pformat
import logging
import time

import draccus

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.utils import init_logging, log_say
from xarm import XArmFollower
from xarm.lerobot.config_xarm_follower import XArmFollowerConfig


@dataclass
class DatasetReplayConfig:
    # Dataset identifier. By convention it should match '{hf_username}/{dataset_name}' (e.g. `lerobot/test`).
    repo_id: str
    # Episode to replay.
    episode: int
    # Root directory where the dataset will be stored (e.g. 'dataset/path').
    root: str | Path | None = None
    # Limit the frames per second. By default, uses the policy fps.
    fps: int = 30


@dataclass
class ReplayConfig:
    robot: XArmFollowerConfig
    dataset: DatasetReplayConfig
    # Use vocal synthesis to read events.
    play_sounds: bool = True


@draccus.wrap()
def replay(cfg: ReplayConfig):
    init_logging()
    logging.info(pformat(asdict(cfg)))

    robot = XArmFollower(cfg.robot)
    dataset = LeRobotDataset(cfg.dataset.repo_id, root=cfg.dataset.root, episodes=[cfg.dataset.episode])
    actions = dataset.hf_dataset.select_columns("action")
    
    robot.connect()

    log_say(f"Replaying episode {cfg.dataset.episode} with {dataset.num_frames} frames", cfg.play_sounds, blocking=True)
    
    for idx in range(dataset.num_frames):
        start_episode_t = time.perf_counter()

        action_array = actions[idx]["action"]
        action = {}
        for i, name in enumerate(dataset.features["action"]["names"]):
            action[name] = action_array[i]

        robot.send_action(action)

        dt_s = time.perf_counter() - start_episode_t
        busy_wait(1 / dataset.fps - dt_s)

    robot.disconnect()
    log_say("Replay completed", cfg.play_sounds, blocking=True)


if __name__ == "__main__":
    replay()