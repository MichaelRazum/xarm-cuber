import time
import torch

from lerobot.configs import parser
from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.datasets.utils import build_dataset_frame, hw_to_dataset_features
from lerobot.policies.factory import make_policy
from lerobot.record import RecordConfig
from lerobot.utils.control_utils import predict_action
from lerobot.utils.robot_utils import busy_wait
from lerobot.utils.utils import get_safe_torch_device
from lerobot.utils.visualization_utils import log_rerun_data, _init_rerun
from xarm import XArmFollower


class ActController:
    def __init__(self,
                 cfg,
        ):
        self.follower = XArmFollower(cfg.robot)
        self.follower.connect()
        self.__dataset = LeRobotDataset(
            cfg.dataset.repo_id,
            root=cfg.dataset.root,
        )
        self.policy = make_policy(cfg.policy, ds_meta=self.__dataset.meta)
        _init_rerun('solving')
        self.set_default_position('flip')

    def set_default_position(self, task=""):
        self.follower.move_to_default_position(task=task)

    def execute_task(self, task, shared_img=None, display_data=True, time_task=30):
        torch.cuda.empty_cache()
        policy = self.policy
        policy.reset()
        self.follower.get_observation()
        self.set_default_position(task)

        start_loop_t = time.perf_counter()
        while time.perf_counter() - start_loop_t < time_task:
            observation = self.follower.get_observation()
            observation_frame = build_dataset_frame(self.__dataset.features, observation, prefix="observation")
            action_values = predict_action(
                observation_frame,
                policy,
                get_safe_torch_device(policy.config.device),
                policy.config.use_amp,
                task=task,
                robot_type=self.follower.robot_type,
            )
            if is_position_end_position(action_values):
                print('END POSITION DETECTED')
                print(f'ACTION FINISHED {task} execution finished')
                print(action_values)
                break
            action = {key: action_values[i].item() for i, key in enumerate(self.follower.action_features)}
            self.follower.send_action(action)
            if display_data:
                log_rerun_data(observation, action)
            if shared_img is not None:
                shared_img.copy_(torch.from_numpy(observation['front']))

            dt_s = time.perf_counter() - start_loop_t
            # print(1 / self.__dataset.fps - dt_s)
            busy_wait(1 / self.__dataset.fps - dt_s)

        print(f'ACTION FINISHED {task} execution finished')
        print(action_values)
        self.set_default_position(task)


action_id2task_and_time = {
    1: ('Flip the Cube', 20),
    2: ('Rotate Left Cube', 60),
    3: ('Rotate Right Cube', 60),
    4: ('Torn Left Top Cube', 60),
    5: ('Torn Left Top Cube', 60),
    6: ('Move Cube to Center', 60),
}


def run_robot(cfg, shared_img, busy, action):
    print('starting run')
    controller = ActController(cfg)
    while True:
        try:
            if action.value == 0:
                observation = controller.follower.get_observation()
                log_rerun_data(observation, dict())
                shared_img.copy_(torch.from_numpy(observation['front']))
            else:
                with busy.get_lock():
                    busy.value = True


                task, time_task = action_id2task_and_time[action.value]
                print(f"executing action {task} with RUNTIME {time_task}")
                controller.execute_task(task=task, time_task=time_task, shared_img=shared_img)

                task, time_task = action_id2task_and_time[6]
                print(f"executing action {task} with RUNTIME {time_task}")
                controller.execute_task(task=task, time_task=time_task, shared_img=shared_img)
        except Exception as e:
            print(f'Got Exception {e}')
        finally:
            if busy.value:
                with busy.get_lock():
                    busy.value = False



if __name__ == '__main__':
    @parser.wrap()
    def get_cfg(cfg: RecordConfig):
        return cfg
    cfg = get_cfg()
    controller = ActController(cfg)
    if cfg.display_data:
        _init_rerun(session_name="recording")
    controller.execute_task('flip', display_data=True)


def is_position_end_position(position: torch.tensor, max_derivation=70, verbose=False):
    # Heuristics
    position = position
    weights = [torch.asarray([0, 1, .05, .1, .8, .2]),
               torch.asarray([0.3, 1.0, .6, .0, .4, .5]),
               torch.asarray([0.3, 1.0, .6, .0, .4, .5]),
               ]
    targets = [torch.asarray([0, 500., 185., 900., 870., 500.]),
               torch.asarray([50, 950, 50, 650, 500, 500]),
               torch.asarray([50, 150, 50, 650, 500, 500]),
               ]

    for (weight, target) in zip(weights, targets):
        abs_derivation =  weight @ (position - target).abs()
        if verbose:
            for i in range(6):
                print(f'[{i}] target {target[i]:1.1f} pos {position[i]:1.1f} '
                      f'diff {target[i] - position[i]:1.1f} '
                      f'diff weight {(target[i] - position[i])*weight[i]:1.1f}')
            print(f'=> abs_derivation = {abs_derivation:1.1f}')
        if abs_derivation < max_derivation:
            return True
    return False