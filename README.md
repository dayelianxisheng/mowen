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
| 雷达-相机融合 | 毫米波雷达目标投影至相机图像 (CRF-Net) | 🚧 |

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
    ├── launch/           # 融合启动文件
    ├── config/           # 传感器参数配置
    ├── msg/              # 自定义消息 (RadarTargetArray)
    ├── mowen_radar_fusion/ # Python 融合节点
    ├── scripts/          # SDF 生成脚本
    ├── urdf/             # 含雷达+相机的完整 URDF
    └── models/           # 融合模型 SDF
docker/                   # Docker 环境
docs/                     # 文档与记录
```

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

### 7. 雷达-相机融合

```bash
# 先启动仿真
ros2 launch mowen_gazebo mowen_world.launch.py
# 启动雷达融合
ros2 launch mowen_radar_fusion radar_fusion.launch.py
```

## 参考资料

- [启动命令参考](docs/启动命令参考.md)
- [Bug修复记录](docs/Bug修复记录.md)

## License

BSD-3-Clause
