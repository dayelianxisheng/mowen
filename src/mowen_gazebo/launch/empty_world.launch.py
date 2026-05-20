import os

# 确保 ROS 库路径对子进程（gzserver）可用
os.environ.setdefault('LD_LIBRARY_PATH', '')
if '/opt/ros/humble/lib' not in os.environ['LD_LIBRARY_PATH']:
    os.environ['LD_LIBRARY_PATH'] = '/opt/ros/humble/lib:' + os.environ['LD_LIBRARY_PATH']

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_mowen = get_package_share_directory('mowen_gazebo')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    x_pose = LaunchConfiguration('x_pose', default='0.0')
    y_pose = LaunchConfiguration('y_pose', default='0.0')

    world = os.path.join(pkg_mowen, 'worlds', 'empty_world.world')

    gzserver_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')),
        launch_arguments={'world': world}.items())

    gzclient_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py')))

    robot_state_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_mowen, 'launch', 'robot_state_publisher.launch.py')),
        launch_arguments={'use_sim_time': use_sim_time}.items())

    spawn_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_mowen, 'launch', 'spawn_mowen.launch.py')),
        launch_arguments={'x_pose': x_pose, 'y_pose': y_pose}.items())

    ld = LaunchDescription()
    ld.add_action(DeclareLaunchArgument('use_sim_time', default_value='true'))
    ld.add_action(gzserver_cmd)
    ld.add_action(gzclient_cmd)
    ld.add_action(robot_state_publisher_cmd)
    ld.add_action(spawn_cmd)
    return ld
