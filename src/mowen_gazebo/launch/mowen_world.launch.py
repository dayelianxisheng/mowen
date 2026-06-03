# =============================================================================
# Gazebo 仿真环境启动文件（mowen 完整场景）
# -----------------------------------------------------------------------------
# 作用: 启动 Gazebo 仿真 + 机器人模型 + robot_state_publisher
#
# 启动的 4 个进程:
#   1. gzserver  —— Gazebo 物理引擎服务器（加载世界 + 机器人模型）
#   2. gzclient  —— Gazebo 图形界面客户端
#   3. robot_state_publisher —— 发布机器人 TF 树（从 URDF 读取关节/连杆定义）
#   4. spawn_entity.py —— 在 Gazebo 中生成 mowen 机器人
#
# 环境变量:
#   GAZEBO_MODEL_PATH  —— Gazebo 搜索模型的路径
#   GAZEBO_PLUGIN_PATH  —— Gazebo 搜索插件的路径（含 ros 插件）
#   GAZEBO_RESOURCE_PATH —— Gazebo 资源路径
#
# 启动命令:
#   ros2 launch mowen_gazebo mowen_world.launch.py x_pose:=0 y_pose:=0
#
# 启动顺序:
#   gzserver (必须先起来) → robot_state_publisher → spawn_entity → gzclient
# =============================================================================

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, ExecuteProcess, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    pkg_mowen = get_package_share_directory('mowen_gazebo')

    # ---- 启动参数 ----------------------------------------------------------
    # use_sim_time: Gazebo 发布 /clock 话题，所有节点统一使用仿真时钟
    use_sim_time = LaunchConfiguration('use_sim_time', default='true')
    # x_pose, y_pose: 机器人初始位置
    x_pose = LaunchConfiguration('x_pose', default='0.0')
    y_pose = LaunchConfiguration('y_pose', default='0.0')

    # ---- 世界文件路径 -------------------------------------------------------
    # mowen_world.world: 包含地面、光照和一个空旷环境
    world = os.path.join(pkg_mowen, 'worlds', 'mowen_world.world')

    # ---- Gazebo 路径配置 ----------------------------------------------------
    # Docker 容器中 GazeboRosPaths.get_paths() 可能返回空，
    # 这里直接硬编码标准路径，确保插件和模型能被找到。
    gazebo_plugin_path = os.pathsep.join([
        '/opt/ros/humble/lib',                           # ROS Gazebo 插件
        '/usr/lib/x86_64-linux-gnu/gazebo-11/plugins',   # Gazebo 自带插件
    ])
    gazebo_resource_path = os.pathsep.join([
        '/opt/ros/humble/share/gazebo_ros',              # ROS Gazebo 共享资源
        '/usr/share/gazebo-11',                          # Gazebo 自带资源
    ])
    gazebo_model_path = os.pathsep.join([
        os.path.join(pkg_mowen, 'models'),               # 本项目的模型目录 ← mowen 模型
        '/opt/ros/humble/share/gazebo_ros/models',       # ROS Gazebo 默认模型
        '/usr/share/gazebo-11/models',                   # Gazebo 默认模型
    ])

    gazebo_env = {
        'GAZEBO_MODEL_PATH': gazebo_model_path,
        'GAZEBO_PLUGIN_PATH': gazebo_plugin_path,
        'GAZEBO_RESOURCE_PATH': gazebo_resource_path,
    }

    # =========================================================================
    # 1. gzserver —— Gazebo 物理引擎（无头模式）
    # -------------------------------------------------------------------------
    # -s libgazebo_ros_init.so:     初始化 ROS 通信（/clock 话题发布者）
    # -s libgazebo_ros_factory.so:  支持 spawn_entity 动态生成模型
    # -s libgazebo_ros_force_system.so: 支持 ROS 力/扭矩控制
    # --verbose: 打印详细日志
    # =========================================================================
    gzserver_cmd = ExecuteProcess(
        cmd=['gzserver', '--verbose', world,
             '-s', 'libgazebo_ros_init.so',
             '-s', 'libgazebo_ros_factory.so',
             '-s', 'libgazebo_ros_force_system.so'],
        output='screen',
        additional_env=gazebo_env,
    )

    # =========================================================================
    # 2. gzclient —— Gazebo 图形界面
    # =========================================================================
    gzclient_cmd = ExecuteProcess(
        cmd=['gzclient'],
        output='screen',
        additional_env=gazebo_env,
    )

    # =========================================================================
    # 3. robot_state_publisher —— TF 发布者
    # -------------------------------------------------------------------------
    # 读取 URDF 中定义的关节(joint)和连杆(link)，发布静态 TF 变换。
    # 例如: base_footprint → base_link → laser_link / wheel_links
    # 注意: 关节的动态值（如轮子角度）来自 Gazebo 发布的 /joint_states
    # =========================================================================
    robot_state_publisher_cmd = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_mowen, 'launch', 'robot_state_publisher.launch.py')),
        launch_arguments={'use_sim_time': use_sim_time}.items())

    # =========================================================================
    # 4. spawn_entity —— 在 Gazebo 中生成机器人
    # -------------------------------------------------------------------------
    # 向 gzserver 请求生成 mowen 模型，位置由 x_pose/y_pose 指定
    # =========================================================================
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
