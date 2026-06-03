#!/usr/bin/env python3
"""创建简单测试世界——放置厚实彩色物体供相机和CNN检测"""
import os

WORLD_DIR = "/home/qc/resource/code/ros2/mowen/src/mowen_gazebo/worlds"
os.makedirs(WORLD_DIR, exist_ok=True)

# 直接在世界文件里定义模型，不用 model:// 引用
objects = ""

# robot spawn at (0,0), objects placed in front (positive x = forward)

# 椅子: 蓝色方块，机器人前方2米
objects += """
    <model name="obj_chair"><static>true</static><pose>2.0 0.5 0.25 0 0 0</pose>
      <link name="link">
        <visual name="vis"><geometry><box><size>0.5 0.5 0.5</size></box></geometry>
          <material><ambient>0.1 0.2 0.8 1</ambient><diffuse>0.1 0.3 1.0 1</diffuse></material>
        </visual>
        <collision name="coll"><geometry><box><size>0.5 0.5 0.5</size></box></geometry></collision>
      </link>
    </model>"""

# 瓶子: 绿色细圆柱
objects += """
    <model name="obj_bottle"><static>true</static><pose>3.0 0.0 0.2 0 0 0</pose>
      <link name="link">
        <visual name="vis"><geometry><cylinder><radius>0.12</radius><length>0.4</length></cylinder></geometry>
          <material><ambient>0.1 0.6 0.2 1</ambient><diffuse>0.2 0.8 0.3 1</diffuse></material>
        </visual>
        <collision name="coll"><geometry><cylinder><radius>0.12</radius><length>0.4</length></cylinder></collision></collision>
      </link>
    </model>"""

# TV/显示器: 深灰色大扁块
objects += """
    <model name="obj_tv"><static>true</static><pose>4.5 0.0 0.4 0 0 0</pose>
      <link name="link">
        <visual name="vis"><geometry><box><size>0.8 0.15 0.6</size></box></geometry>
          <material><ambient>0.15 0.15 0.15 1</ambient><diffuse>0.2 0.2 0.2 1</diffuse></material>
        </visual>
        <collision name="coll"><geometry><box><size>0.8 0.15 0.6</size></box></geometry></collision>
      </link>
    </model>"""

# 人: 多色堆叠方块 (身体+头)
objects += """
    <model name="obj_person"><static>true</static><pose>6.0 0.5 0.0 0 0 0</pose>
      <link name="link">
        <visual name="body"><pose>0 0 0.6 0 0 0</pose><geometry><box><size>0.3 0.3 0.5</size></box></geometry>
          <material><ambient>0.2 0.2 0.8 1</ambient><diffuse>0.3 0.3 0.9 1</diffuse></material>
        </visual>
        <visual name="head"><pose>0 0 1.0 0 0 0</pose><geometry><sphere><radius>0.12</radius></sphere></geometry>
          <material><ambient>0.8 0.6 0.4 1</ambient><diffuse>0.9 0.7 0.5 1</diffuse></material>
        </visual>
        <collision name="coll"><geometry><box><size>0.3 0.3 1.0</size></box></geometry>
          <pose>0 0 0.6 0 0 0</pose></collision>
      </link>
    </model>"""

# 碗: 橙色半球
objects += """
    <model name="obj_bowl"><static>true</static><pose>7.5 0.0 0.05 0 0 0</pose>
      <link name="link">
        <visual name="vis"><geometry><sphere><radius>0.2</radius></sphere></geometry>
          <material><ambient>0.8 0.4 0.1 1</ambient><diffuse>1.0 0.5 0.1 1</diffuse></material>
        </visual>
        <collision name="coll"><geometry><sphere><radius>0.2</radius></sphere></collision>
      </link>
    </model>"""

# 汽车: 大红色方块+轮子
objects += """
    <model name="obj_car"><static>true</static><pose>9.0 -0.5 0.15 0 0 0</pose>
      <link name="link">
        <visual name="body"><pose>0 0 0.2 0 0 0</pose><geometry><box><size>1.2 0.6 0.4</size></box></geometry>
          <material><ambient>0.8 0.1 0.1 1</ambient><diffuse>0.9 0.2 0.2 1</diffuse></material>
        </visual>
        <visual name="top"><pose>0.2 0 0.45 0 0 0</pose><geometry><box><size>0.5 0.5 0.2</size></box></geometry>
          <material><ambient>0.6 0.1 0.1 1</ambient><diffuse>0.7 0.2 0.2 1</diffuse></material>
        </visual>
        <collision name="coll"><geometry><box><size>1.2 0.6 0.4</size></box></geometry>
          <pose>0 0 0.2 0 0 0</pose></collision>
      </link>
    </model>"""

world = f"""<?xml version="1.0"?>
<sdf version="1.6">
  <world name="simple_world">
    <include><uri>model://sun</uri></include>
    <include><uri>model://ground_plane</uri></include>
    <scene><shadows>false</shadows></scene>
    <physics type="ode">
      <real_time_update_rate>1000.0</real_time_update_rate>
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1</real_time_factor>
      <ode>
        <solver><type>quick</type><iters>150</iters><sor>1.4</sor>
        <use_dynamic_moi_rescaling>1</use_dynamic_moi_rescaling></solver>
        <constraints><cfm>0.00001</cfm><erp>0.2</erp>
        <contact_max_correcting_vel>2000.0</contact_max_correcting_vel>
        <contact_surface_layer>0.01</contact_surface_layer></constraints>
      </ode>
    </physics>
{objects}
  </world>
</sdf>
"""

path = os.path.join(WORLD_DIR, "simple_world.world")
with open(path, 'w') as f:
    f.write(world)
print(f"Created: {path} (6 objects: chair, bottle, tv, person, bowl, car)")
