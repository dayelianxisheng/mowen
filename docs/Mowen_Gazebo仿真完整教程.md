# Mowen Mecanum轮机器人 — Gazebo仿真完整教程

## 目录

1. [项目概述](#1-项目概述)
2. [关键技术决策](#2-关键技术决策)
3. [Docker环境搭建](#3-docker环境搭建)
4. [Gazebo仿真包(mowen_gazebo)](#4-gazebo仿真包mowen_gazebo)
5. [启动仿真](#5-启动仿真)
6. [常见问题排查](#6-常见问题排查)
7. [后续扩展](#7-后续扩展)

---

## 1. 项目概述

Mowen是一个基于Mecanum轮的ROS2 Humble机器人项目，支持：
- **Gazebo 11 Classic** 仿真环境
- **Cartographer** SLAM建图
- **Nav2** 自主导航
- **360° LiDAR + IMU + Camera** 传感器

### 1.1 为什么用Docker

**问题背景**：宿主机运行ROS2 Jazzy + Gazebo Harmonic，但Turtlebot3生态依赖ROS2 Humble + Gazebo 11 Classic。

| 特性 | Humble (Docker) | Jazzy (宿主机) |
|------|------------------|-----------------|
| Gazebo版本 | Gazebo 11 Classic | Gazebo Harmonic |
| ROS包兼容性 | ✅ turtlebot3生态 | ❌ 完全不兼容 |
| 开发效率 | 直接使用现成方案 | 需要全部重写 |

**结论**：Docker容器是���一可行路径。

### 1.2 参考资源

| 资源 | 路径 | 用途 |
|------|------|------|
| **Mowen2原始模型** | `/home/qc/resource/code/ros/edu/2_Gazebo_simulation/src/robot_description/mowen2/` | URDF + STL网格 |
| **Turtlebot3参考** | `/home/qc/resource/code/CL/turtlebot3/` | ROS2 Humble完整方案 |
| **Docker镜像** | `robotis/turtlebot3:humble-latest` | 基础环境 |

---

## 2. 关键技术决策

### 2.1 URDF vs SDF

**关键发现**：参考项目是ROS1（URDF），但我们需要ROS2（SDF）。

**错误做法**：手动从URDF改写SDF
- ❌ 坐标变换容易出错
- ❌ RPY旋转处理困难
- ❌ 调试周期长

**正确做法**：使用Gazebo官方工具转换
```bash
# 第1步：展开xacro（如果有）
xacro robot.xacro > robot_expanded.urdf

# 第2步：URDF → SDF转换
gz sdf -p robot.urdf > robot.sdf
```

**转换优势**：
- ✅ 坐标系统完全保留
- ✅ 相对引用（`relative_to`）自动计算
- ✅ 零调试时间

### 2.2 模型结构

转换后的SDF特点：
```xml
<model name='mowen'>
  <link name='base_footprint'>        <!-- 虚拟基座，固定在地面 -->
    <!-- base_link + 传感器合并到这里（fixed joints被优化） -->
  </link>
  
  <joint name='front_left_joint' type='revolute'>  <!-- 轮子关节保持独立 -->
    <pose relative_to='base_footprint'>0.127 0.145 0.048 0 0 0</pose>
  </joint>
  <link name='front_left_wheel'/>
  
  <!-- 其他3个轮子同理 -->
</model>
```

### 2.3 插件配置

ROS2 Gazebo需要两类插件：

**驱动插件**：`libgazebo_ros_planar_move.so`
```xml
<plugin filename='libgazebo_ros_planar_move.so'>
  <robot_base_frame>base_footprint</robot_base_frame>
  <publish_odom_tf>true</publish_odom_tf>
</plugin>
```

**关节状态发布**：`libgazebo_ros_joint_state_publisher.so`
```xml
<plugin filename='libgazebo_ros_joint_state_publisher.so'>
  <joint_name>front_left_joint</joint_name>
  <!-- 其他3个轮子 -->
</plugin>
```

---

## 3. Docker环境搭建

### 3.1 项目结构

```
mowen/
├── docker/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── container.sh
└── src/
    └── mowen_gazebo/        # 仿真包
        ├── CMakeLists.txt
        ├── package.xml
        ├── launch/          # 启动文件
        ├── models/          # Gazebo模型
        └── worlds/          # 仿真世界
```

### 3.2 Dockerfile

```dockerfile
FROM robotis/turtlebot3:humble-latest

# 关键环境变量
ENV LD_LIBRARY_PATH=/opt/ros/humble/lib:${LD_LIBRARY_PATH}
ENV MOWEN_WS=/root/mowen_ws
RUN mkdir -p ${MOWEN_WS}/src

# 自动配置环境
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc && \
    echo "source \${MOWEN_WS}/install/setup.bash" >> ~/.bashrc && \
    echo "export ROS_DOMAIN_ID=30" >> ~/.bashrc && \
    echo "export GAZEBO_MODEL_PATH=\${GAZEBO_MODEL_PATH}:\${MOWEN_WS}/install/mowen_gazebo/share/mowen_gazebo/models" >> ~/.bashrc && \
    echo 'alias cb="colcon build --symlink-install"' >> ~/.bashrc

WORKDIR ${MOWEN_WS}
CMD ["bash"]
```

**关键点**：
- `LD_LIBRARY_PATH` 必须设置，否则gzserver找不到插件
- `GAZEBO_MODEL_PATH` 指向models目录
- `ROS_DOMAIN_ID=30` 隔离DDS通信

### 3.3 docker-compose.yml

```yaml
services:
  mowen:
    container_name: mowen_sim
    build:
      context: .
      dockerfile: Dockerfile
    tty: true
    restart: unless-stopped
    cap_add:
      - SYS_NICE
    network_mode: host        # ROS2 DDS需要
    ipc: host
    pid: host
    environment:
      - DISPLAY=${DISPLAY}
      - QT_X11_NO_MITSHM=1
    volumes:
      - /dev:/dev
      - /dev/shm:/dev/shm
      - /run/udev:/run/udev
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
      - ../src:/root/mowen_ws/src    # 源码挂载
    privileged: true
```

### 3.4 容器管理命令

```bash
# 启动容器
cd docker
./container.sh start

# 进入容器
./container.sh enter

# 停止容器
./container.sh stop
```

---

## 4. Gazebo仿真包(mowen_gazebo)

### 4.1 package.xml

```xml
<?xml-model href="http://download.ros.org/schema/package_format3.xsd"?>
<package format="3">
  <name>mowen_gazebo</name>
  <version>1.0.0</version>
  <description>Gazebo simulation for Mowen mecanum robot</description>
  
  <buildtool_depend>ament_cmake</buildtool_depend>
  
  <depend>gazebo_ros_pkgs</depend>
  <depend>geometry_msgs</depend>
  <depend>rclcpp</depend>
  <depend>sensor_msgs</depend>
  <depend>tf2</depend>
  
  <export>
    <build_type>ament_cmake</build_type>
    <gazebo_ros gazebo_model_path="${prefix}/models"/>
  </export>
</package>
```

### 4.2 CMakeLists.txt

```cmake
cmake_minimum_required(VERSION 3.5)
project(mowen_gazebo)

find_package(ament_cmake REQUIRED)

install(DIRECTORY launch models worlds
  DESTINATION share/${PROJECT_NAME})

ament_package()
```

### 4.3 模型文件结构

```
models/
├── mowen/
│   ├── model.sdf          # 主模型定义（从URDF转换）
│   └── model.config       # 模型元数据
└── mowen_common/
    └── meshes/
        ├── mecanum/        # 底盘+轮子网格
        └── sensor/         # 传感器网格
```

**重要**：`model.sdf` 必须通过 `gz sdf -p` 从参考URDF转换，不要手动编写。

### 4.4 Launch文件

#### empty_world.launch.py

```python
import os

# 确保ROS库路径
os.environ.setdefault('LD_LIBRARY_PATH', '')
if '/opt/ros/humble/lib' not in os.environ['LD_LIBRARY_PATH']:
    os.environ['LD_LIBRARY_PATH'] = '/opt/ros/humble/lib:' + os.environ['LD_LIBRARY_PATH']

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource

def generate_launch_description():
    pkg_mowen = get_package_share_directory('mowen_gazebo')
    pkg_gazebo_ros = get_package_share_directory('gazebo_ros')
    world = os.path.join(pkg_mowen, 'worlds', 'empty_world.world')

    return LaunchDescription([
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo_ros, 'launch', 'gzserver.launch.py')),
            launch_arguments={'world': world}.items()),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_gazebo_ros, 'launch', 'gzclient.launch.py'))),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_mowen, 'launch', 'robot_state_publisher.launch.py'))),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(pkg_mowen, 'launch', 'spawn_mowen.launch.py'))),
    ])
```

**关键点**：
- 必须在导入前设置 `LD_LIBRARY_PATH`
- 使用 `IncludeLaunchDescription` 复用Gazebo官方launch

---

## 5. 启动仿真

### 5.1 首次构建

```bash
# 在容器内
cd /root/mowen_ws
colcon build --symlink-install
source install/setup.bash
```

### 5.2 启动仿真

```bash
# 方法1：使用launch文件（推荐）
ros2 launch mowen_gazebo empty_world.launch.py

# 方法2：分步启动（调试用）
# 终端1
gzserver worlds/empty_world.world -s libgazebo_ros_init.so -s libgazebo_ros_factory.so

# 终端2
gzclient

# 终端3
ros2 run gazebo_ros spawn_entity.py -entity mowen -file models/mowen/model.sdf
```

### 5.3 验证检查

```bash
# 检查话题
ros2 topic list

# 应该看到：
# /scan       (LiDAR)
# /imu        (IMU)
# /odom       (里程计)
# /cmd_vel    (速度控制)
# /joint_states (关节状态)
# /tf, /tf_static (坐标变换)

# 检查TF树
ros2 run tf2_tools view_frames

# 应该看到：
# map → odom → base_footprint → base_link → {wheels, sensors}
```

### 5.4 遥控测试

```bash
# 安装键盘遥控（如果没有）
apt-get install ros-humble-teleop-twist-keyboard

# 启动遥控
ros2 run teleop_twist_keyboard teleop_twist_keyboard

# 在Gazebo中观察机器人移动
```

---

## 6. 常见问题排查

### 6.1 Gazebo黑屏

**症状**：gzclient启动但窗口全黑

**原因**：X11转发问题

**解决**：
```bash
# 检查DISPLAY
echo $DISPLAY

# 检查X11套接字
ls /tmp/.X11-unix/

# 在宿主机允许X11连接
xhost +local:
```

### 6.2 插件加载失败

**症状**：
```
gzserver: error while loading shared libraries: 
libgazebo_ros_init.so: cannot open shared object file
```

**原因**：`LD_LIBRARY_PATH` 未设置

**解决**：
```bash
export LD_LIBRARY_PATH=/opt/ros/humble/lib:$LD_LIBRARY_PATH
gzserver ...
```

或在launch文件中添加（见4.4节）

### 6.3 模型位置不对

**症状**：机器人沉到地下或悬浮过高

**原因**：手动修改SDF坐标出错

**解决**：
1. 使用 `gz sdf -p` 重新转换参考URDF
2. 不要手动调整 `<pose>` 值
3. 检查 `robot_base_frame` 是否为 `base_footprint`

### 6.4 话题不出现

**症状**：只能看到 `/clock` 和 `/rosout`，没有 `/scan`、`/odom`

**原因**：模型spawn失败或插件未加载

**解决**：
```bash
# 检查spawn服务
ros2 service list | grep spawn

# 查看gzserver日志
# 在启动gzserver的终端查看错误信息

# 检查模型文件
cat /root/mowen_ws/install/mowen_gazebo/share/mowen_gazebo/models/mowen/model.sdf | grep plugin
```

### 6.5 容器内无gazebo命令

**症状**：`gzserver: command not found`

**原因**：gazebo11未安装

**解决**：
```bash
apt-get update
apt-get install ros-humble-gazebo-ros-pkgs
```

### 6.6 进程僵死

**症状**：重新启动后gzserver/gzclient无响应

**原因**：旧进程未完全清理

**解决**：
```bash
# 方法1：容器内
killall -9 gzserver gzclient

# 方法2：宿主机
docker exec mowen_sim killall -9 gzserver gzclient

# 方法3：重启容器
docker restart mowen_sim
```

---

## 7. 后续扩展

### 7.1 添加Cartographer SLAM

创建 `mowen_cartographer` 包：
- 配置文件：`config/mowen_lds_2d.lua`
- Launch文件：`cartographer.launch.py`
- RViz配置：`rviz/mowen_cartographer.rviz`

### 7.2 添加Nav2导航

创建 `mowen_navigation2` 包：
- 配置文件：`param/mowen.yaml`（AMCL+DWA+costmaps）
- Launch文件：`navigation2.launch.py`
- 地图文件：`maps/mowen_map.yaml`

### 7.3 创建元包

创建 `mowen` 元包聚合所有功能：

```xml
<package format="3">
  <name>mowen</name>
  <depend>mowen_gazebo</depend>
  <depend>mowen_cartographer</depend>
  <depend>mowen_navigation2</depend>
  <exec_depend>ros2launch</exec_depend>
</package>
```

---

## 附录：完整的URDF→SDF转换流程

```bash
# 1. 进入参考项目目录
cd /home/qc/resource/code/ros/edu/2_Gazebo_simulation/src/robot_description/mowen2

# 2. 转换URDF→SDF
gz sdf -p urdf/mowen2.urdf > /tmp/mowen_converted.sdf

# 3. 复制到项目
cp /tmp/mowen_converted.sdf /home/qc/resource/code/ros2/mowen/src/mowen_gazebo/models/mowen/model.sdf

# 4. 批量修改路径
cd /home/qc/resource/code/ros2/mowen/src/mowen_gazebo/models/mowen
sed -i 's/mowen2/mowen/g' model.sdf
sed -i 's|model://mowen/|model://mowen_common/|g' model.sdf

# 5. 添加ROS2插件（在</model>前）
# 见2.3节

# 6. 修改model.config版本号
# <sdf version="1.11">model.sdf</sdf>
```

---

**文档版本**：v2.0  
**最后更新**：2026-05-20  
**维护者**：Mowen项目组
