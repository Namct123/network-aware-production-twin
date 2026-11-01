"""Build checked solids and three measured-endpoint poses from the Fusion layout."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import export_unity_twin as recorder
recorder.FUSION=ROOT/'fusion/ProductionTwin_V5/ProductionTwin_V5.py'
from cadgen import step,glb
from cadgen import build123d as bd


def parts():
    recorder.PARTS.clear()
    recorder.load_layout()
    return list(recorder.PARTS)


def geometry(drop):
    solids=[]
    for row in parts():
        name,group,shape,x,y,z,sx,sy,sz,ax,ay=row
        moving=name.startswith(('A2 rod ','A2 rod end plate','vacuum cup'))
        if moving:z-=drop
        if name.startswith('A2 rod ') and shape=='cylinder':sz+=drop
        if shape=='box':
            obj=bd.Pos(x,y,z+sz/2)*bd.Box(sx,sy,sz)
        else:
            rotation=(0,90,0) if ax else (-90,0,0) if ay else (0,0,0)
            center=(x+sz/2,y,z) if ax else (x,y+sz/2,z) if ay else (x,y,z+sz/2)
            obj=bd.Pos(*center)*bd.Cylinder(sx/2,sz,rotation=rotation)
        obj.label=name
        from export_viewer_glb import color
        rgb=color(name)
        if name.startswith('product'):rgb=[210,150,65,255]
        obj.color=bd.Color(*(v/255 for v in rgb))
        assert obj.is_valid and obj.volume>0,name
        solids.append(obj)
    return bd.Compound(children=solids)


@step(out='../output/cad/production_twin_v5.step')
@glb(out='../output/cad/production_twin_v5.glb')
def production_twin_v5():return geometry(0)


@step(out='../output/cad/production_twin_v5_pick.step')
@glb(out='../output/cad/production_twin_v5_pick.glb')
def production_twin_v5_pick():return geometry(70)


@step(out='../output/cad/production_twin_v5_extended.step')
@glb(out='../output/cad/production_twin_v5_extended.glb')
def production_twin_v5_extended():return geometry(100)


if __name__=='__main__':
    production_twin_v5()
    production_twin_v5_pick()
    production_twin_v5_extended()
