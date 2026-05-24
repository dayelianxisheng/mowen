import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_mowen_nav = get_package_share_directory('mowen_navigation')

    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    map_dir = LaunchConfiguration('map', default=os.path.join(pkg_mowen_nav, 'map', 'map.yaml'))
    params_file = LaunchConfiguration('params_file', default=os.path.join(pkg_mowen_nav, 'config', 'nav2_params.yaml'))

    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    rviz_config = os.path.join(get_package_share_directory('mowen_cartographer'), 'rviz', 'mowen_cartographer.rviz')

    return LaunchDescription([
        DeclareLaunchArgument('map', default_value=map_dir),
        DeclareLaunchArgument('params_file', default_value=params_file),
        DeclareLaunchArgument('use_sim_time', default_value='true'),

        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')),
            launch_arguments={
                'map': map_dir,
                'use_sim_time': use_sim_time,
                'params_file': params_file,
            }.items(),
        ),

        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'),
    ])
