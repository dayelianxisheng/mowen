#!/usr/bin/env python3
"""
雷达仿真节点: 将 Gazebo RaySensor 的 LaserScan 转换为 RadarTargetArray

Gazebo 中的雷达用一个低分辨率 RaySensor 模拟。
本节点订阅 /radar/scan (LaserScan)，将其转换为自定义的 RadarTargetArray 消息。

毫米波雷达的特点（对比 LiDAR）:
  - 扫描线少 (10 束 vs LiDAR 360+)
  - 角度范围宽 (±40°)
  - 测距远 (最大 35m)
  - 可以测速度 (从多普勒效应推导)
  - SNR 用激光反射强度模拟
"""

import math
import sys
import numpy as np

# --test 模式: 独立运行, 不需要 ROS2
if '--test' in sys.argv:
    print("=" * 60)
    print("雷达仿真节点 测试 - 数据特征:")
    print("=" * 60)
    n_beams = 10
    angles = np.linspace(-0.7, 0.7, n_beams)
    ranges = np.array([1.5, 3.2, 5.8, 35.0, 35.0, 35.0, 4.1, 2.3, 12.0, 8.5])
    print(f"LaserScan: {n_beams}束, ±{np.rad2deg(0.7):.0f}°, 0.5-35m")
    valid = ranges < 35.0
    for i in range(n_beams):
        status = f"{ranges[i]:.1f}m" if valid[i] else "无回波"
        print(f"  束{i:2d} | {np.rad2deg(angles[i]):+6.1f}deg | {status}")
    print(f"有效目标: {valid.sum()}/{n_beams}, 最近{np.min(ranges[valid]):.1f}m, 最远{np.max(ranges[valid]):.1f}m")
    print("=" * 60)
    sys.exit(0)

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from mowen_radar_fusion.msg import RadarTarget, RadarTargetArray


class RadarSimNode(Node):
    def __init__(self):
        super().__init__('radar_sim_node')

        # 订阅 Gazebo 雷达 RaySensor 输出的 LaserScan
        self.sub = self.create_subscription(
            LaserScan, '/radar/scan', self.scan_callback, 10)

        # 发布 RadarTargetArray
        self.pub = self.create_publisher(
            RadarTargetArray, '/radar/targets', 10)

        self.get_logger().info('RadarSimNode started - converting /radar/scan to /radar/targets')

    def scan_callback(self, msg: LaserScan):
        targets = RadarTargetArray()
        targets.header = msg.header
        targets.header.frame_id = 'radar_link'

        target_id = 0
        for i, r in enumerate(msg.ranges):
            # 跳过无效测量 (0.0 表示超出范围或无回波)
            if r <= msg.range_min or r >= msg.range_max:
                continue

            angle = msg.angle_min + i * msg.angle_increment
            intensity = msg.intensities[i] if i < len(msg.intensities) else 0.0

            # 构建雷达目标
            t = RadarTarget()
            t.target_id = target_id
            t.range = r
            t.azimuth = angle
            t.elevation = 0.0  # 2D 雷达
            t.snr = intensity * 100.0  # 强度换算为 SNR
            t.speed = 0.0  # Gazebo 无法直接获取多普勒速度

            targets.targets.append(t)
            target_id += 1

        self.pub.publish(targets)
        self.get_logger().debug(f'Published {len(targets.targets)} radar targets')


def main():
    rclpy.init()
    node = RadarSimNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
