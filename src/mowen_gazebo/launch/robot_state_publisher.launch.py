# =============================================================================
# Robot State Publisher 启动文件
# -----------------------------------------------------------------------------
# 作用: 读取 URDF 中的关节(joint)定义，订阅 /joint_states，
#       发布 TF 树中所有连杆(link)之间的动态变换。
#
# 发布的 TF（静态部分）:
#   base_footprint → base_link → [laser_link, camera_link, imu_link,
#                                  front_left_wheel, front_right_wheel,
#                                  back_left_wheel, back_right_wheel]
#
# 发布的 TF（动态部分）:
#   轮子关节根据 /joint_states 中的角度实时旋转
#
# 工作原理:
#   1. 解析 URDF 中的 <joint> 定义，找到需要发布的 TF
#   2. 对于 fixed 关节 → 发布静态 TF（一次发布，永久有效）
#   3. 对于非 fixed 关节 → 订阅 /joint_states，用其中 position 值计算 TF
#   4. Gazebo 通过 joint_state_publisher 插件发布 /joint_states（轮子角度）
# =============================================================================

import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # ---- URDF 文件路径 -------------------------------------------------
    # 注意: 项目同时有 model.sdf 和 mowen_with_sensors.urdf
    #   - SDF 用于 Gazebo（含插件定义: planar_move, laser, camera）
    #   - URDF 用于 robot_state_publisher（关节和连杆的静态 TF）
    #   两者定义相同的连杆和关节结构，必须保持一致
    urdf_path = os.path.join(
        get_package_share_directory('mowen_gazebo'),
        'urdf',
        'mowen_with_sensors.urdf'
    )

    # ---- 读取 URDF 为字符串 --------------------------------------------
    # robot_description 参数必须是完整的 URDF/XML 字符串，不能是文件路径
    with open(urdf_path, 'r') as f:
        robot_desc = f.read()

    # =========================================================================
    # robot_state_publisher —— 机器人 TF 发布者
    # -------------------------------------------------------------------------
    # 订阅: /joint_states (sensor_msgs/JointState) —— 来自 Gazebo
    # 发布: TF (tf2_msgs/TFMessage) —— 整个机器人 TF 树
    # =========================================================================
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_desc   # URDF 文件内容字符串
        }],
        output='screen'
    )

    return LaunchDescription([
        robot_state_publisher_node,
    ])
