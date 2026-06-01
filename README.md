# Mowen - Mecanum 轮机器人 ROS1 Melodic 仿真

## 环境要求

- **Docker** + **docker compose** (v2)
- **NVIDIA GPU** + `nvidia-container-toolkit`（可选，无 GPU 可用软渲染）
- **X11**（Linux）或 **XQuartz**（macOS）

## 快速启动

### 1. 启动容器

```bash
cd docker
./container.sh start    # 首次运行会构建镜像，约 20-30 分钟
./container.sh enter    # 进入容器
```

### 2. 构建项目

```bash
catkin_make
source devel/setup.bash
```

### 3. 启动仿真

```bash
roslaunch mowen_gazebo mowen_world.launch
```

### 4. 启动 SLAM + RViz（新终端）

```bash
./container.sh enter
source devel/setup.bash
roslaunch mowen_cartographer cartographer.launch use_sim_time:=true
```

### 5. 键盘控制（新终端）

```bash
./container.sh enter
source devel/setup.bash
rosrun teleop_twist_keyboard teleop_twist_keyboard.py
```

控制键：`i` 前进 `,` 后退 `j` 左转 `l` 右转 `u` 左前 `o` 右前 `k` 停止

### 6. 保存地图

```bash
rosservice call /finish_trajectory 0
rosrun map_server map_saver -f ~/mowen_map
```

### 7. 启动导航

```bash
roslaunch mowen_navigation navigation.launch map_file:=/root/mowen_map.yaml
```

## 无 GPU 软渲染

编辑 `docker/docker-compose.yml`，取消下面两行注释：

```yaml
# - LIBGL_ALWAYS_SOFTWARE=1
# - MESA_GL_VERSION_OVERRIDE=3.3
```

## 其他命令

```bash
./container.sh stop     # 停止容器
./container.sh start    # 重新启动
./container.sh enter    # 进入容器
```

## 海外网络

编辑 `docker/Dockerfile`，删除第 8-9 行的 `sed` 换源命令，使用默认 Ubuntu 源。
