# mowen_radar_fusion — 雷达-相机数据级融合

基于 CRF-Net 的毫米波雷达-相机融合 + Faster R-CNN 目标检测。

## 快速启动

```bash
# 进入 ROS2 容器
cd ~/resource/code/ros2/mowen/docker
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

## 下载竞赛场景 (首次使用)

```bash
cd /root/mowen_ws/src/mowen_radar_fusion/models

# 稀疏克隆 osrf/gazebo_models (只下载需要的，~150MB)
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/osrf/gazebo_models.git /tmp/gazebo_sparse
cd /tmp/gazebo_sparse
git sparse-checkout set \
  construction_cone construction_barrel cardboard_box jersey_barrier \
  stop_sign stop_light lamp_post person_standing hatchback hatchback_red \
  dumpster cafe_table fire_hydrant bus_stop pine_tree oak_tree \
  number1 number2 number3 number4 number5

cp -r construction_cone construction_barrel cardboard_box jersey_barrier \
  stop_sign stop_light lamp_post person_standing hatchback hatchback_red \
  dumpster cafe_table fire_hydrant bus_stop pine_tree oak_tree \
  number1 number2 number3 number4 number5 \
  /root/mowen_ws/src/mowen_radar_fusion/models/race_models/

rm -rf /tmp/gazebo_sparse
```

## 场景

| 文件 | 说明 |
|------|------|
| `models/race_scene.world` | 竞赛场地 (12×8m 围墙 + 赛道 + 障碍物) |
| `models/race_models/` | 竞赛模型 (锥桶/车/人/树/标志, 22个) |
| `models/scene.world` | 封闭房间 + person/car/table |
| `models/mowen_with_sensors/` | 含雷达+相机的机器人 SDF |

## 话题

| 话题 | 类型 | 说明 |
|------|------|------|
| `/rgb_camera/image_raw` | Image | 相机原始画面 |
| `/camera/image_radar` | Image | 叠加雷达投影线 (近红远蓝) |
| `/detection_image` | Image | CNN 检测结果 (框+标签+距离) |
| `/detections` | Detection2DArray | 检测结果消息 |
| `/radar/scan` | LaserScan | 毫米波雷达 (10束, ±40°, 0.5-35m) |
| `/radar/targets` | RadarTargetArray | 雷达目标列表 |
| `/scan` | LaserScan | LiDAR 360° 扫描 |
| `/odom` | Odometry | 里程计 |
| `/cmd_vel` | Twist | 速度控制 |

## 架构

```
Gazebo 仿真
├── /radar/scan        (毫米波雷达, 10束, ±40°, 0.5-35m)
├── /rgb_camera/image_raw (RGB 640×480, 30Hz)
└── /scan              (LiDAR 360°)

        ↓
① radar_sim_node.py          LaserScan → RadarTargetArray
② radar_camera_projector.py  球坐标→笛卡尔→TF→像素→画线
③ radar_detector.py          Faster R-CNN (ResNet-50) 检测
④ fusion_visualizer_node.py  并排可视化
```

## 传感器布局 (相对 base_link)

| 传感器 | 位置 (x,y,z) |
|--------|-------------|
| radar  | 0.15, 0, 0.18 |
| camera | 0.149, 0, 0.20 |
| LiDAR  | 0.134, 0, 0.136 |

## 常用命令

```bash
# 查看话题
ros2 topic list

# 键盘控制
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -r cmd_vel:=/cmd_vel

# 查看检测结果
ros2 run rqt_image_view rqt_image_view /detection_image

# 查看雷达投影
ros2 run rqt_image_view rqt_image_view /camera/image_radar

# 独立测试节点 (无需 Gazebo)
python3 mowen_radar_fusion/radar_sim_node.py --test
python3 mowen_radar_fusion/radar_camera_projector.py --test
python3 mowen_radar_fusion/radar_detector.py --test
python3 mowen_radar_fusion/fusion_visualizer_node.py --test

# 清理旧进程
pkill -9 -f gzserver; pkill -9 -f gzclient; sleep 1
```

## 论文参考

[CRF-Net](https://arxiv.org/abs/2005.07431) — *A Deep Learning-based Radar and Camera Sensor Fusion Architecture for Object Detection* (Nobis et al., TUM, 2019)
