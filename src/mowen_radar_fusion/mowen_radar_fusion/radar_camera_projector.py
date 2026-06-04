#!/usr/bin/env python3
"""
雷达→相机投影: 将雷达目标点投影到相机图像平面

CRF-Net 风格的数据级融合核心逻辑:
  1. 从 TF 树获取雷达→相机的空间变换
  2. 读取相机内参
  3. 雷达球坐标 → 笛卡尔坐标 → 相机坐标 → 像素坐标
  4. 在图像上画投影线（底部 z=0 到顶部 z=h）

输出:
  /camera/image_radar: 叠加了雷达投影线的 RGB 图像
  /camera/radar_overlay: 纯雷达投影图（用于调试）
"""

import sys
if '--test' in sys.argv:
    import numpy as np
    import cv2
    print("=" * 60)
    print("雷达→相机投影 测试 - 数据变换链:")
    print("=" * 60)

    IMG_W, IMG_H = 640, 480
    fx = IMG_W / (2 * np.tan(np.deg2rad(60) / 2))
    K = np.array([[fx, 0, IMG_W/2], [0, fx, IMG_H/2], [0, 0, 1]])
    t = np.array([0.001, 0, -0.02])
    R = np.eye(3)
    targets = [(2.0, 0.0), (4.0, 0.3), (8.0, -0.2), (1.5, 0.1), (15.0, 0.0)]
    img = np.ones((IMG_H, IMG_W, 3), dtype=np.uint8) * 50

    for dist, az in targets:
        x_r, y_r = dist * np.cos(az), dist * np.sin(az)
        pt_cam = R @ np.array([x_r, y_r, 0.0]) + t
        if pt_cam[0] <= 0: continue
        px = K @ pt_cam
        u, v = int(px[0]/px[2]), int(px[1]/px[2])
        ratio = min(1.0, dist / 10.0)
        color = (int(255*ratio), 0, int(255*(1-ratio)))
        cv2.line(img, (u, v-30), (u, v+30), color, 2)
        cv2.putText(img, f"{dist:.1f}m", (u+5, v-5), cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        print(f"  {dist:.1f}m, {np.rad2deg(az):+.0f}deg → ({x_r:.1f},{y_r:.1f})m → 相机({pt_cam[0]:.1f},{pt_cam[1]:.1f})m → 像素({u},{v}) | B={color[0]},R={color[2]}")

    cv2.imshow("Projector Test - Press any key", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    print("=" * 60)
    sys.exit(0)

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image, CameraInfo
from mowen_radar_fusion.msg import RadarTargetArray
from cv_bridge import CvBridge
import cv2
import numpy as np
import tf2_ros
import tf2_geometry_msgs
from geometry_msgs.msg import TransformStamped


class RadarCameraProjector(Node):
    def __init__(self):
        super().__init__('radar_camera_projector')

        # 订阅话题
        self.create_subscription(Image, '/rgb_camera/image_raw', self.image_callback, 10)
        self.create_subscription(CameraInfo, '/rgb_camera/camera_info', self.camera_info_callback, 10)
        self.create_subscription(RadarTargetArray, '/radar/targets', self.radar_callback, 10)

        # 发布增强图像
        self.pub_radar_img = self.create_publisher(Image, '/camera/image_radar', 10)
        self.pub_overlay = self.create_publisher(Image, '/camera/radar_overlay', 10)

        # TF 缓冲
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)

        # 状态
        self.bridge = CvBridge()
        self.latest_img = None
        self.K = None  # 相机内参 (3x3)
        self.width = 0
        self.height = 0
        self.latest_radar = None

        # 雷达投影参数
        self.radar_height_min = -0.3   # 投影线底部 (雷达安装高度 - 目标最低高度)
        self.radar_height_max = 1.5    # 投影线顶部 (障碍物最高高度)
        self.max_distance = 10.0       # 颜色映射最大距离(m), 匹配实际场景大小

        self.get_logger().info('RadarCameraProjector started')

    def camera_info_callback(self, msg: CameraInfo):
        """保存相机内参"""
        self.K = np.array(msg.k).reshape(3, 3)
        self.width = msg.width
        self.height = msg.height

    def image_callback(self, msg: Image):
        """保存最新图像"""
        self.latest_img = msg
        # 如果有待处理的雷达数据，立即处理
        if self.latest_radar is not None:
            self.process_frame()

    def radar_callback(self, msg: RadarTargetArray):
        """保存最新雷达数据并尝试处理"""
        self.latest_radar = msg
        if self.latest_img is not None and self.K is not None:
            self.process_frame()

    def process_frame(self):
        """执行雷达→相机投影和图像融合"""
        if self.latest_img is None or self.latest_radar is None or self.K is None:
            return

        # 转换图像
        img = self.bridge.imgmsg_to_cv2(self.latest_img, desired_encoding='bgr8')
        overlay = np.zeros_like(img)

        # 获取雷达→相机变换
        try:
            R, t = self._get_transform('camera_optical', 'radar_link')
        except Exception as e:
            self.get_logger().warn(f'TF lookup failed: {e}')
            return

        for target in self.latest_radar.targets:
            # 球坐标 → 笛卡尔坐标
            x_r = target.range * math.cos(target.azimuth) * math.cos(target.elevation)
            y_r = target.range * math.sin(target.azimuth) * math.cos(target.elevation)
            z_r = target.range * math.sin(target.elevation)
            pt_radar = np.array([x_r, y_r, z_r])

            # 投影线底部点和顶部点
            pt_radar_bottom = np.array([x_r, y_r, self.radar_height_min])
            pt_radar_top = np.array([x_r, y_r, self.radar_height_max])

            # 投影到像素
            px_bottom = self._project(pt_radar_bottom, self.K, R, t)
            px_top = self._project(pt_radar_top, self.K, R, t)

            if px_bottom is None or px_top is None:
                continue

            bx, by = px_bottom
            tx, ty = px_top

            # 根据距离确定颜色（近=红，远=蓝）
            ratio = min(1.0, target.range / self.max_distance)
            color = (
                int(255 * ratio),          # 蓝
                0,
                int(255 * (1.0 - ratio))   # 红
            )

            # 在图像上画垂直线
            cv2.line(img, (bx, by), (tx, ty), color, 2)
            cv2.circle(img, (bx, by), 4, color, -1)

            # 在覆盖图上画
            cv2.line(overlay, (bx, by), (tx, ty), color, 2)
            cv2.circle(overlay, (bx, by), 4, color, -1)

            # 标注距离文字
            cv2.putText(img, f'{target.range:.1f}m', (bx + 5, by - 5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 1)

        # 发布增强图像
        self.pub_radar_img.publish(self.bridge.cv2_to_imgmsg(img, encoding='bgr8'))
        self.pub_overlay.publish(self.bridge.cv2_to_imgmsg(overlay, encoding='bgr8'))

        # 重置雷达数据
        self.latest_radar = None

    def _get_transform(self, target_frame: str, source_frame: str):
        """从 TF 树获取变换矩阵"""
        transform: TransformStamped = self.tf_buffer.lookup_transform(
            target_frame, source_frame, rclpy.time.Time())

        # 平移
        t = np.array([
            transform.transform.translation.x,
            transform.transform.translation.y,
            transform.transform.translation.z
        ])

        # 四元数 → 旋转矩阵
        q = transform.transform.rotation
        R = self._quaternion_to_matrix(q.x, q.y, q.z, q.w)

        return R, t

    def _quaternion_to_matrix(self, x, y, z, w):
        """四元数 → 3x3 旋转矩阵"""
        xx, yy, zz = x * x, y * y, z * z
        xy, xz, yz = x * y, x * z, y * z
        wx, wy, wz = w * x, w * y, w * z

        return np.array([
            [1 - 2*(yy + zz), 2*(xy - wz),     2*(xz + wy)],
            [2*(xy + wz),     1 - 2*(xx + zz), 2*(yz - wx)],
            [2*(xz - wy),     2*(yz + wx),     1 - 2*(xx + yy)]
        ])

    def _project(self, pt_3d, K, R, t):
        """3D 点投影到 2D 像素"""
        cam_pt = R @ pt_3d + t
        if cam_pt[2] <= 0:  # 相机后方
            return None

        px = K @ cam_pt
        px = px[:2] / px[2]

        x, y = int(px[0]), int(px[1])
        if 0 <= x < self.width and 0 <= y < self.height:
            return (x, y)
        return None


def main():
    rclpy.init()
    node = RadarCameraProjector()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    import math  # noqa: E402
    main()
