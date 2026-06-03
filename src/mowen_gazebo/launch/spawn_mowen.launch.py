# =============================================================================
# 机器人生成启动文件
# -----------------------------------------------------------------------------
# 作用: 调用 gazebo_ros 的 spawn_entity.py 在 Gazebo 世界中生成 mowen 模型
#
# 关键点:
#   - 模型文件为 model.sdf（不是 URDF），因为需要 plugin 定义
#     (planar_move, ray_sensor 等 Gazebo 插件只能在 SDF 中定义)
#   - z 坐标固定为 0.01（略高于地面，防止与地面碰撞穿透）
# =============================================================================

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    # ---- 模型文件路径 (SDF 格式) ----------------------------------------
    sdf_path = os.path.join(
        get_package_share_directory('mowen_gazebo'),
        'models',
        'mowen',
        'model.sdf')

    # ---- 初始位姿参数 ---------------------------------------------------
    x_pose = LaunchConfiguration('x_pose', default='0.0')
    y_pose = LaunchConfiguration('y_pose', default='0.0')

    declare_x_cmd = DeclareLaunchArgument('x_pose', default_value='0.0')
    declare_y_cmd = DeclareLaunchArgument('y_pose', default_value='0.0')

    # =========================================================================
    # spawn_entity.py —— Gazebo 工厂节点
    # -entity:  模型在 Gazebo 中的名字
    # -file:    SDF 模型文件路径
    # -x/-y/-z: 初始坐标（z=0.01 略高于地面，防止与地面平面碰撞）
    # =========================================================================
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
