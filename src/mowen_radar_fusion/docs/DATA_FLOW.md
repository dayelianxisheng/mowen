# 数据流文档

## 总览

```
                         Gazebo 仿真
                             │
         ┌───────────────────┼───────────────────┐
         ▼                   ▼                   ▼
    /radar/scan         /rgb_camera/          /scan
    LaserScan           image_raw             LaserScan
         │                   │                   │
         ▼                   │                   │
  ① radar_sim_node          │                   │
    LaserScan→              │                   │
    RadarTargetArray         │                   │
         │                   │                   │
         ▼                   ▼                   ▼
  ② radar_camera_projector ◄────────────────────┘
    ├─ 订阅: /radar/targets, /rgb_camera/image_raw, /rgb_camera/camera_info
    ├─ 输出: /camera/image_radar (增强图)
    └─ 输出: /camera/radar_overlay (覆盖图)
                             │
              ┌──────────────┤
              ▼              ▼
  ③ radar_detector     ⑤ fusion_visualizer
    ├─ 订阅: /camera/image_radar       ├─ 订阅: /rgb_camera/image_raw
    │        /rgb_camera/image_raw     │        /camera/image_radar
    ├─ 模型: Faster R-CNN (COCO)       └─ 输出: /camera/fusion_display
    ├─ 输出: /detections
    └─ 输出: /detection_image (标注图)
```

## 节点详情

### ① radar_sim_node — 雷达仿真转换

- **代码**: `mowen_radar_fusion/radar_sim_node.py`
- **订阅**: `/radar/scan` (sensor_msgs/LaserScan)
  - 来自 Gazebo 毫米波雷达传感器 (10束, ±40°, 0.5-35m)
- **发布**: `/radar/targets` (RadarTargetArray)
  - 自定义消息: 将 LaserScan 的每个点转换为距离+方位角+俯仰角的目标列表

```
每个 LaserScan 点 (range, angle) → RadarTarget(range, azimuth, elevation)
```

### ② radar_camera_projector — 核心融合节点

- **代码**: `mowen_radar_fusion/radar_camera_projector.py`
- **订阅**:
  - `/radar/targets` (RadarTargetArray)
  - `/rgb_camera/image_raw` (sensor_msgs/Image)
  - `/rgb_camera/camera_info` (sensor_msgs/CameraInfo)
- **发布**:
  - `/camera/image_radar` — 叠加雷达投影线的增强图像
  - `/camera/radar_overlay` — 半透明雷达覆盖层

**核心算法 (每个雷达目标)**:

```
1. 球坐标 → 笛卡尔坐标
   x = range × cos(azimuth) × cos(elevation)
   y = range × sin(azimuth) × cos(elevation)
   z = range × sin(elevation)

2. 相机外参定位
   TF: radar_link → camera_optical
   相机原点 t = 外参平移
   旋转矩阵 R = 外参旋转

3. 雷达高度扩展 (CRF-Net 风格)
   底部: z_bottom = -1.0m (补偿雷达无俯仰角)
   顶部: z_top    = +2.0m
   → 在图像上生成垂直线而非单点

4. 相机坐标 → 像素坐标
   P = K × [R|t] × X
   u = P.x / P.z
   v = P.y / P.z

5. 颜色编码
   ratio = range / max_distance  (max_distance=10m)
   B = 255 × ratio          (远=蓝)
   G = 0
   R = 255 × (1 - ratio)    (近=红)
```

### ③ radar_detector — CNN 目标检测

- **代码**: `mowen_radar_fusion/radar_detector.py`
- **订阅**:
  - `/camera/image_radar` (雷达增强图, 触发检测)
  - `/rgb_camera/image_raw` (原始相机图)
  - `/rgb_camera/camera_info` (相机内参)
- **模型**: Faster R-CNN (ResNet-50 FPN, COCO 预训练)
- **硬件**: CUDA GPU
- **发布**:
  - `/detections` (vision_msgs/Detection2DArray) — 结构化检测结果
  - `/detection_image` (sensor_msgs/Image) — 带 BBox + 标签的标注图

**检测流程**:
```
雷达增强图 → Faster R-CNN → Boxes + Scores + Labels
    ↓
每个 BBox + 雷达距离 (最近雷达目标) → 标签: "car 0.85 3.2m"
    ↓
/detections (消息) + /detection_image (标注图)
```

### ④ Gazebo 传感器层

- **SDF 模型**: `models/mowen_with_sensors/model.sdf` (由 `scripts/add_sensors_to_model.py` 生成)
- **URDF 模型**: `urdf/mowen_with_sensors.urdf`

| 传感器 | SDF sensor name | 话题 | 参数 |
|--------|----------------|------|------|
| LiDAR | `lds_laser` | `/scan` | 1440束, 360°, 0.12-3.5m |
| 雷达 | `radar_range` | `/radar/scan` | 10束, ±40°, 0.5-35m |
| 相机 | `rgb_camera` | `/rgb_camera/image_raw` | 640×480, 30Hz |

### ⑤ fusion_visualizer — 可视化

- **代码**: `mowen_radar_fusion/fusion_visualizer_node.py`
- **订阅**: `/rgb_camera/image_raw`, `/camera/image_radar`
- **发布**: `/camera/fusion_display` — 并排对比图 (原始 | 雷达增强)

### ⑥ 启动配置

- **Launch 文件**: `launch/radar_fusion.launch.py` — 一次性启动全部 8 个节点
- **世界文件**: `models/race_scene.world` — 竞赛场景 (12×8m 围墙场地)
- **竞赛模型**: `models/race_models/` — Gazebo 模型库 (锥桶/车/人/树, 来自 osrf/gazebo_models)

## 启动

```bash
ros2 launch mowen_radar_fusion radar_fusion.launch.py
```

启动后自动运行所有节点，无需额外配置。

## 查看结果

```bash
# 雷达增强图
ros2 run rqt_image_view rqt_image_view /camera/image_radar

# CNN 检测结果
ros2 run rqt_image_view rqt_image_view /detection_image

# 并排对比
ros2 run rqt_image_view rqt_image_view /camera/fusion_display
```
