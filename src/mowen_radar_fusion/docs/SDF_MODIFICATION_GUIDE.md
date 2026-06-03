# SDF 修改指南

## 规则

1. **禁止手动编辑 SDF/URDF XML 文件**
2. 所有修改必须通过 Python 脚本完成
3. 脚本放在 `/home/qc/resource/code/ros2/mowen/scripts/` 目录
4. 修改前自动备份 (xxx.backup)
5. 修改后打印修改摘要

## 已有脚本

| 脚本 | 功能 |
|------|------|
| `add_radar_and_camera_sensors.py` | 添加雷达传感器 + 相机传感器 + camera_optical frame |

## 如何添加新传感器

```python
# 参考 add_radar_and_camera_sensors.py 的模式

def add_new_sensor(root):
    """添加新传感器到 model"""
    model = root  # 或 root.find('.//model')
    
    # 1. 添加 frame
    frame = ET.SubElement(model, 'frame')
    frame.set('name', 'new_sensor_joint')
    frame.set('attached_to', 'base_link')
    ET.SubElement(frame, 'pose').text = 'x y z r p y'
    
    # 2. 添加 sensor
    sensor = ET.SubElement(model, 'sensor')
    sensor.set('name', 'new_sensor')
    sensor.set('type', 'ray')  # ray, camera, imu, etc
    
    # 3. 配置 sensor 参数...
    
    # 4. 添加 plugin
    plugin = ET.SubElement(sensor, 'plugin')
    plugin.set('filename', 'libgazebo_ros_xxx.so')
    # ...
    
    return 1  # 返回修改计数

# 备份
shutil.copy2(SDF_PATH, SDF_PATH + '.backup')
# 解析
tree = ET.parse(SDF_PATH)
# 修改
count = add_new_sensor(tree.getroot())
# 写入
ET.indent(tree, space='  ')
tree.write(SDF_PATH, encoding='utf-8', xml_declaration=True)
print(f"Added {count} new sensors")
```

## 传感器在模型上的位置

```
base_link 原点 = robot 底盘中心 (z=0)

传感器位置 (相对 base_link):
  radar_link:   x=0.15,  y=0.0,  z=0.18  (前15cm, 高18cm)
  camera_link:  x=0.149, y=0.0,  z=0.20  (前15cm, 高20cm)
  laser_link:   x=0.134, y=0.0,  z=0.136 (前13cm, 高14cm)
  imu_link:     x=0.144, y=0.0,  z=0.103 (前14cm, 高10cm)
```

## 已安装的 Gazebo 插件

| 插件库 | 用途 |
|--------|------|
| libgazebo_ros_ray_sensor.so | 激光/雷达测距传感器 |
| libgazebo_ros_camera.so | RGB 相机 |
| libgazebo_ros_planar_move.so | 平面移动控制 |
| libgazebo_ros_joint_state_publisher.so | 关节状态发布 |
