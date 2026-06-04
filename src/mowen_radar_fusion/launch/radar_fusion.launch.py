#!/usr/bin/env python3
"""
mowen 雷达-相机融合完整启动文件

启动内容:
  1. gzserver + gzclient (Gazebo 仿真环境)
  2. robot_state_publisher (TF 树)
  3. spawn mowen 机器人 (使用 mowen_radar_fusion 自己的模型)
  4. radar_sim_node (LaserScan → RadarTargetArray)
  5. radar_camera_projector (雷达→相机投影)
  6. fusion_visualizer_node (可视化)
  7. rviz2 (RViz 显示)

用法:
  ros2 launch mowen_radar_fusion radar_fusion.launch.py
  ros2 launch mowen_radar_fusion radar_fusion.launch.py x_pose:=1.0 y_pose:=0.5
"""

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_mowen_radar = get_package_share_directory('mowen_radar_fusion')
    pkg_mowen_gazebo = get_package_share_directory('mowen_gazebo')

    # ---- 启动参数 ----
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    x_pose = LaunchConfiguration('x_pose', default='0.0')
    y_pose = LaunchConfiguration('y_pose', default='0.0')
    yaw = LaunchConfiguration('yaw', default='1.57')
    # 世界选择: warehouse (默认) / mowen / empty
    world_choice = LaunchConfiguration('world', default='warehouse')

    # ---- 模型文件路径 (使用自己的 SDF，含雷达+相机) ----
    sdf_path = os.path.join(pkg_mowen_radar, 'models', 'mowen_with_sensors', 'model.sdf')

    # ---- URDF 文件路径 (含雷达+相机连杆，用于 robot_state_publisher) ----
    urdf_path = os.path.join(pkg_mowen_radar, 'urdf', 'mowen_with_sensors.urdf')
    with open(urdf_path, 'r') as f:
        robot_desc = f.read()

    # ---- 世界文件 ----
    warehouse_world = os.path.join(pkg_mowen_radar, 'models', 'race_scene.world')

    # ---- Gazebo 路径配置 ----
    gazebo_model_path = os.pathsep.join([
        os.path.join(pkg_mowen_radar, 'models'),
        os.path.join(pkg_mowen_radar, 'models', 'race_models'),
        os.path.join(pkg_mowen_gazebo, 'models'),
        '/opt/ros/humble/share/gazebo_ros/models',
        '/usr/share/gazebo-11/models',
    ])
    gazebo_plugin_path = os.pathsep.join([
        '/opt/ros/humble/lib',
        '/usr/lib/x86_64-linux-gnu/gazebo-11/plugins',
    ])
    gazebo_env = {
        'GAZEBO_MODEL_PATH': gazebo_model_path,
        'GAZEBO_PLUGIN_PATH': gazebo_plugin_path,
        'GAZEBO_RESOURCE_PATH': os.pathsep.join([
            '/opt/ros/humble/share/gazebo_ros',
            '/usr/share/gazebo-11',
        ]),
        'GAZEBO_MODEL_DATABASE_URI': '',  # 禁用在线模型数据库下载
    }

    # ---- 1. gzserver ----
    gzserver_cmd = ExecuteProcess(
        cmd=['gzserver', '--verbose', warehouse_world,
             '-s', 'libgazebo_ros_init.so',
             '-s', 'libgazebo_ros_factory.so',
             '-s', 'libgazebo_ros_force_system.so'],
        output='screen',
        additional_env=gazebo_env,
    )

    # ---- 2. gzclient ----
    gzclient_cmd = ExecuteProcess(
        cmd=['gzclient'],
        output='screen',
        additional_env=gazebo_env,
    )

    # ---- 3. robot_state_publisher (使用含雷达+相机的完整 URDF) ----
    robot_state_publisher_cmd = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_desc,
        }],
        output='screen',
    )

    # ---- 4. spawn mowen 模型 ----
    spawn_cmd = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=[
            '-entity', 'mowen',
            '-file', sdf_path,
            '-x', x_pose,
            '-y', y_pose,
            '-z', '0.2'
        ],
        output='screen',
    )

    # ---- 5. 雷达仿真节点 ----
    radar_sim = Node(
        package='mowen_radar_fusion',
        executable='radar_sim_node.py',
        name='radar_sim_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    # ---- 6. 雷达→相机投影节点 ----
    projector = Node(
        package='mowen_radar_fusion',
        executable='radar_camera_projector.py',
        name='radar_camera_projector',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    # ---- 7. 可视化节点 ----
    visualizer = Node(
        package='mowen_radar_fusion',
        executable='fusion_visualizer_node.py',
        name='fusion_visualizer_node',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    # ---- 8. CNN 检测节点 ----
    detector = Node(
        package='mowen_radar_fusion',
        executable='radar_detector.py',
        name='radar_detector',
        output='screen',
        parameters=[{'use_sim_time': use_sim_time}],
    )

    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('x_pose', default_value='0.0'),
        DeclareLaunchArgument('y_pose', default_value='0.0'),
        DeclareLaunchArgument('yaw', default_value='0.0'),
        gzserver_cmd,
        gzclient_cmd,
        robot_state_publisher_cmd,
        spawn_cmd,
        radar_sim,
        projector,
        visualizer,
        detector,
    ])
