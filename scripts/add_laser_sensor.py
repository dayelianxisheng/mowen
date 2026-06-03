#!/usr/bin/env python3
"""Add LDS ray sensor to model.sdf for SLAM mapping."""
import xml.etree.ElementTree as ET
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDF_PATH = os.path.join(PROJECT_ROOT, 'src/mowen_gazebo/models/mowen/model.sdf')

# Strip <?xml?> declaration first to avoid ET issues
with open(SDF_PATH, 'r') as f:
    content = f.read()

content = content.replace("<?xml version='1.0' encoding='UTF-8'?>", '').strip()
content = content.replace('<?xml version="1.0" encoding="UTF-8"?>', '').strip()

tree = ET.ElementTree(ET.fromstring(content))
root = tree.getroot()

base_fp = root.find(".//link[@name='base_footprint']")
if base_fp is None:
    print("ERROR: base_footprint link not found")
    exit(1)

# Check if sensor already exists
existing = base_fp.find("sensor[@name='lds_laser']")
if existing is not None:
    print("Laser sensor already exists, skipping.")
    exit(0)

# Build the sensor element
sensor = ET.SubElement(base_fp, 'sensor', {'name': 'lds_laser', 'type': 'ray'})

ET.SubElement(sensor, 'always_on').text = 'true'
ET.SubElement(sensor, 'visualize').text = 'true'
# laser_link is at (0.13374, 0, 0.13599) relative to base_link, which is at (0,0,0) relative to base_footprint
ET.SubElement(sensor, 'pose').text = '0.13374 0 0.13599 0 0 0'
ET.SubElement(sensor, 'update_rate').text = '5'

ray = ET.SubElement(sensor, 'ray')
scan = ET.SubElement(ray, 'scan')
horizontal = ET.SubElement(scan, 'horizontal')
ET.SubElement(horizontal, 'samples').text = '720'
ET.SubElement(horizontal, 'resolution').text = '1.0'
ET.SubElement(horizontal, 'min_angle').text = '0.0'
ET.SubElement(horizontal, 'max_angle').text = '6.28'

rng = ET.SubElement(ray, 'range')
ET.SubElement(rng, 'min').text = '0.12'
ET.SubElement(rng, 'max').text = '3.5'
ET.SubElement(rng, 'resolution').text = '0.015'

noise = ET.SubElement(ray, 'noise')
ET.SubElement(noise, 'type').text = 'gaussian'
ET.SubElement(noise, 'mean').text = '0.0'
ET.SubElement(noise, 'stddev').text = '0.01'

plugin = ET.SubElement(sensor, 'plugin', {'name': 'mowen_laserscan', 'filename': 'libgazebo_ros_ray_sensor.so'})
ros_el = ET.SubElement(plugin, 'ros')
ET.SubElement(ros_el, 'remapping').text = '~/out:=scan'
ET.SubElement(plugin, 'output_type').text = 'sensor_msgs/LaserScan'
ET.SubElement(plugin, 'frame_name').text = 'laser_link'

# Write back
sdf_out = ET.tostring(root, encoding='unicode')
with open(SDF_PATH, 'w') as f:
    f.write(sdf_out)

print(f'Added LDS laser sensor (laser_link, /scan) to {SDF_PATH}')
