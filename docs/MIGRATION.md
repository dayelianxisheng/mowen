# ROS2 Humble → ROS1 Melodic 迁移记录

> 迁移日期: 2026-06-01

## 迁移概述

将 Mowen 项目从 ROS2 Humble (Gazebo 11) 迁移到 ROS1 Melodic (Gazebo 9)，同时通过 Docker 环境解决 Ubuntu 24.04 宿主机的兼容性问题。

## 主要变更

### 1. 构建系统

| 组件 | ROS2 | ROS1 |
|------|------|------|
| 构建工具 | `colcon build` | `catkin_make` |
| package.xml format | `format="3"` | `format="2"` |
| CMake 宏 | `ament_cmake`, `ament_package()` | `catkin`, `catkin_package()` |
| 安装目标 | `DESTINATION share/${PROJECT_NAME}` | `DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}` |
| 环境 source | `install/setup.bash` | `devel/setup.bash` |

### 2. 依赖包映射

| ROS2 (原) | ROS1 (目标) |
|-----------|-------------|
| `rclcpp` | `roscpp` |
| `tf2` | `tf` |
| `gazebo_ros_pkgs` | `gazebo_ros` + `gazebo_plugins` |
| `nav2_bringup` | `move_base` + `amcl` + `map_server` |
| `nav2_navfn_planner` | `navfn` |
| `dwb_core::DWBLocalPlanner` | `dwa_local_planner/DWAPlannerROS` |
| `nav2_amcl::OmniMotionModel` | `amcl` `odom_model_type: "omni"` |

### 3. Launch 文件

所有 `.launch.py` (Python) → `.launch` (XML)，共 7 个文件：

| 原文件 | 新文件 |
|--------|--------|
| `empty_world.launch.py` | `empty_world.launch` |
| `mowen_world.launch.py` | `mowen_world.launch` |
| `robot_state_publisher.launch.py` | `robot_state_publisher.launch` |
| `spawn_mowen.launch.py` | `spawn_mowen.launch` |
| `cartographer.launch.py` | `cartographer.launch` |
| `occupancy_grid.launch.py` | `occupancy_grid.launch` |
| `navigation.launch.py` | `navigation.launch` |

### 4. 导航参数

`nav2_params.yaml` (385行) → 6个 ROS1 YAML 文件：

| 新文件 | 内容 |
|--------|------|
| `amcl_params.yaml` | AMCL 全向运动模型参数 |
| `move_base_params.yaml` | 全局/局部规划器选择 + 恢复行为 |
| `costmap_common_params.yaml` | 共用的 costmap 层配置 |
| `global_costmap_params.yaml` | 全局 costmap 参数 |
| `local_costmap_params.yaml` | 局部 costmap 参数 |
| `dwa_local_planner_params.yaml` | DWA 局部规划器参数 (holonomic) |

### 5. SDF 模型插件

| 插件 | 变更 |
|------|------|
| 激光传感器 | `libgazebo_ros_ray_sensor.so` → `libgazebo_ros_laser.so`, `<ros>` → `<topicName>` |
| 全向移动 | 库名不变, `<ros><remapping>` → `<commandTopic>/<odometryTopic>` |
| 关节状态 | 库名不变, `<ros><remapping>` → `<robotNamespace>` |

### 6. RViz 配置

- 类名前缀: `rviz_default_plugins/` + `rviz_common/` → `rviz/`
- 删除所有 QoS 设置 (Durability Policy, Reliability Policy 等)
- 删除 Window Geometry 段

### 7. Docker 环境

| 配置项 | ROS2 (原) | ROS1 (目标) |
|--------|-----------|-------------|
| 基础镜像 | `robotis/turtlebot3:humble-latest` | `ubuntu:18.04` |
| ROS 版本 | Humble (22.04) | Melodic (18.04) |
| Gazebo | 11 | 9 |
| 发现机制 | DDS (ROS_DOMAIN_ID=30) | TCP (无 DOMAIN, 用 roscore) |
| seccomp | 默认 | `unconfined` (kernel 6.x兼容) |
| 共享内存 | `/dev/shm` 挂载 | `shm_size: 2gb` |

## 未修改的文件

以下文件在 ROS1/ROS2 间完全通用，无需修改：
- `src/mowen_gazebo/urdf/mowen.urdf`
- `src/mowen_gazebo/worlds/empty_world.world`
- `src/mowen_gazebo/worlds/mowen_world.world`
- `src/mowen_cartographer/config/mowen_lds_2d.lua`
- `src/mowen_gazebo/models/mowen_common/*` (所有 STL mesh)
- `map.yaml` / `map.pgm`

## 已知限制

1. **无 Behavior Tree**: ROS1 `move_base` 使用硬编码状态机，不支持 Nav2 的 Behavior Tree
2. **无 Velocity Smoother**: Nav2 的 velocity_smoother 在 ROS1 中无直接等价组件
3. **无 Lifecycle 管理**: ROS1 节点直接启动，无 configure/activate 生命周期
4. **Python 2.7**: 如需要写 Python 脚本需兼容 Python 2.7（当前项目无自定义 Python 代码）
5. **Cartographer 已停止维护**: Google 已放弃 Cartographer，apt 包可能在未来不可用
