# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Mowen is a **ROS2 Humble** project for a mecanum-wheel robot: Gazebo simulation, Cartographer SLAM mapping, and Nav2 autonomous navigation. The robot model has a 360° LiDAR, IMU, and camera (visual only, no plugin).

**Everything runs inside a Docker container** (`robotis/turtlebot3:humble-latest`) because the host runs ROS2 Jazzy + Gazebo Harmonic, which is incompatible with the Gazebo 11 Classic used by turtlebot3's ecosystem.

The full tutorial is [docs/Mowen_Gazebo仿真完整教程.md](docs/Mowen_Gazebo仿真完整教程.md).

## Architecture — 4 ROS2 packages

| Package | Purpose | Key files |
|---|---|---|
| `mowen_gazebo` | Gazebo simulation with robot model | `models/mowen/model.sdf` (the most critical file — defines robot physics, sensors, plugins) |
| `mowen_cartographer` | SLAM mapping (Cartographer) | `config/mowen_lds_2d.lua` (algorithm parameters) |
| `mowen_navigation2` | Nav2 autonomous navigation | `param/mowen.yaml` (all Nav2 params: AMCL, DWA, costmaps, planners, behaviors) |
| `mowen` | Metapackage (aggregates the above) | `package.xml` + `CMakeLists.txt` only |

**Data flow:** Gazebo publishes `/scan`, `/odom`, `/imu`, `/tf` → Cartographer builds `/map` → Nav2 uses `/map` + AMCL for localization + DWA local planner for navigation → sends `/cmd_vel` back to Gazebo.

Key design decisions:
- Uses `libgazebo_ros_planar_move.so` for mecanum drive (not diff drive)
- AMCL uses `nav2_amcl::OmniMotionModel` (mecanum-specific)
- DWA local planner enables lateral velocity sampling (`vy_samples: 10`) for mecanum side movement
- Camera link has no Gazebo plugin (visual only, saves performance)

## Build & Run (everything in Docker container)

```bash
# Container management (from docker/)
./container.sh start    # Start container
./container.sh enter    # Enter container shell
./container.sh stop     # Stop container

# Inside container — build
cd /root/mowen_ws
colcon build --symlink-install
source install/setup.bash

# SLAM mapping (3 terminals, all: docker exec -it mowen_sim bash)
# Terminal 1: ros2 launch mowen_gazebo empty_world.launch.py
# Terminal 2: ros2 launch mowen_cartographer cartographer.launch.py use_sim_time:=True
# Terminal 3: ros2 run teleop_twist_keyboard teleop_twist_keyboard

# Save map (after SLAM)
ros2 run nav2_map_server map_saver_cli -f ~/mowen_map

# Autonomous navigation
# Terminal 1: ros2 launch mowen_gazebo empty_world.launch.py
# Terminal 2: ros2 launch mowen_navigation2 navigation2.launch.py use_sim_time:=True map:=/root/mowen_map.yaml
```

## Quick diagnostics (inside container)

```bash
ros2 topic list                        # All active topics
ros2 topic echo /cmd_vel               # Check if robot receives commands
ros2 topic echo /scan --once           # Verify LiDAR data
ros2 run tf2_tools view_frames         # TF tree: map → odom → base_footprint → base_link → sensors
killall -9 gzserver gzclient           # Clean up stuck Gazebo processes
echo $GAZEBO_MODEL_PATH                # Must include .../install/mowen_gazebo/share/mowen_gazebo/models
echo $LD_LIBRARY_PATH                  # Must include /opt/ros/humble/lib
```

## Critical: URDF to SDF conversion

The `model.sdf` file was generated using Gazebo's official conversion tool from the reference URDF:

```bash
# Convert reference URDF to SDF (host machine)
gz sdf -p /path/to/reference.urdf > model.sdf

# Fix mesh paths
sed -i 's/model://mowen2/model://mowen_common/g' model.sdf
sed -i 's/mowen2/mowen/g' model.sdf
```

**Do NOT manually edit coordinates** in the SDF. Always regenerate from the reference URDF if coordinate changes are needed.

## Key references

- Turtlebot3 reference project: `/home/qc/resource/code/CL/turtlebot3/` (fully working ROS2 Humble sim+mapping+nav)
- Original Mowen2 URDF/STL models: `/home/qc/resource/code/ros/2_Gazebo_simulation/src/robot_description/mowen2/`
- Real robot ROS1 workspace: `/home/qc/resource/code/ros/newznzc_ws/`
- Docker image: `robotis/turtlebot3:humble-latest` (pre-loaded with ROS2 Humble, Cartographer, Nav2, Gazebo 11)
