# mowen_radar_fusion — 雷达-相机数据级融合

基于 CRF-Net 的毫米波雷达-相机融合 + Faster R-CNN 目标检测。

## 快速启动

```bash
# 进入 ROS2 容器
cd /home/qcqc/resource/code/eai/mowen/docker-ros2
./container.sh start && ./container.sh enter

# 构建
source /opt/ros/humble/setup.bash
cd /root/mowen_ws
colcon build --symlink-install
source install/setup.bash

# 清理旧 Gazebo 进程
pkill -9 -f gzserver; pkill -9 -f gzclient; sleep 1

# 启动完整管线（Gazebo + 场景 + 所有节点）
ros2 launch mowen_radar_fusion radar_fusion.launch.py
```

## 常用命令

```bash
# ---- 查看话题 ----
ros2 topic list

# ---- 键盘控制小车 ----
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel

# ---- 查看检测结果 ----
ros2 run rqt_image_view rqt_image_view          # 选 /detection_image
ros2 run rqt_image_view rqt_image_view          # 选 /camera/image_radar

# ---- 打开 RViz ----
rviz2 -d /root/mowen_ws/src/mowen_radar_fusion/rviz/radar_fusion.rviz

# ---- 调试：检查话题发布 ----
ros2 topic hz /rgb_camera/image_raw
ros2 topic hz /radar/scan
ros2 topic echo /odom | grep "angular"

# ---- 清理并重启 ----
pkill -9 -f gzserver; pkill -9 -f gzclient; sleep 1
rm -rf ~/.gazebo/models
ros2 launch mowen_radar_fusion radar_fusion.launch.py
```

## 话题

| 话题 | 类型 | 说明 |
|------|------|------|
| `/rgb_camera/image_raw` | Image | 相机原始画面 |
| `/camera/image_radar` | Image | 叠加雷达投影线 |
| `/detection_image` | Image | CNN 检测结果（框+标签） |
| `/detections` | Detection2DArray | 检测结果消息 |
| `/radar/scan` | LaserScan | 毫米波雷达仿真 |
| `/radar/targets` | RadarTargetArray | 雷达目标列表 |
| `/scan` | LaserScan | LiDAR 扫描 |
| `/odom` | Odometry | 里程计 |
| `/cmd_vel` | Twist | 速度控制 |

## 架构

```
Gazebo 仿真
├── /radar/scan    (LaserScan, 10束, ±40°, 0.5-35m)
├── /rgb_camera/image_raw (RGB 640x480, 30Hz)
└── /scan          (LiDAR 360°)

        ↓
radar_sim_node         → /radar/targets
radar_camera_projector → /camera/image_radar
radar_detector         → /detection_image, /detections
fusion_visualizer_node → /camera/fusion_display
```

## 场景

- `models/scene.world` — 封闭房间 + person/car/table
- `models/cafe_models/` — COCO 物体模型库（person、hatchback、table 等）

## 传感器布局 (相对 base_link)

| 传感器 | 位置 (x,y,z) |
|--------|-------------|
| radar  | 0.15, 0, 0.18 |
| camera | 0.149, 0, 0.20 |
| LiDAR  | 0.134, 0, 0.136 |
