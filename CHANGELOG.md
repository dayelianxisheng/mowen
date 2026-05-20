# Mowen 项目更新日志

## [v2.0] - 2026-05-20

### 🎉 主要更新

#### Gazebo仿真环境完全重构
- ✅ **使用Gazebo官方工具转换URDF→SDF**
  - 解决了手动编写坐标系统的问题
  - 保留了参考项目的完整运动学定义
  
- ✅ **修复插件加载问题**
  - 添加 `LD_LIBRARY_PATH` 环境变量
  - 确保gzserver能找到ROS插件

- ✅ **Docker环境优化**
  - 基于 `robotis/turtlebot3:humble-latest`
  - ROS_DOMAIN_ID=30 隔离DDS通信
  - 完整的Gazebo模型路径配置

#### 代码质量改进
- ✅ 清理所有临时测试文件
- ✅ 统一代码格式和文件结构
- ✅ 完善项目文档

### 📁 文件变更

#### 删除文件
- `docs/Mowen2仿真SLAM导航_完整教程.md` → 替换为新教程
- `launch/empty_world_headless.launch.py` (临时测试)
- `launch/test_spawn.launch.py` (临时测试)
- `models/mowen/model_plugins.txt` (垃圾文件)

#### 新增文件
- `docs/Mowen_Gazebo仿真完整教程.md` — 全新的完整教程

#### 修改文件
- `docker/Dockerfile` — 添加 `LD_LIBRARY_PATH`
- `models/mowen/model.sdf` — 从参考URDF转换
- `models/mowen/model.config` — 版本号更新为1.11
- `launch/empty_world.launch.py` — 添加环境变量设置
- `CLAUDE.md` — 更新关键信息

### 🔧 技术栈

| 组件 | 版本 | 说明 |
|------|------|------|
| **ROS2** | Humble | Docker容器内 |
| **Gazebo** | 11 Classic | gzserver/gzclient |
| **驱动** | libgazebo_ros_planar_move.so | Mecanum全向移动 |
| **传感器** | LiDAR + IMU | 360°扫描 + 姿态数据 |

### 📝 已知问题

无严重问题。所有仿真功能正常工作。

### 🚀 下一步计划

- [ ] 添加Cartographer SLAM包
- [ ] 添加Nav2导航包
- [ ] 创建mowen元包

---

## [v1.0] - 初始版本

### 基础结构
- 创建Docker环境
- 基础URDF模型复制
- 初步Gazebo配置（有坐标问题）
