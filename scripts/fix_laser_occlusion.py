#!/usr/bin/env python3
"""Limit laser scan to front 240deg: skip rear 120deg (matching real robot occlusion)."""
import xml.etree.ElementTree as ET

SDF_PATH = "/home/qc/resource/code/ros2/mowen/src/mowen_gazebo/models/mowen/model.sdf"
TREE = ET.parse(SDF_PATH)
ROOT = TREE.getroot()

# Front 240deg: -120 to +120 deg in radians
NEW_MIN_ANGLE = "-2.094395"
NEW_MAX_ANGLE = "2.094395"
NEW_SAMPLES = "960"  # 1440 * 240/360 = same angular resolution

changes = 0

for sensor in ROOT.iter("sensor"):
    if sensor.get("name") == "lds_laser":
        scan = sensor.find(".//horizontal")
        if scan is not None:
            for child in scan:
                if child.tag == "min_angle":
                    child.text = NEW_MIN_ANGLE
                    changes += 1
                elif child.tag == "max_angle":
                    child.text = NEW_MAX_ANGLE
                    changes += 1
                elif child.tag == "samples":
                    child.text = NEW_SAMPLES
                    changes += 1

TREE.write(SDF_PATH, encoding="utf-8")
print(f"Changed {changes} entries in {SDF_PATH}")
print(f"  laser scan: -120deg to +120deg (front 240deg, rear occluded)")
print(f"  samples: 1440 -> 960")
