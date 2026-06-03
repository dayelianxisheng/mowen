#!/usr/bin/env python3
"""Generate a mapping-friendly world with rooms, corridors, and obstacles."""
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORLD_PATH = os.path.join(PROJECT_ROOT, 'src/mowen_gazebo/worlds/mowen_world.world')

# Wall template: a static box
def wall(name, pose, size):
    """pose: [x y z roll pitch yaw], size: [x y z]"""
    return f'''    <model name="{name}">
      <static>true</static>
      <pose>{pose[0]} {pose[1]} {pose[2]} {pose[3]} {pose[4]} {pose[5]}</pose>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>{size[0]} {size[1]} {size[2]}</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>{size[0]} {size[1]} {size[2]}</size></box></geometry>
          <material><ambient>0.7 0.7 0.7 1</ambient><diffuse>0.7 0.7 0.7 1</diffuse></material>
        </visual>
      </link>
    </model>'''

elements = []

# ---- Outer walls: 8x6m arena (x=[-4,4], y=[-3,3]) ----
elements.append(wall("wall_bottom", [0, -3, 0.75, 0, 0, 0], [8, 0.15, 1.5]))
elements.append(wall("wall_top", [0, 3, 0.75, 0, 0, 0], [8, 0.15, 1.5]))
elements.append(wall("wall_left", [-4, 0, 0.75, 0, 0, 0], [0.15, 6, 1.5]))
# Right wall split with wide main door (3m gap, y=-1.5 to y=1.5)
elements.append(wall("wall_right_back", [4, -2.25, 0.75, 0, 0, 0], [0.15, 1.5, 1.5]))
elements.append(wall("wall_right_front", [4, 2.25, 0.75, 0, 0, 0], [0.15, 1.5, 1.5]))

# ---- Top-right semi-enclosed room: x=[1.5, 4], y=[1, 3] ----
elements.append(wall("room_wall_bottom", [2.75, 1, 0.75, 0, 0, 0], [2.65, 0.15, 1.5]))
# Left wall, 1.5m door gap at bottom (y=[1, 2.5])
elements.append(wall("room_wall_left_top", [1.5, 2.75, 0.75, 0, 0, 0], [0.15, 0.5, 1.5]))

# ---- Internal wall ----
elements.append(wall("corridor_h1", [-1.5, -1.5, 0.75, 0, 0, 0], [5.0, 0.15, 1.5]))

# ---- Boxes ----
def box_obs(name, pose, size):
    return f'''    <model name="{name}">
      <static>true</static>
      <pose>{pose[0]} {pose[1]} {pose[2]} {pose[3]} {pose[4]} {pose[5]}</pose>
      <link name="link">
        <collision name="collision">
          <geometry><box><size>{size[0]} {size[1]} {size[2]}</size></box></geometry>
        </collision>
        <visual name="visual">
          <geometry><box><size>{size[0]} {size[1]} {size[2]}</size></box></geometry>
          <material><ambient>0.3 0.5 0.7 1</ambient><diffuse>0.3 0.5 0.7 1</diffuse></material>
        </visual>
      </link>
    </model>'''

elements.append(box_obs("box_room", [2.8, 2.1, 0.45, 0, 0, 0], [0.5, 0.5, 0.9]))
elements.append(box_obs("box_1", [1.5, -1.5, 0.5, 0, 0, 0], [0.8, 0.5, 1.0]))

world_sdf = f'''<?xml version="1.0"?>
<sdf version="1.6">
  <world name="mowen_world">
    <include>
      <uri>model://sun</uri>
    </include>
    <include>
      <uri>model://ground_plane</uri>
    </include>

    <scene>
      <shadows>false</shadows>
    </scene>

    <physics type="ode">
      <real_time_update_rate>1000.0</real_time_update_rate>
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1</real_time_factor>
      <ode>
        <solver>
          <type>quick</type>
          <iters>150</iters>
          <sor>1.4</sor>
          <use_dynamic_moi_rescaling>1</use_dynamic_moi_rescaling>
        </solver>
        <constraints>
          <cfm>0.00001</cfm>
          <erp>0.2</erp>
          <contact_max_correcting_vel>2000.0</contact_max_correcting_vel>
          <contact_surface_layer>0.01</contact_surface_layer>
        </constraints>
      </ode>
    </physics>

{chr(10).join(elements)}

  </world>
</sdf>'''

with open(WORLD_PATH, 'w') as f:
    f.write(world_sdf)

print(f"Generated {WORLD_PATH}")
print(f"  Arena: 8x6m, right 3m door, top-right room with 1.5m door gap")
print(f"  2 boxes, no pillars")
