#!/usr/bin/env python3
"""Update laser sensor params: rate 5->10Hz, samples 720->1440."""
import xml.etree.ElementTree as ET
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDF_PATH = os.path.join(PROJECT_ROOT, 'src/mowen_gazebo/models/mowen/model.sdf')

with open(SDF_PATH, 'r') as f:
    content = f.read()

content = content.replace("<?xml version='1.0' encoding='UTF-8'?>", '').strip()
content = content.replace('<?xml version="1.0" encoding="UTF-8"?>', '').strip()

tree = ET.ElementTree(ET.fromstring(content))
root = tree.getroot()

sensor = root.find(".//sensor[@name='lds_laser']")
if sensor is None:
    print("ERROR: lds_laser sensor not found")
    exit(1)

changes = []

ur = sensor.find('update_rate')
if ur is not None and ur.text == '5':
    ur.text = '10'
    changes.append('update_rate: 5 -> 10')

samples = sensor.find(".//horizontal/samples")
if samples is not None and samples.text == '720':
    samples.text = '1440'
    changes.append('samples: 720 -> 1440')

if not changes:
    print("No changes needed.")
    exit(0)

sdf_out = ET.tostring(root, encoding='unicode')
with open(SDF_PATH, 'w') as f:
    f.write(sdf_out)

print(f'Updated laser sensor in {SDF_PATH}')
for c in changes:
    print(f'  {c}')
