import time
import os
from rubikvision.cube_solver import CubePlanner
import numpy as np
import cv2

from lerobot.utils.visualization_utils import log_rerun_data, _init_rerun


def run_planner(shared_img, busy, action, plot_bounding_box=False, plot_projection=False,
              plot_cube_state=True, rotate_img=True):
    print('starting cube_planer')
    _init_rerun("solving")
    cube_planner = CubePlanner(K=np.array([[632.11326486, 0., 316.16980761],
                                           [0., 630.54696352, 233.72252151],
                                           [0., 0., 1.]]),
                               init_thread=False)
    executing_action = ""
    n = 0
    while True:
        try:
            if busy.value:
                cube_planner.action_executor.current_action = ""

            image = cv2.cvtColor(shared_img.numpy(), cv2.COLOR_RGB2BGR)
            print(f'processing frame {(n:=n+1)}')
            os.makedirs("outputs", exist_ok=True)
            cv2.imwrite(f'outputs/img_{n}_{busy.value}.png', image)

            cube_planner.init_image(image, rotate_img=rotate_img)
            cube_planner.estimate_step(busy=bool(busy.value))

            if action_str:=cube_planner.action_executor.current_action:
                executing_action = action_str
                print(f' CUBE-SOLVER new action {executing_action}')
                with action.get_lock():
                    if action_str == 'flip':
                        action.value = 1
                    elif action_str == 'rotate_left':
                        action.value = 2
                    elif action_str == 'rotate_right':
                        action.value = 3
                    elif action_str == 'rotate_upper_left':
                        action.value = 4
                    elif action_str == 'rotate_upper_right':
                        action.value = 5
                    else:
                        raise Exception(f'unknown action {action_str}')
            else:
                with action.get_lock():
                    action.value = 0
            time.sleep(0.2)
            if rotate_img:
                image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
            cube_planner.plot(image,
                              plot_bounding_box=plot_bounding_box,
                              plot_projection=plot_projection,
                              plot_cube_state=plot_cube_state,
                              action=executing_action)
            log_rerun_data({'solver':cv2.cvtColor(image, cv2.COLOR_BGR2RGB)}, dict())

        except Exception as e:
            print(f'Got Exception {e}')


