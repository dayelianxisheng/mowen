# Mowen Bug 修复记录

> 修复日期：2026-05-21 ~ 2026-05-22

## Bug 1: 键盘控制不了机器人

**现象**: teleop_twist_keyboard 发送 /cmd_vel，机器人不响应。

**根因**: ROS_DOMAIN_ID 不匹配。
- `ros2 launch` 在非交互 shell 运行，.bashrc 未加载 → domain 默认 0
- teleop 在交互终端运行，.bashrc 加载 `ROS_DOMAIN_ID=30` → domain 30
- 两个进程在不同 ROS2 域，互相不可见。

**修复**:
- `docker-compose.yml` environment 加 `ROS_DOMAIN_ID=30`（容器环境变量，所有进程生效）
- `docker/Dockerfile` 中 .bashrc 的 `ROS_DOMAIN_ID=30` 作为补充

---

## Bug 2: GPU 渲染报错 libGL/failed to load driver: nouveau

**现象**: 启动 Gazebo 报 `libGL error: failed to load driver: nouveau`，gzserver 崩溃。

**根因**: 宿主机 NVIDIA RTX 5070 Ti 用闭源驱动，容器内没有 NVIDIA 驱动，回退到开源 nouveau，nouveau 不支持新显卡。

**修复**:
- 宿主机安装 `nvidia-container-toolkit`
- `docker-compose.yml` 加 `runtime: nvidia`

---

## Bug 3: Gazebo 模型塌陷（所有零件堆一起）

**现象**: 修改 model.sdf 后 Gazebo 中机器人所有零件堆在原点。

**根因**: 多次手动 Edit model.sdf 导致缩进/标签错乱，SDF XML 解析失败，所有 mesh 位置归零。

**修复**: 用 Python 脚本精确替换（插入 surface/friction 到碰撞体、damping 到关节），避免手动编辑错误。

---

## Bug 4: 移动一颤一颤、侧移不灵敏、停止后滑

**现象**:
- 移动时机器人颤动
- 向左/右平移几乎不动
- 停止后机体向后滑动

**根因**: model.sdf 缺少关键物理参数：
- 轮子碰撞体无 `mu2`（横向摩擦系数）→ 默认值太高，mecanum 滚子无法侧滑
- 轮子关节无 `damping` → 停止时轮子惯性带动后滑
- 默认接触刚度使滚子凹凸面产生颤动

**修复** (`src/mowen_gazebo/models/mowen/model.sdf`):
- 4 个轮子碰撞体加 `surface/friction`: `mu=0.3, mu2=0.02`
- 4 个轮子碰撞体加 `contact`: `kp=1e5, kd=10`
- 4 个轮子关节 dynamics 加 `damping=0.5`

---

## Bug 5: RViz 中轮子躺平（不是竖直的）

**现象**: RViz 中机器人轮子水平放置，Gazebo 中正常。

**根因**: `urdf/mowen.urdf` 中 4 个轮子关节的 `rpy` 值错误（`1.5708` 即 90°翻转），而 SDF 模型中关节无旋转。URDF 与 SDF 不一致导致 RViz 渲染错误。

**修复** (`src/mowen_gazebo/urdf/mowen.urdf`):
- 4 个轮子关节 `rpy` 从 `1.5708 0 0` / `-1.5708 0 3.1416` 改为 `0 0 0`

---

## Bug 6: /spawn_entity 服务不可用（30秒超时）

**现象**: `ros2 launch mowen_gazebo empty_world.launch.py` 后 spawn_entity 报错 `Service /spawn_entity unavailable`。

**根因**: `gazebo_ros` 的 `GazeboRosPaths.get_paths()` 遍历所有包的 `package.xml` 的 `<gazebo_ros>` export 标签来构建 `GAZEBO_PLUGIN_PATH`，但核心 `gazebo_ros` 包自己没写这些标签，函数返回空值。`gzserver.launch.py` 用空值覆写了环境变量，导致 `libgazebo_ros_factory.so` 找不到。

**修复**:
- `src/mowen_gazebo/launch/empty_world.launch.py` 重写，不再 Include `gzserver.launch.py`/`gzclient.launch.py`，改用 `ExecuteProcess` 直接运行 gzserver/gzclient，硬编码正确的 `GAZEBO_PLUGIN_PATH`（含 `/opt/ros/humble/lib`）
- `docker/Dockerfile` 加 `source /usr/share/gazebo/setup.sh` 确保系统 Gazebo 路径

---

## Bug 7: 轮子嵌入地面

**现象**: Gazebo 中轮子有一小部分嵌入地面以下。

**根因**: 轮子碰撞圆柱体尺寸远小于实际 STL 轮子。
- 圆柱体 radius=0.033m，实际 STL 半径 ~0.0485m
- 圆柱体 length=0.020m，实际 STL 宽度 ~0.0506m
碰撞体太小→机器人下沉到 base_footprint 碰撞体着地→视觉网格穿透地面。

**修复** (`scripts/fix_sdf.py`, `scripts/fix_wheel_collision.py`, `model.sdf`):
- 4 个轮子碰撞圆柱体 `radius` 从 0.033→0.0485
- 4 个轮子碰撞圆柱体 `length` 从 0.020→0.0506

---

## Bug 8: Cartographer 不建图（submap_list 始终为空）

**现象**: Cartographer 运行后 `/submap_list` 显示 `submap: []`，`/map` 无数据，RViz 显示 "no map received"。

**根因**: `mowen_lds_2d.lua` 中 `TRAJECTORY_BUILDER_2D.use_imu_data = true`，但机器人没有 IMU 传感器。Cartographer 的 ordered_multi_queue 一直等待 IMU 数据 `Queue waiting for data: (0, imu)`，导致所有传感器数据（scan、odom）都无法处理，子图永远不会创建。

**修复** (`src/mowen_cartographer/config/mowen_lds_2d.lua`):
- `TRAJECTORY_BUILDER_2D.use_imu_data` 从 `true` 改为 `false`

---

## Bug 9: 转弯/停车时建图出现黑斑（已扫白的区域变黑）

**现象**: 小车停止后前进，停止点变黑；先停再转向再前进，该点更黑。

**根因**: 两个原因叠加：
1. 激光 `min_range = 0.12` 太小，激光扫到了机器人自身（轮子、车身边缘约 0.12~0.2m），cartographer 把自扫点当真障碍物标记
2. 之前添加的 `ceres_scan_matcher.rotation_weight = 60` 过高，导致转弯时过分信任里程计，里程计微小偏差无法被纠正，激光点云投影错位

**修复**:
- `min_range` 从 0.12 改为 **0.25**（过滤自扫点）
- 删除 `ceres_scan_matcher.translation_weight`、`rotation_weight`
- 删除 `motion_filter.max_distance_meters`
- 删除 `submaps.num_range_data`
- `motion_filter.max_angle_radians` 恢复为 `math.rad(0.1)`（与 turtlebot3 一致）

---

## Bug 10: RViz 中 /map 话题有数据但界面不显示

**现象**: `ros2 topic echo /map` 有数据，但 RViz 中 Map display 不渲染。

**根因**: 
1. `nav2_bringup` 的 lifecycle manager 可能创建多个 map_server 实例
2. RViz Map display 的 Durability Policy 默认 `Volatile`，但 map_server 发布的是 `Transient Local`，不匹配时收不到
3. `ros2 topic hz /map` 报 `RTPS_READER_HISTORY Error`，因为 map 消息较大（174×132 = 22KB），默认 history payload 只有 11 字节

**修复**:
- RViz 中 Map display → Topic → Durability Policy 改为 `Transient Local`
- 多个 map_server 实例不影响功能（所有实例都发布同一份地图，latched topic）

---

## 当前模型物理参数

| 参数 | 值 | 位置 |
|---|---|---|
| mu（前进摩擦） | 0.3 | model.sdf 轮子碰撞体 |
| mu2（横向摩擦） | 0.02 | model.sdf 轮子碰撞体 |
| kp（接触刚度） | 1e5 | model.sdf 轮子碰撞体 |
| kd（接触阻尼） | 10 | model.sdf 轮子碰撞体 |
| damping（关节阻尼） | 0.5 | model.sdf 轮子关节 |

---

## Bug 11: 导航效果极差（一卡一卡、定位漂移）

**现象**: 
- 机器人移动一卡一卡，不连续
- 走着走着 AMCL 定位漂移，雷达点和地图墙壁对不上
- RViz 中激光扫描与地图错位

**根因**: 多个问题叠加：

1. **relay 与 velocity_smoother 冲突**（主因）
   - `navigation.launch.py` 中有 relay 节点 `/cmd_vel_nav` → `/cmd_vel`
   - `velocity_smoother` 也发布 `cmd_vel_smoothed` → `/cmd_vel`
   - 两个发布者同时往 `/cmd_vel` 发，机器人收到交替的原始和平滑指令，导致抖动

2. **AMCL motion model 错误**（定位漂移主因）
   - 机器人是 mecanum 全向轮 + planar_move 插件（可侧移）
   - 但 AMCL 用的是 `DifferentialMotionModel`（差速模型）
   - 差速模型不理解侧向移动，机器人横移时 AMCL 认为是噪声，粒子发散，定位漂移

3. **behavior_server 参数过期**
   - 旧格式 `local_costmap_topic`/`local_footprint_topic` → 新格式 `costmap_topic`/`footprint_topic`
   - `global_frame: map` → `odom`
   - `transform_tolerance: 1.0` → `0.1`

4. **bt_navigator rclcpp_node 命名不对**
   - 旧: `bt_navigator_rclcpp_node`
   - 新: `bt_navigator_navigate_through_poses_rclcpp_node` + `bt_navigator_navigate_to_pose_rclcpp_node`

5. **缺少 smoother_server 配置**
   - navigation_launch.py 加载了 smoother_server 节点但没有参数

6. **velocity_smoother 多余参数**
   - `enable_stamped_cmd_vel: true` 在 Humble 默认配置中不存在

**修复**:
- `navigation.launch.py`: 删除 relay 节点
- `nav2_params.yaml`:
  - AMCL: `DifferentialMotionModel` → `OmniMotionModel`（注意不是 `OmniDirectionalMotionModel`，那个不存在）
  - behavior_server: 改用 Humble 参数名，`global_frame: odom`，`transform_tolerance: 0.1`
  - bt_navigator: rclcpp_node 拆成两个
  - controller_server: `transform_tolerance: 0.2`
  - velocity_smoother: 删除 `enable_stamped_cmd_vel`
  - 新增 `smoother_server` 配置段

---

## Bug 12: 容器重启后 Gazebo 丢失

**现象**: `docker compose down && up` 后容器内没有 Gazebo。

**根因**: Docker 镜像是 `robotis/turtlebot3:humble-latest`，不含 Gazebo。旧容器内手动安装过，重建容器后丢失。

**修复**: `apt-get install -y ros-humble-gazebo-ros-pkgs`（安装 gazebo + gazebo_ros 插件）

---

## Bug 13: 轮子不转（未解决）

**现象**: 机器人可以移动，但 4 个轮子视觉上没有转动。

**状态**: 待排查，可能原因：
- SDF 中轮子 joint 的 axis 方向不对
- `libgazebo_ros_planar_move.so` 插件不驱动关节旋转，只移动整体（关节旋转依赖 `libgazebo_ros_joint_state_publisher.so`）
- joint state publisher 与模拟运动不同步
