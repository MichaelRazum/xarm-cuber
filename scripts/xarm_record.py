from dataclasses import asdict
from pprint import pformat
import logging

from lerobot.configs import parser
from lerobot.record import RecordConfig, record_loop
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.utils import hw_to_dataset_features
from lerobot.utils.utils import init_logging
from lerobot.utils.visualization_utils import _init_rerun
from lerobot.utils.control_utils import init_keyboard_listener
from xarm import XArmFollower
from xarm.lerobot.xarm_teleop import XArmLeader


def record_core(cfg: RecordConfig) -> LeRobotDataset:
    """Core recording logic that can be called programmatically."""
    init_logging()
    logging.info(pformat(asdict(cfg)))
    if cfg.display_data:
        _init_rerun(session_name="recording")

    robot = XArmFollower(cfg.robot)
    teleop = XArmLeader(cfg.teleop) if cfg.teleop is not None else None

    action_features = hw_to_dataset_features(robot.action_features, "action", cfg.dataset.video)
    obs_features = hw_to_dataset_features(robot.observation_features, "observation", cfg.dataset.video)
    dataset_features = {**action_features, **obs_features}

    # Create dataset
    dataset = LeRobotDataset.create(
        cfg.dataset.repo_id,
        cfg.dataset.fps,
        root=cfg.dataset.root,
        robot_type=robot.name,
        features=dataset_features,
        use_videos=cfg.dataset.video,
        image_writer_processes=cfg.dataset.num_image_writer_processes,
        image_writer_threads=cfg.dataset.num_image_writer_threads_per_camera * len(robot.cameras),
    )

    robot.connect()
    if teleop is not None:
        teleop.connect()

    listener, events = init_keyboard_listener()

    recorded_episodes = 0
    while recorded_episodes < cfg.dataset.num_episodes and not events["stop_recording"]:
        # Record episode
        record_loop(
            robot=robot,
            events=events,
            fps=cfg.dataset.fps,
            dataset=dataset,
            teleop=teleop,
            control_time_s=cfg.dataset.episode_time_s,
            single_task=cfg.dataset.single_task,
            display_data=cfg.display_data,
        )
        recorded_episodes += 1

    robot.disconnect()
    if teleop is not None:
        teleop.disconnect()

    return dataset


@parser.wrap()
def record(cfg: RecordConfig) -> LeRobotDataset:
    """CLI entry point with draccus command line parsing."""
    return record_core(cfg)


if __name__ == "__main__":
    record()