#!/usr/bin/env python3
"""
雷达→相机投影 Demo (纯Python，无需ROS)
======================================
展示毫米波雷达目标如何投影到相机图像平面上。

核心流程:
  1. 雷达球坐标 (距离, 方位角) → 笛卡尔坐标 (x, y, z)
  2. 雷达坐标 → 相机坐标 (通过外参: 旋转R + 平移t)
  3. 相机坐标 → 像素坐标 (通过内参K)
  4. 在图像上画投影线 (CRF-Net风格: 距离编码颜色)

运行: python3 demo_projection.py
"""

import numpy as np
import cv2

# ============================================================
# 1. 模拟传感器配置 (与 mowen 机器人一致)
# ============================================================

# 相机内参 (640x480, 水平FOV 60°)
IMG_W, IMG_H = 640, 480
fx = IMG_W / (2 * np.tan(np.deg2rad(60) / 2))  # ~554
fy = fx  # 假设正方形像素
cx, cy = IMG_W / 2, IMG_H / 2
K = np.array([[fx, 0, cx],
              [0, fy, cy],
              [0,  0,  1]])

# 雷达→相机外参 (雷达在相机后方偏上)
# camera_link 位置: (0.149, 0, 0.20)
# radar_link 位置:  (0.15,  0, 0.18)
# 差值: radar在相机前方0.001m, 下方0.02m
R = np.eye(3)  # 两者朝向相同 (都是朝前)
t = np.array([0.001, 0, -0.02])

# ============================================================
# 2. 模拟雷达数据 (距离米, 方位角弧度)
# ============================================================
radar_pts = [
    (3.0,  0.3),   # 前方3m, 右偏17°
    (5.0, -0.2),   # 前方5m, 左偏11°
    (2.0,  0.0),   # 前方2m, 正前方
    (8.0,  0.5),   # 前方8m, 右偏28°
    (4.0, -0.4),   # 前方4m, 左偏23°
    (1.5,  0.1),   # 前方1.5m, 右偏6°
    (12.0, 0.0),   # 前方12m, 正前方
    (6.0, -0.6),   # 前方6m, 左偏34° (可能超出FOV)
]

# ============================================================
# 3. 投影核心算法
# ============================================================

def radar_to_pixel(range_m, azimuth_rad, K, R, t):
    """
    雷达点 → 像素坐标

    参数:
      range_m:    距离 (米)
      azimuth_rad: 方位角 (弧度, 以相机光轴为0)
      K: 相机内参矩阵 (3x3)
      R: 旋转矩阵 (3x3)
      t: 平移向量 (3x1)

    返回:
      (u, v, in_fov) 或 (None, None, False) 如果投影失败
    """
    # Step A: 球坐标 → 笛卡尔 (雷达坐标系)
    x_r = range_m * np.cos(azimuth_rad)  # 前方
    y_r = range_m * np.sin(azimuth_rad)  # 侧方
    z_r = 0.0  # 毫米波雷达无高度信息 (实际=0 或 默认高度)
    pt_radar = np.array([x_r, y_r, z_r])

    # Step B: 雷达坐标 → 相机坐标 (TF变换)
    pt_cam = R @ pt_radar + t

    # 检查是否在相机前方
    if pt_cam[0] <= 0:
        return None, None, False

    # Step C: 相机坐标 → 像素坐标 (内参投影)
    px_homo = K @ pt_cam
    u = px_homo[0] / px_homo[2]
    v = px_homo[1] / px_homo[2]

    # 检查是否在图像范围内
    in_fov = (0 <= u < IMG_W) and (0 <= v < IMG_H)
    return u, v, in_fov


# ============================================================
# 4. 可视化
# ============================================================

def distance_color(dist, max_dist=15.0):
    """距离编码颜色: 近→红色, 远→蓝色 (CRF-Net风格)"""
    ratio = min(dist / max_dist, 1.0)
    r = int(255 * (1 - ratio))
    b = int(255 * ratio)
    return (b, 0, r)  # BGR for OpenCV


# 创建空白图像 (模拟相机画面, 用灰色背景)
image = np.ones((IMG_H, IMG_W, 3), dtype=np.uint8) * 60
cv2.putText(image, "Radar -> Camera Projection Demo", (30, 30),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)

# 画水平参考线
for y in range(0, IMG_H, 60):
    cv2.line(image, (0, y), (IMG_W, y), (40, 40, 40), 1)

for i, (dist, az) in enumerate(radar_pts):
    u, v, in_fov = radar_to_pixel(dist, az, K, R, t)

    if u is None:
        print(f"  [{i}] {dist:.1f}m, {np.rad2deg(az):+.0f}° → 相机后方, 跳过")
        continue

    color = distance_color(dist)
    print(f"  [{i}] {dist:.1f}m, {np.rad2deg(az):+.0f}° → 像素 ({u:.0f}, {v:.0f}) {'✓' if in_fov else '✗超出FOV'}")

    base_y = 20  # 雷达的默认高度 (米内的z, 对应图像底部附近)

    if in_fov:
        # 画投影线 (CRF-Net风格垂直线)
        line_top = max(0, int(v - 40))
        line_bot = min(IMG_H - 1, int(v + 40))
        cv2.line(image, (int(u), line_top), (int(u), line_bot), color, 2)

        # 画目标点
        cv2.circle(image, (int(u), int(v)), 5, color, -1)

        # 距离标签
        label = f"{dist:.1f}m"
        cv2.putText(image, label, (int(u) + 8, int(v) - 8),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
    else:
        # 超出FOV: 在图像边缘画箭头指示方向
        edge_u = max(0, min(IMG_W - 1, int(u)))
        cv2.putText(image, f"{dist:.1f}m ->", (edge_u - 40, IMG_H // 2 + i * 15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.35, color, 1)

# 图例
legend_y = 60
for d in [2, 5, 10, 15]:
    c = distance_color(d)
    cv2.putText(image, f"{d}m", (IMG_W - 80, legend_y),
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, c, 1)
    legend_y += 18

# 显示 + 保存
cv2.imshow("Radar Projection Demo", image)
print(f"\n按任意键关闭窗口...")
cv2.imwrite("radar_projection_demo.png", image)
print(f"已保存 radar_projection_demo.png")
cv2.waitKey(0)
cv2.destroyAllWindows()
