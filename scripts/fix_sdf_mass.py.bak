#!/usr/bin/env python3
"""Fix masses and inertias in model.sdf using values from mowen.urdf."""
import xml.etree.ElementTree as ET
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SDF_PATH = os.path.join(PROJECT_ROOT, 'src/mowen_gazebo/models/mowen/model.sdf')
URDF_PATH = os.path.join(PROJECT_ROOT, 'src/mowen_gazebo/urdf/mowen.urdf')

def parse_inertial(link_el):
    """Extract inertial pose, mass, inertia from a link element."""
    inertial = link_el.find('inertial')
    if inertial is None:
        return None
    pose_el = inertial.find('origin') if inertial.find('origin') is not None else inertial.find('pose')
    mass_el = inertial.find('mass')
    inertia_el = inertial.find('inertia')
    if mass_el is None or inertia_el is None:
        return None
    pose = pose_el.get('xyz', '0 0 0') if pose_el is not None else '0 0 0'
    pose += ' ' + (pose_el.get('rpy', '0 0 0') if pose_el is not None else '0 0 0')
    mass = float(mass_el.get('value'))
    inertia = {k: float(v) for k, v in inertia_el.attrib.items()}
    return {'pose': pose, 'mass': mass, 'inertia': inertia}

# Parse URDF: map link_name -> {mass, inertia, pose}
print('Parsing URDF...')
urdf_tree = ET.parse(URDF_PATH)
urdf_mass = {}
for link in urdf_tree.iter('link'):
    name = link.get('name')
    data = parse_inertial(link)
    if data:
        urdf_mass[name] = data
        print(f'  URDF {name}: mass={data["mass"]:.4f}')

# Parse SDF
print('Parsing SDF...')
sdf_tree = ET.parse(SDF_PATH)
sdf_root = sdf_tree.getroot()

fixed_count = 0
for link in sdf_root.iter('link'):
    name = link.get('name')
    if name not in urdf_mass:
        # Check if this is the lumped link containing all merged bodies
        if name == 'base_footprint' and name not in urdf_mass:
            # The gz sdf -p conversion lumps all fixed-joint links into the parent
            # Use base_link URDF data for base_footprint
            target = 'base_link'
            if target in urdf_mass:
                pass  # Will handle below
        continue

    urdf_data = urdf_mass[name]
    inertial = link.find('inertial')
    if inertial is None:
        print(f'  SKIP {name}: no inertial element')
        continue

    # Update pose
    pose_el = inertial.find('pose')
    if pose_el is None:
        pose_el = ET.SubElement(inertial, 'pose')
    pose_parts = urdf_data['pose'].split()
    pose_el.text = ' '.join(pose_parts[:6])

    # Update mass
    mass_el = inertial.find('mass')
    if mass_el is None:
        mass_el = ET.SubElement(inertial, 'mass')
    mass_el.text = str(urdf_data['mass'])

    # Update inertia
    inertia_el = inertial.find('inertia')
    if inertia_el is None:
        inertia_el = ET.SubElement(inertial, 'inertia')

    urdf_inertia = urdf_data['inertia']
    # URDF uses ixx, ixy, ixz, iyy, iyz, izz format
    # SDF uses the same
    inertia_el.clear()
    for key in ['ixx', 'ixy', 'ixz', 'iyy', 'iyz', 'izz']:
        val = urdf_inertia.get(key, 0.0)
        inertia_el.set(key, str(val))

    fixed_count += 1
    print(f'  Fixed {name}: mass {urdf_data["mass"]:.4f} kg')

# Also fix base_footprint mass from base_link URDF data (it's the lumped body)
base_fp = sdf_root.find(".//link[@name='base_footprint']")
if base_fp is not None:
    inertial = base_fp.find('inertial')
    if inertial is not None and 'base_link' in urdf_mass:
        urdf_data = urdf_mass['base_link']
        mass_el = inertial.find('mass')
        current_mass = float(mass_el.text.strip()) if mass_el is not None and mass_el.text else 0
        if abs(current_mass - urdf_data['mass']) > 0.001:
            mass_el.text = str(urdf_data['mass'])
            inertia_el = inertial.find('inertia')
            inertia_el.clear()
            for key in ['ixx', 'ixy', 'ixz', 'iyy', 'iyz', 'izz']:
                inertia_el.set(key, str(urdf_data['inertia'].get(key, 0.0)))
            fixed_count += 1
            print(f'  Fixed base_footprint (from base_link): mass {urdf_data["mass"]:.4f} kg')

# Write back
sdf_tree.write(SDF_PATH, encoding='UTF-8', xml_declaration=True)
print(f'\nDone. Fixed {fixed_count} links.')
