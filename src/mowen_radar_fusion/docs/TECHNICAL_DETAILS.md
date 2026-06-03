# 技术细节

## 1. 为什么用 RaySensor 模拟毫米波雷达

Gazebo 没有内置的毫米波雷达传感器模型。我们使用 `RaySensor` 近似模拟:

| 参数 | LiDAR (lds_laser) | 雷达 (radar_range) |
|------|------------------|-------------------|
| 波束数 | 1440 | 10 |
| 角度范围 | 360° | ±40° (共80°) |
| 最小距离 | 0.12m | 0.5m |
| 最大距离 | 3.5m | 35m |
| 噪声 | 1cm | 5cm |
| 更新率 | 10Hz | 10Hz |
| 话题 | /scan | /radar/scan |

关键区别: 雷达波束极少（稀疏）、测距远、噪声大。

## 2. 相机坐标系约定 (ROS REP 103)

```
相机光学坐标系 (camera_optical):
  z-axis → 前方（相机拍摄方向）
  x-axis → 右方
  y-axis → 下方

相机物理坐标系 (camera_link):
  x-axis → 前方
  y-axis → 左方
  z-axis → 上方
```

变换: camera_link → camera_optical:
  rotation: roll=-90°, pitch=0, yaw=-90° (将 x-forward 转为 z-forward)

## 3. 雷达消息设计

为了和 ainstein_radar_msgs 兼容，自定义消息结构相同:

```
RadarTarget:
  uint32 target_id   # 目标编号
  float64 range      # 距离 (m)
  float64 speed      # 速度 (m/s, 当前为0)
  float64 azimuth    # 水平角 (rad)
  float64 elevation  # 垂直角 (rad)
  float64 snr        # 信噪比 (dB)

RadarTargetArray:
  std_msgs/Header header
  RadarTarget[] targets
```

## 4. 数据流时序

```
Gazebo tick:
  ├── gzserver 物理步进
  ├── radar_range 传感器更新 → /radar/scan
  ├── rgb_camera 传感器更新 → /camera/image_raw + /camera/camera_info
  └── radar_sim_node 收到 /radar/scan → /radar/targets
      radar_camera_projector 收到图像+雷达 → /camera/image_radar
```

## 5. 已知限制

1. **无多普勒测速**: Gazebo RaySensor 只能测距，无法获取速度。radar_sim_node 的 speed 字段恒为 0
2. **无 RCS**: 雷达散射截面无法仿真。snr 用激光反射强度近似
3. **理想化噪声**: 5cm 高斯噪声无法模拟真实雷达的多径反射和虚警
4. **2D 雷达**: RaySensor 只有水平扫描，elevation 恒为 0。真实毫米波雷达有一定的垂直分辨率

## 6. 从仿真到真机

如果后续接上真机毫米波雷达 (如 TI IWR6843):

```python
# 替换 radar_sim_node 的输入
# 仿真: 订阅 /radar/scan (LaserScan)
# 真机: 订阅真实的雷达驱动话题 (如 /ti_mmwave/radar_scan)

# 只需修改订阅的话题名和消息类型，投影逻辑不变
```
