# CLAUDE.md — mowen_radar_fusion 项目指引

## 项目目标
在 mowen 机器人（ROS2 Humble + Gazebo 11）上实现毫米波雷达-相机数据级融合，
参考 CRF-Net 方法。最终产出: 可运行的仿真验证 + 论文实验。

## 当前进度

- [x] 创建 mowen_radar_fusion ROS2 包
- [x] 完整 URDF (含雷达+相机传感器)
- [x] 实现雷达仿真节点 (LaserScan → RadarTargetArray)
- [x] 实现雷达→相机投影节点 (核心融合逻辑)
- [x] 文档 (README.md, docs/)
- [x] 生成 SDF + 编译验证 (colcon build)
- [x] Gazebo 仿真启动验证 (仓库场景 + 雷达相机投影已打通)
- [ ] 完善雷达消息定义 (当前无速度，可后续加多普勒仿真)
- [ ] 训练检测网络 (CRF-Net Step 2)
- [ ] 恶劣条件仿真测试 (烟雾/暗光场景)

## 关键路径

- 工作空间: /home/qc/resource/code/ros2/mowen
- URDF (完整机器人): src/mowen_radar_fusion/urdf/mowen_with_sensors.urdf
- SDF 生成脚本: src/mowen_radar_fusion/scripts/generate_sdf.py
- SDF 模型: src/mowen_radar_fusion/models/mowen_with_sensors/
- 网格资源 (不修改): src/mowen_gazebo/models/mowen_common/meshes/

## 重要规则

1. **所有 URDF/SDF 在 mowen_radar_fusion 内管理，不修改 mowen_gazebo**
2. **SDF 通过 generate_sdf.py 从 URDF 生成，禁止手动编辑 SDF XML**
3. 修改 URDF 后运行: `python3 scripts/generate_sdf.py` 重新生成 SDF
4. 代码全部 Python，不写 C++

## 传感器布局 (相对 base_link)

| 传感器 | 位置 (x,y,z) | 话题 |
|--------|-------------|------|
| radar  | 0.15, 0, 0.18 | /radar/scan → /radar/targets |
| camera | 0.149, 0, 0.20 | /camera/image_raw |
| LiDAR  | 0.134, 0, 0.136 | /scan |

## 编译和运行

```bash
cd /home/qc/resource/code/ros2/mowen
# 先确保 URDF 正确
python3 src/mowen_radar_fusion/scripts/generate_sdf.py
# 编译
colcon build --packages-select mowen_radar_fusion
source install/setup.bash
# 启动
ros2 launch mowen_radar_fusion radar_fusion.launch.py
```

## 参考代码

### 核心参考（已 clone 到本地）
- [CameraRadarFusionNet/CRF-Net](https://github.com/TUMFTM/CameraRadarFusionNet) → /home/qc/resource/code/CL/CameraRadarFusionNet
  - 论文: Nobis et al., "CRF-Net: A Deep Learning-based Radar and Camera Sensor Fusion Architecture", 2019
  - 方法: 数据级融合（雷达点投影到图像 + RetinaNet 检测）

- [CenterFusion](https://github.com/mrnabati/CenterFusion) → /home/qc/resource/code/CL/Homework1_CenterFusion
  - 论文: Nabati et al., "CenterFusion: Center-based Radar and Camera Fusion for 3D Object Detection", WACV 2021
  - 方法: 混合融合（Frustum 关联 + 特征融合）

### 其他参考
- [RCBEVDet](https://github.com/VDIGPKU/RCBEVDet) — CVPR 2024, 雷达-相机 BEV 融合
- [RCM-Fusion](https://github.com/mjseong0414/RCM-Fusion) — ICRA 2024, 雷达-相机多级融合
- [BEVFusion](https://github.com/mit-han-lab/bevfusion) — 多模态 BEV 融合

### 雷达资源
- [ainstein_radar](https://github.com/AinsteinAI/ainstein_radar) → /home/qc/resource/code/CL/ainstein_radar
  - Gazebo 雷达仿真插件 (ROS1, 已修复编译)
  - 用于参考雷达消息格式和仿真参数

### 综述论文
- Wei et al., "Integrating Multi-Modal Sensors", 2025 → ~/surveys/
- Xie et al., "Sensing Technologies for Indoor AMRs", 2024 → ~/surveys/

## 下一步任务优先级

1. 生成 SDF + colcon build 验证
2. Gazebo 仿真启动 + 雷达投影效果验证
3. 添加障碍物到世界 + 验证检测
4. 录制 rosbag 用于检测网络训练
5. 训练轻量检测网络 (MobileNet + 雷达增强)
