# Mowen

Mecanum 轮全向移动机器人 —— ROS2 Humble 项目，支持 Gazebo 仿真、Cartographer SLAM 建图、Nav2 自主导航、毫米波雷达-相机融合。

## 功能特性

| 模块 | 功能 | 状态 |
|---|---|---|
| Gazebo 仿真 | 完整机器人模型 + 物理仿真 (Gazebo 11) | ✅ |
| LiDAR | 360° 激光扫描 (1440采样点, 最大3.5m) | ✅ |
| IMU | 姿态传感器 | ✅ |
| Mecanum 驱动 | 全向移动控制 (PlanarMovePlugin) | ✅ |
| Cartographer | 2D SLAM 实时建图 + 闭环检测 | ✅ |
| Nav2 导航 | AMCL 定位 + 全局/局部路径规划 + 避障 | ✅ |
| 雷达-相机融合 | 毫米波雷达→图像投影 + CNN 目标检测 (CRF-Net) | ✅ |

## 项目结构

```
src/
├── mowen_gazebo/         # Gazebo 仿真包
│   ├── launch/           # 仿真启动文件
│   ├── urdf/             # 机器人 URDF 模型
│   ├── models/           # SDF 仿真模型 + STL 网格
│   ├── worlds/           # Gazebo 世界文件
│   ├── rviz/             # RViz2 配置文件
│   └── config/           # Gazebo 控制器配置
├── mowen_cartographer/   # Cartographer SLAM 包
│   ├── launch/           # SLAM 启动文件
│   ├── config/           # Lua 参数配置
│   └── rviz/             # RViz2 配置文件
├── mowen_navigation/     # Nav2 导航包
│   ├── launch/           # 导航启动文件
│   ├── config/           # Nav2 参数 (AMCL/DWB/costmap)
│   └── map/              # 预建地图
└── mowen_radar_fusion/   # 雷达-相机融合包
    ├── launch/           # 一键启动
    ├── msg/              # 自定义消息 (RadarTarget, RadarTargetArray)
    ├── mowen_radar_fusion/ # Python 节点
    │   ├── radar_sim_node.py           # 雷达格式转换
    │   ├── radar_camera_projector.py   # 核心: 雷达→像素投影
    │   ├── radar_detector.py           # ★ CNN 检测 (Faster R-CNN)
    │   └── fusion_visualizer_node.py   # 可视化
    ├── urdf/             # 含雷达+相机的完整 URDF
    ├── models/           # SDF 模型 + 竞赛场景
    ├── scripts/          # SDF 生成 + 投影 Demo
    └── docs/             # 数据流文档 + 论文参考
docker/                   # Docker 环境
docs/                     # 文档与记录
```

## 雷达-相机融合架构

```
Gazebo 仿真
├── /radar/scan        (毫米波雷达, 10束, ±40°, 0.5-35m)
├── /rgb_camera/image_raw (RGB 640×480, 30Hz)
└── /scan              (LiDAR 360°)

        ↓
① radar_sim_node          LaserScan → RadarTargetArray
        ↓
② radar_camera_projector  球坐标→笛卡尔→TF→像素→画线 (近红远蓝)
        ↓
③ radar_detector          Faster R-CNN (ResNet-50, COCO预训练)
        ↓                  检测 + 雷达距离标签
   /detections             结构化检测结果
   /detection_image        标注图 (BBox + 类别 + 距离)
```

**核心算法**: CRF-Net 风格 —— 将毫米波雷达目标投影到相机图像平面，用颜色编码距离（红近蓝远），CNN 在增强图上做目标检测。

**检测模型**: `ObjectDetector` (纯 PyTorch, 可与 ROS2 解耦)
- Faster R-CNN + ResNet-50 FPN + COCO 预训练
- `DetectionConfig` 统一管理所有超参
- 输出结构化 `DetectionResult` (box/score/label/distance)
- 后续可 fine-tune 或替换为 YOLO

**论文参考**: [CRF-Net](https://arxiv.org/abs/2005.07431) — *A Deep Learning-based Radar and Camera Sensor Fusion Architecture for Object Detection* (TUM, 2019)

## 快速开始

### 1. 启动 Docker 容器

```bash
cd docker
./container.sh build   # 首次构建
./container.sh start   # 启动容器
./container.sh enter   # 进入容器
```

### 2. 构建项目

```bash
cd /root/mowen_ws
colcon build --symlink-install
source install/setup.bash
```

### 3. 启动 Gazebo 仿真

```bash
# 空世界
ros2 launch mowen_gazebo empty_world.launch.py
```

### 4. 键盘控制

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel
```

### 5. SLAM 建图

```bash
ros2 launch mowen_cartographer cartographer.launch.py use_sim_time:=true
```

### 6. 导航

```bash
ros2 launch mowen_navigation navigation.launch.py use_sim_time:=true
```

### 7. 雷达-相机融合（一键启动）

```bash
# 完整启动：Gazebo + 竞赛场景 + 雷达/相机/CNN 所有节点
ros2 launch mowen_radar_fusion radar_fusion.launch.py

# 控制小车
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel

# 查看检测结果
ros2 run rqt_image_view rqt_image_view /detection_image

# 查看雷达投影
ros2 run rqt_image_view rqt_image_view /camera/image_radar

# 独立测试每个节点（无需 Gazebo）
python3 mowen_radar_fusion/radar_sim_node.py --test
python3 mowen_radar_fusion/radar_camera_projector.py --test
python3 mowen_radar_fusion/radar_detector.py --test
python3 mowen_radar_fusion/fusion_visualizer_node.py --test
```

## 参考资料

- [启动命令参考](docs/启动命令参考.md)
- [Bug修复记录](docs/Bug修复记录.md)

## License

BSD-3-Clause
