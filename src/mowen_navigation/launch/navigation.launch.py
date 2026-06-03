# =============================================================================
# Navigation2 (Nav2) 导航启动文件
# -----------------------------------------------------------------------------
# 作用: 启动完整的 Nav2 导航栈，包括:
#   - map_server:      加载预建地图
#   - AMCL:            蒙特卡洛定位（粒子滤波）
#   - planner_server:  全局路径规划（A* / Dijkstra）
#   - controller_server: 局部轨迹规划与控制（DWB）
#   - behavior_server: 行为树（spin/backup/wait 等恢复行为）
#   - velocity_smoother: 速度平滑（限制加速度/减速度）
#   - bt_navigator:    行为树导航器（编排以上所有模块）
#   - smoother_server: 路径平滑
#   - waypoint_follower: 多点导航
#
# 启动依赖: Gazebo 已运行、robot_state_publisher 已运行
# 启动命令: ros2 launch mowen_navigation navigation.launch.py
#           use_sim_time:=true map:=/path/to/map.yaml
#
# Nav2 官方文档: https://docs.nav2.org/
# =============================================================================

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    pkg_mowen_nav = get_package_share_directory('mowen_navigation')

    # ---- 启动参数 ----------------------------------------------------------
    # use_sim_time: 仿真时间。仿真=true(用Gazebo的/clock)，真机=false
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    # map: 预建地图文件路径(YAML)，map_server加载
    map_dir = LaunchConfiguration('map', default=os.path.join(pkg_mowen_nav, 'map', 'map.yaml'))
    # params_file: Nav2 全部参数配置文件（AMCL/DWB/costmap等都在这里）
    params_file = LaunchConfiguration('params_file', default=os.path.join(pkg_mowen_nav, 'config', 'nav2_params.yaml'))

    # ---- nav2_bringup 包路径（调用官方启动脚本）-------------------------------
    nav2_bringup_dir = get_package_share_directory('nav2_bringup')

    # ---- Rviz 配置（复用 Cartographer 的 Rviz 配置）-------------------------
    rviz_config = os.path.join(get_package_share_directory('mowen_cartographer'), 'rviz', 'mowen_cartographer.rviz')

    return LaunchDescription([
        DeclareLaunchArgument('map', default_value=map_dir),
        DeclareLaunchArgument('params_file', default_value=params_file),
        DeclareLaunchArgument('use_sim_time', default_value='true'),

        # =========================================================================
        # nav2_bringup 官方启动脚本
        # -------------------------------------------------------------------------
        # 这是一个"一站式"启动脚本，内部启动了 Nav2 所有核心节点：
        #   map_server, AMCL, planner, controller, behavior_server,
        #   bt_navigator, waypoint_follower, velocity_smoother, smoother_server
        #
        # RewrittenYaml 机制:
        #   nav2_bringup 会用 RewrittenYaml 处理 params_file，
        #   把其中叶子节点的 use_sim_time、yaml_filename、autostart
        #   替换为当前启动参数的值。这意味着 nav2_params.yaml 中的
        #   use_sim_time: False 会被自动覆盖为 true。
        #
        # 参数传递:
        #   'map': 地图 YAML 文件路径
        #   'use_sim_time': 覆盖所有子节点的 use_sim_time
        #   'params_file': 覆盖所有子节点的参数文件
        # =========================================================================
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(nav2_bringup_dir, 'launch', 'bringup_launch.py')),
            launch_arguments={
                'map': map_dir,
                'use_sim_time': use_sim_time,
                'params_file': params_file,
            }.items(),
        ),

        # ---- Rviz 可视化 ---------------------------------------------------
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen'),
    ])
