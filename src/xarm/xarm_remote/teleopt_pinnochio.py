import numpy as np
import pink

import pinocchio as pin
import qpsolvers
from pink import FrameTask, PostureTask, custom_configuration_vector, solve_ik

def get_rotation_angle(p):
    return np.arctan2(p[1], p[0])

def derotate(p, P, theta):
    R = pin.utils.rpyToMatrix(0, 0, theta)
    p_r = R.T @ p
    P_r = R.T@ P.toRotationMatrix()
    return p_r, pin.Quaternion(P_r)


class Controller:
    def __init__(self, urdf_path, end_effector:str, solver='quadprog'):
        self.robot = pin.RobotWrapper.BuildFromURDF(
            filename=urdf_path,
            package_dirs=["."],
            root_joint=None,
        )
        self.end_effector_task = FrameTask(
                                end_effector,
                                position_cost=10.0,  # [cost] / [m]
                                orientation_cost=.1,  # [cost] / [rad]
                                lm_damping=1.5,  # tuned for this setup
                            )
        self.posture_task = PostureTask(
            cost=1e-3,  # [cost] / [rad]
        )
        q_ref = custom_configuration_vector(
            self.robot,
        )
        self.configuration = pink.Configuration(self.robot.model, self.robot.data, q_ref)
        self.tasks = [self.end_effector_task, self.posture_task]
        for task in self.tasks:
            task.set_target_from_configuration(self.configuration)

        if solver not in qpsolvers.available_solvers:
            raise Exception(f'unknown solver {solver}')
        self.solver = solver

    def _ik_step(self, x,y,z,r):
        target = self.end_effector_task.transform_target_to_world
        target.translation[0] = x
        target.translation[1] = y
        target.translation[2] = z
        target.rotation = r
        dt = 0.1
        velocity = solve_ik(self.configuration,
                            self.tasks,
                            dt,
                            solver=self.solver,
                            barriers=[],
                            safety_break=False)
        
        # Only integrate for non-fixed joints
        nv = self.robot.nv
        self.configuration.integrate_inplace(velocity[:nv], dt)
        return self.configuration.q

    def ik(self, x, y, z, r):
        # TODO: Add breaking criterion or do step by step control
        for _ in range(50):
            self._ik_step(x, y, z, r)
        return self.configuration.q