# Mowen

Mecanum轮机器人ROS1 Melodic项目 - Gazebo仿真、SLAM建图、自主导航

## 项目概述
- **机器人类型**: Mecanum轮全向移动机器人
- **ROS版本**: ROS1 Melodic (Ubuntu 18.04)
- **仿真环境**: Gazebo 9 Classic
- **运行环境**: Docker容器 (ubuntu:18.04 + ROS Melodic)

## 功能特性
- ✅ Gazebo物理仿真 (完整机器人模型)
- ✅ 360° LiDAR扫描
- ✅ IMU姿态传感器
- ✅ Mecanum轮全向移动控制
- ✅ Cartographer SLAM 建图
- ✅ move_base 自主导航 (AMCL + DWA)

## 项目结构
- `docker/` - Docker环境配置 (Ubuntu 18.04 + ROS Melodic)
- `src/mowen_gazebo/` - Gazebo仿真包
- `src/mowen_cartographer/` - Cartographer SLAM
- `src/mowen_navigation/` - ROS1 Navigation (move_base)
- `docs/` - 文档

## 宿主机兼容性说明

本项目的 Docker 环境针对 **Ubuntu 24.04 宿主机**做了特殊优化：

- **GPU**: 支持 NVIDIA GPU (需安装 `nvidia-container-toolkit`)，自动 fallback 到软件渲染
- **X11**: 通过 XWayland 转发 Gazebo 和 RViz 窗口到宿主机
- **内核**: 已设置 `seccomp:unconfined` 解决 Gazebo 9 与 kernel 6.x 的兼容问题

如果宿主机的 NVIDIA 驱动或 Wayland 导致 Gazebo 崩溃，请参考 `docs/启动命令参考.md` 中的故障排除。

## 快速开始
```bash
# 启动Docker容器
cd docker && ./container.sh start

# 进入容器
./container.sh enter

# 构建项目
cd /root/mowen_ws && catkin_make

# 启动仿真
source devel/setup.bash
roslaunch mowen_gazebo empty_world.launch

# 启动 SLAM
roslaunch mowen_cartographer cartographer.launch use_sim_time:=true

# 启动导航
roslaunch mowen_navigation navigation.launch
```

## 文档
- 启动命令: [docs/启动命令参考.md](docs/启动命令参考.md)
- Bug修复记录: [docs/Bug修复记录.md](docs/Bug修复记录.md)
- ROS2→ROS1迁移说明: [docs/MIGRATION.md](docs/MIGRATION.md)

## 许可证
BSD-3-Clause
