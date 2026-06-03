# =============================================================================
# occupancy_grid_node 启动文件
# -----------------------------------------------------------------------------
# 作用: 将 Cartographer 内部 submap 转为标准 ROS2 OccupancyGrid 消息，
#       发布到 /map 话题，供 AMCL 导航使用。
#
# cartographer_node 内部维护的是 submap（子图），不是标准的 OccupancyGrid，
# 这个节点负责"翻译"工作。
# =============================================================================

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():
    use_sim_time = LaunchConfiguration('use_sim_time',default='flase')
    # resolution: 输出栅格分辨率(米/像素)，0.05 = 每格5厘米
    resolution = LaunchConfiguration('resolution',default='0.05')
    # publish_period_sec: 地图发布频率，1.0 = 每秒发布一次
    publish_period_sec = LaunchConfiguration('publish_period_sec',default='1.0')

    return LaunchDescription([
        DeclareLaunchArgument(
            'resolution',
            default_value=resolution,
            description='Resolution of a grid cell in the published occupancy grid'),

        DeclareLaunchArgument(
            'publish_period_sec',
            default_value=publish_period_sec,
            description='OccupancyGrid publishing period'),

        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),

        # =========================================================================
        # cartographer_occupancy_grid_node
        # - 从 cartographer_node 获取 submap 数据
        # - 转换成 nav_msgs/OccupancyGrid 发布到 /map
        # - AMCL 和 costmap 都订阅 /map 来做定位和规划
        # =========================================================================
        Node(
            package='cartographer_ros',
            executable='cartographer_occupancy_grid_node',
            name='cartographer_occupancy_grid_node',
            output='screen',
            parameters=[{'use_sim_time': use_sim_time}],
            arguments=['-resolution', resolution,
                       '-publish_period_sec', publish_period_sec]),
    ])
