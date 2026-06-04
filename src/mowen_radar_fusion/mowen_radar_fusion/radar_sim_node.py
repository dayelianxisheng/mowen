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

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import LaserScan
from mowen_radar_fusion.msg import RadarTarget, RadarTargetArray
import math


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


def test():
    """测试: 生成模拟雷达数据并打印特征"""
    import numpy as np
    print("=" * 60)
    print("雷达仿真节点 测试 — 数据特征:")
    print("=" * 60)

    # 模拟 10 束雷达, ±40° (±0.7rad), 距离 0.5-35m
    n_beams = 10
    angles = np.linspace(-0.7, 0.7, n_beams)
    # 模拟场景: 有近有远的目标
    ranges = np.array([1.5, 3.2, 5.8, 35.0, 35.0, 35.0, 4.1, 2.3, 12.0, 8.5])

    print(f"\n输入 (LaserScan):")
    print(f"  {n_beams} 束, 角度范围 ±{np.rad2deg(0.7):.0f}°")
    print(f"  angle_min={angles[0]:.2f}, angle_max={angles[-1]:.2f}")
    print(f"  range_min=0.5m, range_max=35.0m")

    print(f"\n有效检测 (Range < 35m = 有物体):")
    valid = ranges < 35.0
    for i in range(n_beams):
        status = f"✓ {ranges[i]:.1f}m" if valid[i] else "✗ 无回波"
        print(f"  束{i:2d} | 角度 {np.rad2deg(angles[i]):+6.1f}° | {status}")

    print(f"\n输出 (RadarTargetArray):")
    print(f"  有效目标数: {valid.sum()}/{n_beams}")
    print(f"  最近: {ranges[valid].min():.1f}m (束{np.argmin(ranges)})")
    print(f"  最远: {ranges[valid].max():.1f}m")
    print(f"  平均: {ranges[valid].mean():.1f}m")
    print(f"  检测率: {valid.sum()/n_beams*100:.0f}%")
    print("=" * 60)


def main():
    import sys
    if '--test' in sys.argv:
        test()
        return

    rclpy.init()
    node = RadarSimNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
