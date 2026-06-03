#!/usr/bin/env python3
"""将 mowen_world 的 ODE 物理参数注入仓库世界，解决机器人漂移问题。"""
import re

# Paths inside container
warehouse = "/tmp/aws-robomaker-small-warehouse-world/worlds/no_roof_small_warehouse.world"
mowen_ref = "/root/mowen_ws/src/mowen_gazebo/worlds/mowen_world.world"

with open(warehouse) as f:
    ws = f.read()

with open(mowen_ref) as f:
    ms = f.read()

# Extract ODE block from mowen
ode_physics = re.search(r"<ode>.*?</ode>", ms, re.DOTALL).group(0)

old_physics = re.search(r"<physics[^>]*type=\"ode\">.*?</physics>", ws, re.DOTALL).group(0)

new_physics = f"""<physics type="ode">
      <real_time_update_rate>1000.0</real_time_update_rate>
      <max_step_size>0.001</max_step_size>
      <real_time_factor>1</real_time_factor>
      {ode_physics}
    </physics>"""

ws = ws.replace(old_physics, new_physics)

with open(warehouse, "w") as f:
    f.write(ws)
print("Fixed physics in warehouse world")
