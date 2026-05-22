import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_mowen = get_package_share_directory('mowen_gazebo')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    x_pose = LaunchConfiguration('x_pose', default='0.0')
    y_pose = LaunchConfiguration('y_pose', default='0.0')

    world = os.path.join(pkg_mowen, 'worlds', 'empty_world.world')

    # GazeboRosPaths.get_paths() is unreliable (returns empty in some envs).
    # Set paths directly to ensure libgazebo_ros_factory.so is found.
    gazebo_plugin_path = os.pathsep.join([
        '/opt/ros/humble/lib',
        '/usr/lib/x86_64-linux-gnu/gazebo-11/plugins',
    ])
    gazebo_resource_path = os.pathsep.join([
        '/opt/ros/humble/share/gazebo_ros',
        '/usr/share/gazebo-11',
    ])
    gazebo_model_path = os.pathsep.join([
        os.path.join(pkg_mowen, 'models'),
        '/opt/ros/humble/share/gazebo_ros/models',
        '/usr/share/gazebo-11/models',
    ])

    gazebo_env = {
        'GAZEBO_MODEL_PATH': gazebo_model_path,
        'GAZEBO_PLUGIN_PATH': gazebo_plugin_path,
        'GAZEBO_RESOURCE_PATH': gazebo_resource_path,
    }

    gzserver_cmd = ExecuteProcess(
        cmd=['gzserver', '--verbose', world,
             '-s', 'libgazebo_ros_init.so',
             '-s', 'libgazebo_ros_factory.so',
             '-s', 'libgazebo_ros_force_system.so'],
        output='screen',
        additional_env=gazebo_env,
    )

    gzclient_cmd = ExecuteProcess(
        cmd=['gzclient'],
        output='screen',
        additional_env=gazebo_env,
    )

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
