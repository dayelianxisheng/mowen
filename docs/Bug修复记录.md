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

## 当前模型物理参数

| 参数 | 值 | 位置 |
|---|---|---|
| mu（前进摩擦） | 0.3 | model.sdf 轮子碰撞体 |
| mu2（横向摩擦） | 0.02 | model.sdf 轮子碰撞体 |
| kp（接触刚度） | 1e5 | model.sdf 轮子碰撞体 |
| kd（接触阻尼） | 10 | model.sdf 轮子碰撞体 |
| damping（关节阻尼） | 0.5 | model.sdf 轮子关节 |
