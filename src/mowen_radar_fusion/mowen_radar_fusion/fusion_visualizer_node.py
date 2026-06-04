#!/usr/bin/env python3
"""
融合可视化节点: 在双窗口中展示雷达-相机融合效果

左侧: 原始相机画面
右侧: 叠加了雷达投影线的增强画面
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class FusionVisualizerNode(Node):
    def __init__(self):
        super().__init__('fusion_visualizer_node')
        self.bridge = CvBridge()

        # 订阅原始图像和增强图像
        self.create_subscription(Image, '/rgb_camera/image_raw', self.raw_callback, 10)
        self.create_subscription(Image, '/camera/image_radar', self.fused_callback, 10)

        self.latest_raw = None
        self.latest_fused = None
        self.combined_pub = self.create_publisher(Image, '/camera/fusion_display', 10)

        self.get_logger().info('FusionVisualizerNode started - publish to /camera/fusion_display')

    def raw_callback(self, msg: Image):
        self.latest_raw = msg
        self._display()

    def fused_callback(self, msg: Image):
        self.latest_fused = msg
        self._display()

    def _display(self):
        """并排显示原始图像和融合图像"""
        if self.latest_raw is None or self.latest_fused is None:
            return

        import cv2
        import numpy as np

        raw = self.bridge.imgmsg_to_cv2(self.latest_raw, desired_encoding='bgr8')
        fused = self.bridge.imgmsg_to_cv2(self.latest_fused, desired_encoding='bgr8')

        # 确保尺寸一致
        h = max(raw.shape[0], fused.shape[0])
        if raw.shape[0] != h:
            raw = cv2.resize(raw, (int(raw.shape[1] * h / raw.shape[0]), h))
        if fused.shape[0] != h:
            fused = cv2.resize(fused, (int(fused.shape[1] * h / fused.shape[0]), h))

        # 并排
        combined = np.hstack([raw, fused])

        # 标题
        cv2.putText(combined, 'Camera', (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(combined, 'Camera + Radar', (raw.shape[1] + 10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

        # 发布合并图像为 ROS2 topic，用 rqt_image_view /detection_image 看
        img_msg = self.bridge.cv2_to_imgmsg(combined, encoding='bgr8')
        self.combined_pub.publish(img_msg)


def test():
    """测试: 展示原始图 + 雷达投影图的并排对比效果"""
    import numpy as np
    import cv2

    print("=" * 60)
    print("融合可视化 测试 — 并排对比:")
    print("=" * 60)

    w, h = 320, 240

    # 左: 模拟原始相机图
    raw = np.ones((h, w, 3), dtype=np.uint8) * 80
    cv2.rectangle(raw, (0, 160), (w, h), (60, 60, 60), -1)  # 地面
    cv2.rectangle(raw, (100, 80), (160, 180), (50, 50, 200), -1)  # 障碍物
    cv2.putText(raw, "RAW Camera", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # 右: 模拟雷达投影图 (加上投影线)
    fused = np.ones((h, w, 3), dtype=np.uint8) * 80
    cv2.rectangle(fused, (0, 160), (w, h), (60, 60, 60), -1)
    cv2.rectangle(fused, (100, 80), (160, 180), (50, 50, 200), -1)
    # 添加模拟雷达投影线
    for px, dist in [(130, 2), (150, 5), (80, 8), (200, 3)]:
        ratio = min(1.0, dist / 10.0)
        color = (int(255 * ratio), 0, int(255 * (1 - ratio)))
        cv2.line(fused, (px, 200), (px, 40), color, 2)
        cv2.putText(fused, f"{dist}m", (px + 4, 35),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)
    cv2.putText(fused, "Camera + Radar", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # 并排
    combined = np.hstack([raw, fused])
    cv2.imshow("Fusion Visualizer Test - Press any key", combined)

    print(f"\n  左侧: 原始相机画面 ({w}x{h})")
    print(f"  右侧: 雷达投影增强 ({w}x{h})")
    print(f"  红色线 = 近距离物质, 蓝色线 = 远距离物质")
    print(f"  对比: 雷达线标注了障碍物位置和距离")

    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("=" * 60)


def main():
    import sys
    if '--test' in sys.argv:
        test()
        return

    rclpy.init()
    node = FusionVisualizerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
