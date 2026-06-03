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


def main():
    rclpy.init()
    node = FusionVisualizerNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
