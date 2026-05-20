import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')

    # 获取 URDF 文件路径
    urdf_path = os.path.join(
        get_package_share_directory('mowen_gazebo'),
        'urdf',
        'mowen.urdf'
    )

    # 读取 URDF 内容
    with open(urdf_path, 'r') as f:
        robot_desc = f.read()

    # 启动 robot_state_publisher 节点
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{
            'use_sim_time': use_sim_time,
            'robot_description': robot_desc
        }],
        output='screen'
    )

    return LaunchDescription([
        robot_state_publisher_node,
    ])