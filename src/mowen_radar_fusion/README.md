# mowen_radar_fusion — 雷达-相机数据级融合

基于 CRF-Net 思想，将毫米波雷达目标投影到相机图像平面，实现传感器数据级融合。

## 架构

```
Gazebo 仿真
├── /radar/scan    (LaserScan, 10束, ±40°, 0.5-35m)
├── /camera/image_raw (RGB 640x480, 30Hz)
└── /camera/camera_info

        ↓

radar_sim_node.py
   LaserScan → RadarTargetArray → /radar/targets

radar_camera_projector.py
   /radar/targets + /camera/image_raw + /camera/camera_info
        ↓
   雷达球坐标 → 笛卡尔 → TF变换 → 像素坐标 → 投影线
        ↓
   /camera/image_radar (增强图像)

fusion_visualizer_node.py
   /camera/image_raw + /camera/image_radar → 双窗口显示
```

## 传感器布局

```
        前方 →
┌─────────────────────────────┐
│  📶 radar (0.15, 0, 0.18)    │  ← 毫米波雷达
│  📷 camera (0.149, 0, 0.20)  │  ← RGB-D 相机
│  📡 LiDAR (0.134, 0, 0.136)  │  ← 激光雷达
│        ┌───────────┐         │
│        │  mowen    │         │
│        │  chassis  │         │
│        └───────────┘         │
└─────────────────────────────┘
         base_link
```

## 快速启动

```bash
# 1. 编译
cd /home/qc/resource/code/ros2/mowen
colcon build --packages-select mowen_radar_fusion
source install/setup.bash

# 2. 启动 Gazebo 仿真
ros2 launch mowen_gazebo mowen_world.launch.py

# 3. 启动雷达融合
ros2 launch mowen_radar_fusion radar_fusion.launch.py
```

## 话题

| 话题 | 类型 | 发布者 |
|------|------|--------|
| `/radar/scan` | LaserScan | Gazebo (libgazebo_ros_ray_sensor) |
| `/radar/targets` | RadarTargetArray | radar_sim_node |
| `/rgb_camera/image_raw` | Image | Gazebo (libgazebo_ros_camera) |
| `/rgb_camera/camera_info` | CameraInfo | Gazebo (libgazebo_ros_camera) |
| `/camera/image_radar` | Image | radar_camera_projector |
| `/camera/radar_overlay` | Image | radar_camera_projector |

## TF 树

```
base_link
├── radar_link      (雷达传感器)
├── camera_link → camera_optical  (相机，ROS REP 103)
├── laser_link      (LiDAR)
└── imu_link        (IMU)
```

## 参数配置

详见 `config/sensor_params.yaml`

## 核心算法

### 雷达→相机投影

```
1. 雷达球坐标 → 笛卡尔坐标:
   x = range * cos(azimuth) * cos(elevation)
   y = range * sin(azimuth) * cos(elevation)
   z = range * sin(elevation)

2. 雷达坐标 → 相机坐标 (TF 变换):
   pt_cam = R * pt_radar + t

3. 相机坐标 → 像素坐标 (内参投影):
   px = K * pt_cam
   u = px[0] / px[2], v = px[1] / px[2]
```

### CRF-Net 风格的投影线

```
每个雷达点 → 底部像素 (z = radar_height_min)
           → 顶部像素 (z = radar_height_max)
           → 在图像上画垂直线
线的颜色 = 根据距离编码 (近红远蓝)
```

## SDF 修改规则

**任何对 `model.sdf` 的修改必须通过 Python 脚本完成，禁止手动编辑 XML。**

修改脚本放在 `/home/qc/resource/code/ros2/mowen/scripts/` 目录下。

当前传感器配置脚本: `scripts/add_radar_and_camera_sensors.py`
