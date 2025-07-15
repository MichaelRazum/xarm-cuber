import json
import time
from pathlib import Path
import numpy as np
import meshcat_shapes
import pinocchio as pin
import redis
from ikpy.chain import Chain
from pink.visualization import start_meshcat_visualizer
import meshcat
import meshcat.geometry as g
import meshcat.transformations as tranform
from teleopt import BusServoRemoteTelopt
from teleopt_pinnochio import Controller, get_rotation_angle


def plot_point(viz, x, y, z, color, line_length=0.1, line_thickness=0.01, name='x_'):
    """
    Adds a big red "X" at the specified coordinates in the MeshCat visualizer.

    Parameters:
    viz (meshcat.Visualizer or its equivalent): The MeshCat visualizer object.
    x, y, z (float): The coordinates where the "X" should be placed.
    line_length (float): The length of each line in the "X". Default is 0.1.
    line_thickness (float): The thickness of each line in the "X". Default is 0.01.
    """
    # Step 1: Define the position of the point
    assert color in {'green', 'yellow', 'red', 'blue'}
    name = name + color
    color_map = {'green':0x00ff00, 'yellow':0xffff00, 'red':0xff0000, 'blue':0x0000FF}
    point_position = np.array([x, y, z])

    # Step 2: Create the "X" geometry (two crossing lines)
    line1 = g.Cylinder(line_length, line_thickness)
    line2 = g.Cylinder(line_length, line_thickness)

    # Step 3: Create transformations for the "X" shape
    line1_transform = meshcat.transformations.rotation_matrix(np.pi / 4, [0, 0, 1])
    line1_transform[:3, 3] = point_position

    line2_transform = meshcat.transformations.rotation_matrix(-np.pi / 4, [0, 0, 1])
    line2_transform[:3, 3] = point_position

    # Step 4: Set the color of the "X" to red

    material = g.MeshLambertMaterial(color=color_map[color])

    # Step 5: Add the lines to the MeshCat visualizer
    viz.viewer[f'{name}1'].set_object(line1, material)
    viz.viewer[f'{name}1'].set_transform(line1_transform)

    viz.viewer[f"{name}2"].set_object(line2, material)
    viz.viewer[f"{name}2"].set_transform(line2_transform)

def delete_point(color, name='x'):
    assert color in {'green', 'yellow', 'red', 'blue'}
    name = name + color
    viz.viewer[f'{name}1'].delete()
    viz.viewer[f'{name}2'].delete()

def set_camera_perspective(viewer):
    translation = [-2., 1., -.2]  # [x, y, z] position of the camera
    rotation = tranform.rotation_matrix(np.radians(0), [0, 1, 0])
    camera_transform = tranform.translation_matrix(translation) @ rotation
    viewer["/Cameras/default"].set_transform(camera_transform)
    viewer["/Cameras/default"].set_property("vertical_fov", 1.0)  # FOV in radians


def setup_visualization(contr):
    viz = start_meshcat_visualizer(contr.robot)
    viz.display(contr.configuration.q)
    viewer = viz.viewer
    meshcat_shapes.frame(viewer["end_effector_target"], opacity=0.5)
    meshcat_shapes.frame(viewer["end_effector"], opacity=1.0)
    return viz

def update_viewer(viewer, contr: Controller):
    viewer["end_effector_target"].set_transform(contr.end_effector_task.transform_target_to_world.np)
    viewer["end_effector"].set_transform(
        contr.configuration.get_transform_frame_to_world(
            contr.end_effector_task.frame
        ).np
    )

class VrStream:
    def __init__(self):
        self.r = redis.StrictRedis()

        self.T = np.eye(3)
        self.R = np.eye(3)

        self.control_mode = False
        self.rel_pos = None

    def do_control(self):
        inputs = json.loads(self.r.get('right_hand_inputs'))
        do_control = inputs['button_lower']
        return do_control

    def get_target_relativ(self, old_pos):
        do_control = self.do_control()
        if do_control is True:
            x,y,z, r = self.get_target(rotate=False)
            p_cntr = np.array([x,y,z])
            if self.control_mode is False:
                self.control_mode = True
                self.rel_pos = old_pos.translation - p_cntr
                x,y,z  = old_pos.translation
                return x,y,z, old_pos.rotation
            else:
                new_pos = self.rel_pos+p_cntr
                x,y,z = new_pos
                return x,y,z,r
        else:
            x, y, z = old_pos.translation
            return x, y, z, old_pos.rotation






    def get_target(self, rotate=True):
        right_pose = json.loads(self.r.get('right_hand_pose'))
        pose_r = right_pose['pose']
        x = pose_r['orientation']['x']
        y = pose_r['orientation']['y']
        z = pose_r['orientation']['z']
        w = pose_r['orientation']['w']
        quat = pin.Quaternion(w, x, y, z)
        rotation_matrix = quat.toRotationMatrix()

        x =  pose_r['position']['x']
        y =  pose_r['position']['y']
        z =  pose_r['position']['z']

        if rotate:
            x, y, z, rotation_matrix = self.rotate_coordinate_system(x, y, z,  quat.toRotationMatrix())


        rotation_matrix_ret = self.R.T @ rotation_matrix
        x,y,z  = self.R.T @ np.array([x,y,z])

        return x*0.7,y*0.7,z*0.7, rotation_matrix_ret

    def set_rotation(self, x,y,z):
        # Calculate the rotation angle using the get_rotation_angle function
        angle = get_rotation_angle(np.array([x, y, z], dtype=np.float32))
        rotation_matrix = pin.utils.rpyToMatrix(0, 0, float(angle))
        self.R = rotation_matrix

    def set_coordinate_system(self, p_x, p_y, p_z):
        # Target points
        x_target = np.array([0.4, 0, 0])
        y_target = np.array([0, 0.4, 0])
        z_target = np.array([0, 0, 0.4])

        # Construct matrices
        original_matrix = np.vstack([p_x, p_y, p_z]).T
        target_matrix = np.vstack([x_target, y_target, z_target]).T

    # Calculate transformation matrix
        transformation_matrix = np.linalg.inv(original_matrix) @ target_matrix
        self.T = transformation_matrix

    def button_lower_pressed(self):
        inputs = json.loads(self.r.get('right_hand_inputs'))
        return inputs['button_lower']

    def rotate_coordinate_system(self, x, y, z, rotation_matrix):
        # Create a rotation matrix that rotates 180 degrees around the Y axis
        rotation_y_180 = pin.utils.rpyToMatrix(0, 0, np.pi)
        new_rotation_matrix = rotation_y_180 @ rotation_matrix
        position = np.array([x, y, z])
        new_position = rotation_y_180 @ position
        return new_position[0], new_position[1], new_position[2], new_rotation_matrix

def pos2pwm(pos:np.ndarray) -> np.ndarray:
    """
    :param pos: numpy array of joint positions in range [-pi, pi]
    :return: numpy array of pwm values in range [0, 4096]
    """
    return (pos /  4.19 + 1.) * 500

def follower_update(q ,vr_stream ):
    r = vr_stream.r
    do_control = vr_stream.do_control()
    positions = follower.read_position()
    MAX_MOV = 120

    q = q[::-1]
    positions_new = positions.copy()
    if do_control:
        positions_new[5] =  max(min((q[4] / 2.06 + 1.) * 500, 1000), 0) # Rotation Base
        positions_new[4] =  max(min((q[3] / 2.06 + 1.) * 500, 1000), 0) # Arm Button
        positions_new[3] =  max(min((q[2] / 2.06 + 1.) * 500, 1000), 0) # Arm middle (negativ angle)
        positions_new[2] =  max(min((q[1] / 2.06 + 1.) * 500, 900), 100) # Arm Top
        positions_new[1] =  max(min((q[0] / 2.05 + 1.) * 500, 1000), 0) # Rotation Arms
        # positions_new[0] =  positions[0]                                # Gripper ARms
        right_inputs = json.loads(r.get('right_hand_inputs'))
        if right_inputs['press_index'] > 0:
            cmd_grip = max(min(follower.last_position[0] + 75 * right_inputs['press_index'],1000),0)
        elif right_inputs['press_middle'] > 0:
            cmd_grip = max(min(follower.last_position[0] + -75 * right_inputs['press_middle'],1000),0)
        else:
            cmd_grip = follower.last_position[0]
        positions_new[0] = cmd_grip

    positions_final = []
    for p, p0 in zip(positions_new,positions):
        delta = p-p0
        positions_final.append(np.sign(delta) * min(np.abs(delta), MAX_MOV) + p0)
    follower.set_goal_pos(positions_final, servo_runtime=400, TOL=10)


def set_xyz_axis(viz, vr_stream):
    print('setting z')

    while vr_stream.button_lower_pressed() is False:
        pass

    x,y,z,_ = vr_stream.get_target(rotate=False)
    p_z = np.array([x,y,z])
    print(p_z)
    plot_point(viz=viz, x=x, y=y, z=z, color='blue')
    time.sleep(2)

    print('setting x')
    while vr_stream.button_lower_pressed() is False:
        pass
    x, y, z, _ = vr_stream.get_target(rotate=False)
    p_x = np.array([x, y, z])
    print(p_x)
    plot_point(viz=viz, x=x, y=y, z=z, color='red')

    time.sleep(2)
    print('setting y')
    while vr_stream.button_lower_pressed() is False:
        pass
    x, y, z, _ = vr_stream.get_target(rotate=False)
    p_y = np.array([x, y, z])
    print(p_y)
    plot_point(viz=viz, x=x, y=y, z=z, color='green')
    vr_stream.set_coordinate_system(p_x=p_x, p_y=p_y, p_z=p_z)
    time.sleep(2)

def set_rotation_axis(viz, vr_stream):
    print('setting rotation')
    print('get zero reference frame')
    while vr_stream.button_lower_pressed() is False:
        pass
    x0,y0,z0,_ = vr_stream.get_target(rotate=False)
    time.sleep(2)

    print('get x direction')
    while vr_stream.button_lower_pressed() is False:
        pass
    x1,y1,z1,_ = vr_stream.get_target(rotate=False)
    time.sleep(2)
    print('before rotation', x1,y1,z0)
    plot_point(viz=viz, x=x0, y=y0, z=z0, color='red')
    plot_point(viz=viz, x=x1, y=y1, z=z1, color='blue')

    vr_stream.set_rotation(x=x1-x0, y=y1-y0, z=z1-z0)

    x,y,z = vr_stream.R.T @ np.array([x1,y1,z0], dtype=np.float32)
    print('after rotation', x,y,z)
    plot_point(viz=viz, x=x, y=y, z=z, color='blue')



if __name__ == "__main__":
    # BEFORE STARTING NEED TO RUN
    # In xarm_ros2quest to get date from quest 2 with combination of quest2ros
    # docker run -it --network host --rm --name my_ros_container ros_noetic_with_quest2ros

    # Try controlling in simulation first
    SIM_MODE = False

    # Fixed arm with less degree of freedom
    urdf_path = str(Path(__file__).parent / 'xarm.urdf')


    contr = Controller(urdf_path, end_effector='link5', solver='osqp', )
    viz = setup_visualization(contr)
    viz.display(contr.configuration.q)

    # set_camera_perspective(viz.viewer)
    vr_stream = VrStream()
    # set_xyz_axis(viz=viz, vr_stream=vr_stream)

    # need to set rotation to be able
    set_rotation_axis(viz=viz, vr_stream=vr_stream)

    while vr_stream.button_lower_pressed() is False:
        x,y,z,r  = vr_stream.get_target(rotate=False)
        plot_point(viz=viz, x=x, y=y, z=z, color='yellow')
    delete_point('yellow')

    follower = BusServoRemoteTelopt('/dev/ttyUSB0')

    follower.enable_torque()

    default_pos = [0, 500, 300, 500, 500, 500]
    follower.set_goal_pos(default_pos, servo_runtime=300)

    _chain = Chain.from_urdf_file(urdf_file='xarm.urdf',
                                  active_links_mask=[False, True, True, True, True, True])
    while True:
        update_viewer(viz.viewer, contr)
        pos = contr.configuration.get_transform_frame_to_world(contr.end_effector_task.frame)

        x,y,z,r  = vr_stream.get_target_relativ(pos)
        rpy = pin.utils.matrixToRpy(r)
        r = pin.utils.rpyToMatrix(np.pi, 0, rpy[2])

        q1 = contr.ik(x,y,z,r)
        print(q1)
        frame_target = np.eye(4)
        frame_target[:3, 3] = np.array([x,y,z])
        if SIM_MODE is False:
            try:
                follower_update(q1, vr_stream)
            except Exception as e:
                print(f'got error {e}')

        viz.display(contr.configuration.q)

        time.sleep(.05)