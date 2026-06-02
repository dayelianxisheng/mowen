# Mowen - Mecanum 轮机器人 ROS1 Melodic 仿真

## 环境要求

- **Docker** + **docker compose** (v2)
- **NVIDIA GPU** + `nvidia-container-toolkit`（可选，无 GPU 可用软渲染）
- **X11**（Linux）或 **XQuartz**（macOS）

## 快速启动

### 1. 启动容器

```bash
cd docker
./container.sh start    # 首次运行会构建镜像
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

### 4. 启动 SLAM 建图（容器内新终端）

```bash
docker exec -it mowen_sim bash
source /opt/ros/melodic/setup.bash
source /root/mowen_ws/devel/setup.bash
roslaunch mowen_cartographer cartographer.launch use_sim_time:=true
```

### 5. 键盘控制（容器内新终端）

```bash
docker exec -it mowen_sim bash
source /opt/ros/melodic/setup.bash
rosrun teleop_twist_keyboard teleop_twist_keyboard.py
```

控制键：`u` 左前 `i` 前进 `o` 右前 `j` 左转 `k` 停止 `l` 右转 `m` 左后 `,` 后退 `.` 右后

### 6. 保存地图

```bash
rosrun map_server map_saver -f ~/mowen_ws/src/mowen_navigation/map/map
```

### 7. 导航（容器内新终端，Gazebo 需在运行中）

```bash
docker exec -it mowen_sim bash
source /opt/ros/melodic/setup.bash
source /root/mowen_ws/devel/setup.bash
roslaunch mowen_navigation navigation.launch
```

在 RViz 中：**2D Pose Estimate** → 点初始位姿 → **2D Nav Goal** → 点目标位置

## 无 GPU 软渲染

编辑 `docker/docker-compose.yml`，取消下面两行注释：

```yaml
# - LIBGL_ALWAYS_SOFTWARE=1
# - MESA_GL_VERSION_OVERRIDE=3.3
```

## 常用命令

```bash
# 容器管理
docker exec -it mowen_sim bash      # 进入容器
./container.sh stop                 # 停止容器
./container.sh start                # 启动容器

# 清理残留进程
cd /root/mowen_ws && bash scripts/kill_ros.sh
```

## 海外网络

编辑 `docker/Dockerfile`，删除第 8-9 行的 `sed` 换源命令。
