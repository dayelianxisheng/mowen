# Mowen

Mecanum轮机器人ROS2 Humble项目 - Gazebo仿真、SLAM建图、自主导航

## 项目概述
- **机器人类型**: Mecanum轮全向移动机器人
- **ROS版本**: ROS2 Humble
- **仿真环境**: Gazebo 11 Classic
- **运行环境**: Docker容器 (robotis/turtlebot3:humble-latest)

## 功能特性
- ✅ Gazebo物理仿真 (完整机器人模型)
- ✅ 360° LiDAR扫描
- ✅ IMU姿态传感器
- ✅ Mecanum轮全向移动控制

## 项目结构
- `docker/` - Docker环境配置
- `src/mowen_gazebo/` - Gazebo仿真包
- `docs/` - 完整教程文档

## 快速开始
```bash
# 启动Docker容器
cd docker && ./container.sh start

# 进入容器
./container.sh enter

# 构建项目
cd /root/mowen_ws && colcon build --symlink-install

# 启动仿真
source install/setup.bash
ros2 launch mowen_gazebo empty_world.launch.py
```

## 文档
详细教程请查看: [docs/Mowen_Gazebo仿真完整教程.md](docs/Mowen_Gazebo仿真完整教程.md)

## 许可证
BSD-3-Clause

