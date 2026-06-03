# =============================================================================
# cartographer_node 启动文件
# -----------------------------------------------------------------------------
# 作用: 启动 Google Cartographer 2D SLAM 节点，接收 /scan 和 /odom，
#       发布 submap 和 TF(map→odom)，由 occupancy_grid_node 生成栅格地图。
#
# 订阅: /scan (sensor_msgs/LaserScan), /odom (nav_msgs/Odometry)
# 发布: /submap_list (cartographer_ros_msgs/SubmapList)
#       TF: map → odom → base_link
#
# 配置文件: config/mowen_lds_2d.lua
# =============================================================================

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration, ThisLaunchFileDir
from launch_ros.actions import Node


def generate_launch_description():
    # ---- 基础参数 ----------------------------------------------------------
    # use_sim_time: 仿真时间开关。仿真=true(用Gazebo时钟)，真机=false(用系统时钟)
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    # use_rviz: 是否同时启动Rviz可视化
    use_rviz = LaunchConfiguration('use_rviz', default='true')

    # ---- Cartographer 配置路径 --------------------------------------------
    pkg_prefix = get_package_share_directory('mowen_cartographer')
    # config_dir: lua配置文件的目录
    config_dir = LaunchConfiguration('config_dir', default=os.path.join(pkg_prefix, 'config'))
    # config_basename: lua配置文件名（相对于config_dir）
    config_basename = LaunchConfiguration('config_basename', default='mowen_lds_2d.lua')

    # ---- 栅格地图参数 ------------------------------------------------------
    # resolution: 输出栅格地图的分辨率(米/像素)，0.05=5cm
    resolution = LaunchConfiguration('resolution', default='0.05')
    # publish_period_sec: 栅格地图发布周期(秒)
    publish_period_sec = LaunchConfiguration('publish_period_sec', default='1.0')

    rviz_config = os.path.join(pkg_prefix, 'rviz', 'mowen_cartographer.rviz')

    return LaunchDescription([
        DeclareLaunchArgument('config_dir', default_value=config_dir),
        DeclareLaunchArgument('config_basename', default_value=config_basename),
        DeclareLaunchArgument('use_sim_time', default_value='false'),
        DeclareLaunchArgument('use_rviz', default_value='true'),

        # =========================================================================
        # cartographer_node —— SLAM 核心节点
        # - 订阅激光扫描和里程计，构建子图(submap)
        # - 通过闭环检测(loop closure)优化全局位姿图(pose graph)
        # - 发布 map→odom 坐标变换
        # =========================================================================
        Node(
            package='cartographer_ros',           # Cartographer ROS2 包
            executable='cartographer_node',        # 可执行文件名
            name='cartographer_node',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
            arguments=['-configuration_directory', config_dir,   # lua配置目录
                       '-configuration_basename', config_basename]),  # lua配置文件

        DeclareLaunchArgument('resolution', default_value=resolution),
        DeclareLaunchArgument('publish_period_sec', default_value=publish_period_sec),

        # =========================================================================
        # cartographer_occupancy_grid_node —— 栅格地图转换节点
        # - 将 Cartographer 的 submap 转换为标准的 OccupancyGrid
        # - 这是 AMCL 导航所需的 /map 话题来源
        # =========================================================================
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource([ThisLaunchFileDir(), '/occupancy_grid.launch.py']),
            launch_arguments={
                'use_sim_time': use_sim_time,
                'resolution': resolution,
                'publish_period_sec': publish_period_sec,
            }.items()),

        # ---- Rviz 可视化 ---------------------------------------------------
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': use_sim_time}],
            condition=IfCondition(use_rviz)),
    ])
