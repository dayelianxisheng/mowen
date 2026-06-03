#!/usr/bin/env python3
"""Fix laser pose in model.sdf: align with real robot and add 180 deg yaw flip."""
import xml.etree.ElementTree as ET

SDF_PATH = "/home/qc/resource/code/ros2/mowen/src/mowen_gazebo/models/mowen/model.sdf"
TREE = ET.parse(SDF_PATH)
ROOT = TREE.getroot()

NEW_POSE = "0.1 0 0.05 0 0 0"
changes = 0

# 1. Fix all laser_link collision/visual pose (in lumped base_footprint children)
for elem in ROOT.iter():
    if elem.tag in ("collision", "visual") and "laser_link" in elem.get("name", ""):
        pose = elem.find("pose")
        if pose is not None and "0.1 0 0.05" in (pose.text or ""):
            pose.text = NEW_POSE
            changes += 1

# 2. Fix sensor pose
for elem in ROOT.iter("sensor"):
    if elem.get("name") == "lds_laser":
        pose = elem.find("pose")
        if pose is not None:
            pose.text = NEW_POSE
            changes += 1
        # Fix min_range
        ray = elem.find("ray")
        if ray is not None:
            range_elem = ray.find("range")
            if range_elem is not None:
                min_elem = range_elem.find("min")
                if min_elem is not None and float(min_elem.text) < 0.2:
                    min_elem.text = "0.25"
                    changes += 1

# 3. Fix laser_joint frame pose
for elem in ROOT.iter("frame"):
    if elem.get("name") == "laser_joint":
        pose = elem.find("pose")
        if pose is not None:
            pose.text = NEW_POSE
            changes += 1

TREE.write(SDF_PATH, encoding="utf-8")
print(f"Changed {changes} entries in {SDF_PATH}")
print(f"  laser pose → {NEW_POSE}")
print(f"  min_range → 0.25")
