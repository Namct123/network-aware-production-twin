"""Functional, parameterized cell; measured envelope is not a calibrated CAD replica."""
import xml.etree.ElementTree as ET
from config import exact_keys, number, vector, ordered

FIELDS = ('frame_inner_xy_m frame_center_xy_m profile_section_xy_m beam_underside_z_m '
          'base_size_m belt_surface_z_m belt_thickness_m long_belt_width_m '
          'side_rail_thickness_m side_rail_height_m transfer_bridge_y_m '
          'cup_retracted_z_m cup_radius_m cup_height_m cup_contact_gap_m cup_contact_dimension cup_patch_radius_m cup_pad_radius_m '
          'carriage_size_m pusher_rest_xyz_m pusher_plate_size_m '
          'bin_floor_top_z_m bin_floor_thickness_m bin_wall_height_m bin_wall_thickness_m '
          'pusher_sensor_offset_m transfer_detection_range_m admission_centering_distance_m '
          'admission_timeout_s admission_stop_margin_m front_stop_coast_m bin_release_descent_m gravity_m_s2 sensor_roles').split()

def validate_mechanics(c):
    m,g = c['mechanics'],c['geometry']
    exact_keys(m,FIELDS,'mechanics')
    for key in ('frame_inner_xy_m','profile_section_xy_m'):
        vector(m[key],2,key,positive=True)
    vector(m['frame_center_xy_m'],2,'frame_center_xy_m')
    for key in ('base_size_m','carriage_size_m','pusher_plate_size_m'):
        vector(m[key],3,key,positive=True)
    for key in ('pusher_rest_xyz_m','pusher_sensor_offset_m','gravity_m_s2'):
        vector(m[key],3,key)
    ordered(m['transfer_bridge_y_m'],'transfer_bridge_y_m')
    for key in FIELDS:
        if key in {'sensor_roles','cup_contact_dimension'} or isinstance(m[key],list):
            continue
        number(m[key],key,0,positive=key not in {'cup_contact_gap_m','admission_centering_distance_m'})
    exact_keys(m['sensor_roles'],('transfer_present','ps1','ps2'),'sensor_roles')
    labels=list(m['sensor_roles'].values())
    if any(not isinstance(v,str) or not v.strip() for v in labels) or len(set(labels))!=3:
        raise ValueError('three distinct physical sensor labels are required')
    if m['beam_underside_z_m'] <= m['belt_surface_z_m'] or m['cup_retracted_z_m'] >= m['beam_underside_z_m']:
        raise ValueError('invalid beam/cup/belt height relationship')
    if m['beam_underside_z_m'] <= m['profile_section_xy_m'][1] or m['bin_floor_top_z_m'] < m['bin_floor_thickness_m']:
        raise ValueError('invalid post height or bin floor below the base')
    if min(g['product_size_m'][:2]) < 2*m['cup_radius_m']:
        raise ValueError('this flat-pad suction model requires a product covering the cup footprint')
    if type(m['cup_contact_dimension']) is not int or m['cup_contact_dimension'] not in (3,4,6):
        raise ValueError('cup contact dimension must be 3, 4 or 6')
    if m['cup_patch_radius_m']+m['cup_pad_radius_m'] > m['cup_radius_m']:
        raise ValueError('contact pads must fit the cup footprint')
    admission_distance=g['product_initial_xyz_m'][0]-g['front_belt_xy_m'][0][0]-g['product_size_m'][0]/2
    if admission_distance <= m['admission_stop_margin_m']+m['front_stop_coast_m']:
        raise ValueError('no front-belt stopping allowance for the known reset pose')
    if any(g['product_size_m'][i] >= width for i,width in enumerate(
            (m['long_belt_width_m'],g['front_belt_xy_m'][1][1]-g['front_belt_xy_m'][1][0]))):
        raise ValueError('product must fit both effective belt widths')
    if m['cup_retracted_z_m']-g['joint_limits_m']['a2_joint'][1] <= m['belt_surface_z_m']:
        raise ValueError('full tool descent must remain above the belt')
    contact_z=m['cup_retracted_z_m']-c['motion']['a2_pick_m']
    if abs(contact_z-(m['belt_surface_z_m']+g['product_size_m'][2])) > m['cup_contact_gap_m']:
        raise ValueError('pick descent does not meet product top; update related dimensions together')
    if not 0 < m['bin_release_descent_m'] <= g['joint_limits_m']['a2_joint'][1]:
        raise ValueError('bin release descent exceeds tool travel')
    if m['cup_retracted_z_m']-m['bin_release_descent_m']-g['product_size_m'][2] <= m['bin_floor_top_z_m']+m['bin_wall_height_m']:
        raise ValueError('release pose would put the carried product below the bin wall top')
    for key in ('base_size_m','pusher_plate_size_m'):
        if min(m[key])<=0:
            raise ValueError(key)

def vec(x):
    return ' '.join(format(float(v),'.12g') for v in x)

def model_xml(c):
    g,p,m=c['geometry'],c['plant'],c['mechanics']
    root=ET.Element('mujoco',model='parameterized_measured_envelope')
    ET.SubElement(root,'compiler',angle='radian',autolimits='true')
    ET.SubElement(root,'option',timestep=str(c['timing']['physics_step_s']),gravity=vec(m['gravity_m_s2']),integrator='implicitfast')
    ET.SubElement(ET.SubElement(root,'visual'),'global',offwidth='1200',offheight='900')
    world=ET.SubElement(root,'worldbody')
    ET.SubElement(world,'light',pos='0 -0.5 1.5',dir='0 0 -1')
    ET.SubElement(world,'camera',name='overview',pos='1.15 -1.35 1.15',xyaxes='0.76 0.65 0 -0.34 0.4 0.85')
    def box(parent,name,pos,full,rgba='0.65 0.7 0.74 1',contact=True,**attrs):
        if not contact: attrs.update(contype='0',conaffinity='0')
        return ET.SubElement(parent,'geom',name=name,type='box',pos=vec(pos),size=vec(v/2 for v in full),rgba=rgba,**attrs)
    base=m['base_size_m']; box(world,'base_board',(0,0,-base[2]/2),base,'0.2 0.24 0.27 1')
    z,t=m['belt_surface_z_m'],m['belt_thickness_m']
    for name,bounds in [('front_green_belt',g['front_belt_xy_m']),
                        ('long_green_belt',[[g['lane_x_m']-m['long_belt_width_m']/2,g['lane_x_m']+m['long_belt_width_m']/2],g['long_belt_y_m']])]:
        box(world,name,[sum(b)/2 for b in bounds]+[z-t/2],
            [b[1]-b[0] for b in bounds]+[t],'0.06 0.45 0.19 1',friction=vec(p['belt_friction']),surfacevel='0 0 0 0 0 0')
    bridge=m['transfer_bridge_y_m']
    box(world,'transfer_bridge',(g['lane_x_m'],sum(bridge)/2,z-t/2),
        (m['long_belt_width_m'],bridge[1]-bridge[0],t),friction=vec(p['belt_friction']))
    for sign in (-1,1):
        box(world,'long_side_rail_'+str(sign),(g['lane_x_m']+sign*(m['long_belt_width_m']+m['side_rail_thickness_m'])/2,
            sum(g['long_belt_y_m'])/2,z+m['side_rail_height_m']/2),
            (m['side_rail_thickness_m'],g['long_belt_y_m'][1]-g['long_belt_y_m'][0],m['side_rail_height_m']))
    fx,fy=m['frame_center_xy_m']; ix,iy=m['frame_inner_xy_m']; sx,sy=m['profile_section_xy_m']
    for sign_y in (-1,1):
        y=fy+sign_y*(iy+sy)/2
        box(world,'fixed_crossbeam_'+str(sign_y),(fx,y,m['beam_underside_z_m']-sy/2),(ix+2*sx,sy,sy),contact=False)
        for sign_x in (-1,1):
            h=m['beam_underside_z_m']-sy
            box(world,f'post_{sign_x}_{sign_y}',(fx+sign_x*(ix+sx)/2,y,h/2),(sx,sy,h),contact=False)
    origins={}
    def body(parent,name,joint,world_pos,axis):
        parent_world=origins.get(parent,(0,0,0))
        el=ET.SubElement(world if parent is None else bodies[parent],'body',name=name,
                         pos=vec(a-b for a,b in zip(world_pos,parent_world)))
        origins[name]=world_pos
        ET.SubElement(el,'joint',name=joint,type='slide',axis=vec(axis),range=vec(g['joint_limits_m'][joint]),damping=str(p['joint_damping']))
        inert=p['link_inertials'][name]
        ET.SubElement(el,'inertial',mass=str(inert['mass_kg']),pos=vec(inert['com_m']),diaginertia=vec(inert['diagonal_kg_m2']))
        return el
    bodies={}
    rx,ry=g['robot_origin_xy_m']
    bodies['x_beam_link']=body(None,'x_beam_link','x_joint',(rx,fy,m['beam_underside_z_m']+sy/2),(1,0,0))
    box(bodies['x_beam_link'],'moving_beam',(0,0,0),(sx,iy+2*sy,sy),contact=False)
    carriage_z=m['beam_underside_z_m']+sy+m['carriage_size_m'][2]/2
    bodies['y_carriage_link']=body('x_beam_link','y_carriage_link','y_joint',(rx,ry,carriage_z),(0,1,0))
    box(bodies['y_carriage_link'],'carriage',(0,0,0),m['carriage_size_m'],'0.15 0.17 0.2 1',contact=False)
    bodies['cup_link']=body('y_carriage_link','cup_link','a2_joint',(rx,ry,m['cup_retracted_z_m']+m['cup_height_m']/2),(0,0,-1))
    ET.SubElement(bodies['cup_link'],'geom',name='vacuum_cup',type='cylinder',size=vec((m['cup_radius_m'],m['cup_height_m']/2)),
                  rgba='0.1 0.1 0.12 1',contype='0',conaffinity='0',adhesion='0')
    # Four finite-force contact samples approximate the cup footprint; no parenting,
    # teleportation or perfect weld. Patch geometry and effective adhesion await calibration.
    radius=m['cup_patch_radius_m']; pad=m['cup_pad_radius_m']
    for i,(px,py) in enumerate(((radius,0),(-radius,0),(0,radius),(0,-radius))):
        ET.SubElement(bodies['cup_link'],'geom',name=f'vacuum_pad_{i}',type='sphere',
                      pos=vec((px,py,-m['cup_height_m']/2+pad)),size=str(pad),rgba='0.15 0.15 0.15 1',
                      friction=vec(p['cup_friction']),adhesion='0',gap=str(m['cup_contact_gap_m']),condim=str(m['cup_contact_dimension']))
    bodies['pusher_link']=body(None,'pusher_link','a1_joint',m['pusher_rest_xyz_m'],(0,1,0))
    box(bodies['pusher_link'],'pusher_plate',(0,0,0),m['pusher_plate_size_m'])
    wall=m['bin_wall_thickness_m']; floor=m['bin_floor_thickness_m']; bx,by=g['bin_inner_size_xy_m']; bh=m['bin_wall_height_m']
    for i,(x,y) in enumerate(g['bin_centers_xy_m']):
        prefix=f'bin_r{i//2+1}c{i%2+1}_'
        box(world,prefix+'floor',(x,y,m['bin_floor_top_z_m']-floor/2),(bx+2*wall,by+2*wall,floor),'0.82 0.79 0.91 1')
        for sign in (-1,1):
            box(world,prefix+'side_wall_'+str(sign),(x+sign*(bx+wall)/2,y,m['bin_floor_top_z_m']+bh/2),(wall,by+2*wall,bh),'0.82 0.79 0.91 1')
            box(world,prefix+'end_wall_'+str(sign),(x,y+sign*(by+wall)/2,m['bin_floor_top_z_m']+bh/2),(bx,wall,bh),'0.82 0.79 0.91 1')
    product=ET.SubElement(world,'body',name='product',pos=vec(g['product_initial_xyz_m']))
    ET.SubElement(product,'freejoint',name='product_free')
    box(product,'product_box',(0,0,0),g['product_size_m'],'0.72 0.42 0.2 1',mass=str(p['product_mass_kg']),friction=vec(p['product_friction']))
    actuator=ET.SubElement(root,'actuator')
    for joint in g['joint_limits_m']:
        ET.SubElement(actuator,'position',name=joint+'_target',joint=joint,kp=str(p['position_kp'][joint]),
                      dampratio=str(p['dampratio']),ctrlrange=vec(g['joint_limits_m'][joint]))
    sensors=ET.SubElement(root,'sensor')
    for key,y in g['ps_y_m'].items():
        ET.SubElement(world,'site',name=key+'_beam',pos=vec((g['optical_xz_m'][0],y,g['optical_xz_m'][1])),
                      quat='0.70710678 0 0.70710678 0',size='0.003',rgba='1 0.2 0.1 0.8')
        ET.SubElement(sensors,'rangefinder',name=key+'_range',site=key+'_beam')
    ET.SubElement(bodies['pusher_link'],'site',name='transfer_present_beam',pos=vec(m['pusher_sensor_offset_m']),
                  quat='0.70710678 -0.70710678 0 0',size='0.003',rgba='1 0.6 0.1 0.8')
    ET.SubElement(sensors,'rangefinder',name='transfer_present_range',site='transfer_present_beam')
    ET.indent(root,space='  ')
    return '<?xml version="1.0"?>\n'+ET.tostring(root,encoding='unicode')+'\n'
