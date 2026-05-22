import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    sdf_path = os.path.join(
        get_package_share_directory('mowen_gazebo'),
        'models',
        'mowen',
        'model.sdf')

    x_pose = LaunchConfiguration('x_pose', default='0.0')
    y_pose = LaunchConfiguration('y_pose', default='0.0')

    declare_x_cmd = DeclareLaunchArgument('x_pose', default_value='0.0')
    declare_y_cmd = DeclareLaunchArgument('y_pose', default_value='0.0')

    spawn_cmd = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'mowen',
            '-file', sdf_path,
            '-x', x_pose,
            '-y', y_pose,
            '-z', '0.01'
        ],
        output='screen',
    )

    return LaunchDescription([
        declare_x_cmd,
        declare_y_cmd,
        spawn_cmd,
    ])
