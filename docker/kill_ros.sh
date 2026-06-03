#!/bin/bash
# 杀掉 Gazebo / RViz / ROS 及相关僵尸进程
# container.sh kill 会先执行这个脚本，确保端口和进程都清理干净

echo "=== Killing ROS/Gazebo/RViz processes ==="

# 杀掉容器内所有 ROS 相关进程
docker exec mowen_sim bash -c '
  kill -9 $(ps aux | grep -E "gzserver|gzclient|spawn_entity|rviz2|robot_state_publisher|ros2 launch|cartographer|radar_sim|radar_camera|fusion_visual" | grep -v grep | awk "{print \$2}") 2>/dev/null
' 2>/dev/null

# 杀掉宿主机上残留的 Gazebo/RViz 进程（network_mode=host 导致）
pkill -9 -f "gzserver" 2>/dev/null
pkill -9 -f "gzclient" 2>/dev/null
pkill -9 -f "rviz2" 2>/dev/null
pkill -9 -f "spawn_entity" 2>/dev/null
pkill -9 -f "robot_state_publisher" 2>/dev/null

# 强制释放 Gazebo 端口 11345
fuser -k 11345/tcp 2>/dev/null

sleep 1

# 检查清理结果
REMAINING=$(ss -tlnp 2>/dev/null | grep -c 11345)
if [ "$REMAINING" -eq 0 ]; then
    echo "  All clean. Gazebo port 11345 freed."
else
    echo "  WARNING: Port 11345 still in use!"
fi

echo "  Done."
