# CLAUDE.md

## 项目信息

- **项目**: Mowen - Mecanum轮移动机器人仿真
- **ROS 版本**: ROS1 Melodic (Ubuntu 18.04 Docker 容器)
- **Gazebo**: Gazebo 9 Classic
- **构建工具**: catkin_make (非 colcon)
- **环境 source**: `source devel/setup.bash`

## SDF/URDF 修改规则

**任何对 SDF 或 URDF 文件的修改，必须通过 Python 脚本精准完成，禁止手动编辑 XML。**

原因：
- `model.sdf` 由 `gz sdf -p` 自动生成，结构复杂，手动编辑容易引入 XML 格式错误（缩进不一致、标签未闭合、属性格式错误等）
- 惯性参数必须用子元素格式（`<inertia><ixx>value</ixx></inertia>`）而非属性格式
- 多处重复结构（如4个轮子碰撞体）需保持一致

要求：
1. 脚本放在 `scripts/` 目录下，命名清晰（如 `fix_sdf_mass.py`, `fix_wheel_collision.py`）
2. 脚本使用 `xml.etree.ElementTree` 或精确的正则替换
3. 修改前先备份或通过 git 确认当前状态
4. 脚本执行后打印修改摘要（改了什么、改了多少处）

## ROS1 注意事项

- **绝不可使用** `ros2` 命令，只能使用 `rosrun`, `roslaunch`, `rostopic`, `rosservice`, `rosparam`
- Launch 文件为 XML 格式 (.launch)，**不可写 Python launch**
- 参数 YAML 格式: 无 `ros__parameters` 嵌套键
- 无 `ROS_DOMAIN_ID`（ROS1 用 TCP 发现），无 lifecycle 概念
- `nav2_*` 包不存在，使用 `move_base` + `amcl` + `map_server`

## Docker 相关

```bash
cd docker && ./container.sh start   # 启动容器
cd docker && ./container.sh enter   # 进入容器
cd /root/mowen_ws && catkin_make    # 构建项目
```
