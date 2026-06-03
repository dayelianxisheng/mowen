#!/usr/bin/env python3
"""Fix model.sdf: inertia as child elements, cylinder collisions for wheels."""
import re, os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDF_PATH = os.path.join(PROJECT_ROOT, 'src/mowen_gazebo/models/mowen/model.sdf')

with open(SDF_PATH, 'r') as f:
    content = f.read()

# Strip XML declaration
content = re.sub(r'<\?xml[^?]*\?>\s*\n?', '', content)

# ------------------------------------------------------------
# Step 1: Fix inertia — convert attributes to child elements
# ------------------------------------------------------------
# Matches: <inertia ixx="0.001" ixy="2e-07" ixz="0.0001" iyy="0.004" iyz="2e-07" izz="0.0049" />
attr_pattern = r'<inertia\s+ixx="([^"]*)"\s+ixy="([^"]*)"\s+ixz="([^"]*)"\s+iyy="([^"]*)"\s+iyz="([^"]*)"\s+izz="([^"]*)"\s*/>'

def make_inertia(m):
    return f'<inertia>\n          <ixx>{m.group(1)}</ixx>\n          <ixy>{m.group(2)}</ixy>\n          <ixz>{m.group(3)}</ixz>\n          <iyy>{m.group(4)}</iyy>\n          <iyz>{m.group(5)}</iyz>\n          <izz>{m.group(6)}</izz>\n        </inertia>'

content = re.sub(attr_pattern, make_inertia, content)
print(f'Fixed inertia attributes -> child elements: {len(re.findall(attr_pattern, content))} remaining (should be 0)')
# Double check
remaining = len(re.findall(r'<inertia\s+ixx=', content))
print(f'  Remaining attribute-style inertias: {remaining}')

# ------------------------------------------------------------
# Step 2: Replace wheel mesh collisions with cylinder
# ------------------------------------------------------------
cylinder_tpl = '''      <collision name='{name}'>
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

for wn in ['back_left_wheel', 'back_right_wheel', 'front_left_wheel', 'front_right_wheel']:
    cname = f'{wn}_collision'
    # Match mesh-based collision block for this wheel
    # The old collision has <surface>...</surface> <pose>...</pose> <geometry><mesh>...</mesh></geometry>
    pattern = rf"      <collision name='{cname}'>.*?</collision>"
    replacement = cylinder_tpl.format(name=cname)
    new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
    if new_content != content:
        print(f'Replaced {cname}: mesh -> cylinder')
        content = new_content
    else:
        print(f'WARNING: could not match {cname}')

with open(SDF_PATH, 'w') as f:
    f.write(content)

print(f'\nDone. Written to {SDF_PATH}')
