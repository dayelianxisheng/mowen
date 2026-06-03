#!/usr/bin/env python3
"""Replace mesh collision with cylinder for wheel links in model.sdf."""
import re, os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDF_PATH = os.path.join(PROJECT_ROOT, 'src/mowen_gazebo/models/mowen/model.sdf')

with open(SDF_PATH, 'r') as f:
    content = f.read()

# Cylinder collision template for one wheel (radius=0.033, length=0.020, axis=Y via rpy=1.57)
# The cylinder is oriented along Y (wheel rotation axis) by rotating around X by 1.57 rad
cylinder_collision = '''      <collision name='{collision_name}'>
      <surface>
        <friction>
          <ode>
            <mu>0.3</mu>
            <mu2>0.02</mu2>
          </ode>
        </friction>
        <contact>
          <ode>
            <soft_cfm>0</soft_cfm>
            <soft_erp>0.2</soft_erp>
            <kp>1e5</kp>
            <kd>10</kd>
            <max_vel>0.01</max_vel>
            <min_depth>0.001</min_depth>
          </ode>
        </contact>
      </surface>
        <pose>0 0 0 1.57 0 0</pose>
        <geometry>
          <cylinder>
            <radius>0.0485</radius>
            <length>0.0506</length>
          </cylinder>
        </geometry>
      </collision>'''

wheel_names = ['back_left_wheel', 'back_right_wheel', 'front_left_wheel', 'front_right_wheel']

for name in wheel_names:
    collision_name = f'{name}_collision'
    # Regex to match the entire collision block for this wheel (mesh-based)
    pattern = rf"      <collision name='{collision_name}'>.*?</collision>"
    replacement = cylinder_collision.format(collision_name=collision_name)
    content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    print(f'Replaced {collision_name}: mesh -> cylinder')

with open(SDF_PATH, 'w') as f:
    f.write(content)

print(f'\nDone. Updated {SDF_PATH}')
