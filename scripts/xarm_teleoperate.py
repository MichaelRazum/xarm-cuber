from dataclasses import asdict
from pprint import pformat
import rerun as rr
import logging
import draccus

from lerobot.teleoperate import TeleoperateConfig, teleop_loop
from lerobot.utils.utils import init_logging
from lerobot.utils.visualization_utils import _init_rerun
from xarm import XArmFollower
from xarm.lerobot.xarm_teleop import XArmLeader


@draccus.wrap()
def teleoperate(cfg: TeleoperateConfig):
    init_logging()
    logging.info(pformat(asdict(cfg)))
    if cfg.display_data:
        _init_rerun(session_name="teleoperation")

    teleop = XArmLeader(cfg.teleop)
    robot = XArmFollower(cfg.robot)

    teleop.connect()
    robot.connect()

    try:
        teleop_loop(teleop, robot, cfg.fps, display_data=cfg.display_data, duration=cfg.teleop_time_s)
    except KeyboardInterrupt:
        pass
    finally:
        if cfg.display_data:
            rr.rerun_shutdown()
        teleop.disconnect()
        robot.disconnect()


if __name__ == "__main__":
    teleoperate()
