"""Measured-envelope V5, millimetres, machine base TOP is Z=0.

Unmeasured mounts, bin locations, A1 and peripherals remain estimates.
270 mm interpreted from +Y belt end to front crossbeam INNER edge.
"""
import importlib.util
from pathlib import Path

spec=importlib.util.spec_from_file_location('legacy_twin',Path(__file__).parents[1]/'ProductionTwin_V0/ProductionTwin_V0.py')
old=importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)
_box,_cylinder,_open_bin=old._box,old._cylinder,old._open_bin
CUP_DROP=0.0


def sensor(root,tag,x,y,z):
    _box(root,tag+' bracket foot',x+45,y,z-45,30,25,4)
    _box(root,tag+' bracket upright',x+50,y,z-41,5,25,41)
    _cylinder(root,tag+' estimated cylindrical housing',x,y,z,18,58,along_x=True)
    _cylinder(root,tag+' locking ring',x+58,y,z,28,8,along_x=True)
    _cylinder(root,tag+' optical face 25mm',x+66,y,z,25,3,along_x=True)


def pusher_sensor(root):
    # Optical axis +Y, same as A1 push, NOT the other sensors' +X beam.
    # Face center stays (-150,-385,152.5); the body extends behind the head.
    _cylinder(root,'PS1 pusher head estimated cylindrical housing',-150,-452.5,152.5,18,58,along_y=True)
    _cylinder(root,'PS1 pusher head locking ring',-150,-394.5,152.5,28,8,along_y=True)
    _cylinder(root,'PS1 pusher head optical face 25mm',-150,-386.5,152.5,25,3,along_y=True)
    _box(root,'PS1 pusher head mounting upright provisional',-150,-405,102,25,5,43)


def build(root):
    _box(root,'base board',0,0,-12,760,1000,12)
    for name,x,y,sx,sy in [('long',-140,0,80,530),('front',35,-335,470,80)]:
        _box(root,name+' conveyor chassis',x,y,77,sx+20,sy+20,19)
        _box(root,name+' green belt',x,y,96,sx,sy,4)
        for edge in [-1,1]:
            if name=='long':
                _box(root,name+' side rail '+str(edge),x+edge*47,y,86,6,sy+20,14)
            else:
                # Transfer exit at +Y is open around the pusher lane.
                _box(root,name+' side rail left '+str(edge),-190,y+edge*47,86,20,6,14)
                _box(root,name+' side rail right '+str(edge),85,y+edge*47,86,370,6,14)
        for dx,dy in [(-.35,-.35),(.35,.35)]:
            _box(root,name+' estimated support '+str(dx),x+dx*sx,y+dy*sy,0,20,20,77)
    for y in [-265,265]:
        _cylinder(root,'long roller '+str(y),-180,y,84,24,80,along_x=True)
    for x in [-200,270]:
        _cylinder(root,'front roller '+str(x),x,-375,84,24,80,along_y=True)
    _box(root,'L transfer guide',-140,-280,96,80,30,4)
    _box(root,'long conveyor DC motor',-140,298,65,40,46,35)
    _box(root,'front conveyor DC motor',304,-335,65,48,36,35)
    # X inner edges +/-232.5; Y inner edges -5 and455 => 465 x460 clear.
    for x in [-242.5,242.5]:
        for y in [-15,465]:
            _box(root,'gantry post 2020 '+str((x,y)),x,y,0,20,20,305)
    for y in [-15,465]:
        _box(root,'gantry X rail 2020 '+str(y),0,y,305,505,20,20)
    _box(root,'right Y guide 2020',242.5,225,325,20,500,20)
    _box(root,'moving Y rail 2020',-140,225,325,20,500,20)
    _box(root,'pick carriage',-140,60,345,54,60,20)
    _box(root,'A2 carriage mount estimated',-140,60,320,45,32,25)
    _box(root,'A2 body estimated - actuator stroke unconfirmed',-140,60,260,45,32,60)
    for x in [-151,-129]:
        _cylinder(root,'A2 rod '+str(x),x,60,254-CUP_DROP,8,66+CUP_DROP)
    _box(root,'A2 rod end plate',-140,60,246-CUP_DROP,44,30,8)
    _cylinder(root,'vacuum cup stem',-140,60,246-CUP_DROP,8,10)
    _cylinder(root,'vacuum cup contact lower face',-140,60,230-CUP_DROP,22,16)
    for name,y in [('motor X front',-15),('motor X rear',465)]:
        _box(root,name,280,y,325,40,40,40)
    _box(root,'motor Y carriage',-140,480,345,40,40,40)
    _box(root,'S3 A2 upper switch estimated',-167,60,304,8,22,13)
    _box(root,'S4 A2 lower switch estimated',-167,60,269,8,22,13)
    for r,y in enumerate([90,205,320],1):
        for col,x in enumerate([30,145],1):
            _open_bin(root,f'bin R{r}C{col} estimated',x,y)
    # User correction: first optical sensor is mounted above the pusher head.
    # Face center X=-150 is 50 mm from front effective belt's -X end.
    pusher_sensor(root)
    # PS2 stays at the original first long-belt sensor position.
    # PS3 alone moves +50 from its old Y=-5 location; not 50 from PS2.
    sensor(root,'PS2',-256,-215,130)
    sensor(root,'PS3',-256,45,130)
    _box(root,'PS1 pusher head top mounting pad provisional',-185,-385,140,60,25,4)
    _box(root,'A1 front pusher cylinder estimated',-140,-440,60,36,100,42)
    _box(root,'A1 pusher rod',-140,-440,112,9,110,9)
    _box(root,'A1 pusher plate',-140,-385,100,70,6,40)
    for tag,y in [('S1 A1 retracted switch estimated',-480),('S2 A1 extended switch estimated',-402)]:
        _box(root,tag,-166,y,80,9,16,11)
    old._box,old._cylinder=_box,_cylinder
    old._valve(root,'Y1',-455)
    old._valve(root,'Y2',-415)
    _box(root,'PLC 1214C envelope estimated',320,170,0,90,155,85)
    _box(root,'button station envelope estimated',320,-170,0,75,180,35)
    _box(root,'product 60x60x60 measured',-140,60,100,60,60,60)


def run(context):
    import adsk.core,adsk.fusion
    app=adsk.core.Application.get()
    app.documents.add(adsk.core.DocumentTypes.FusionDesignDocumentType)
    design=adsk.fusion.Design.cast(app.activeProduct)
    old._make_appearances(app,design)
    build(design.rootComponent)
    out=Path(__file__).parents[2]/'output/cad'
    for name,factory in [('production_twin_v5.f3d',design.exportManager.createFusionArchiveExportOptions),
                         ('production_twin_v5_fusion.step',design.exportManager.createSTEPExportOptions)]:
        if not design.exportManager.execute(factory(str(out/name))):raise RuntimeError(name)
    app.activeViewport.fit()
