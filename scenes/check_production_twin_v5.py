"""Check source placements against the recorded survey, not a physical calibration."""
import hashlib
import json
from pathlib import Path
from production_twin_v5 import parts

ROOT=Path(__file__).resolve().parents[1]
rows={p[0]:p for p in parts()}
survey=ROOT/'mujoco/configs/survey_20261028.json'
s=json.loads(survey.read_text(encoding='utf-8'))
m=s['measurements']


def close(a,b):
    assert abs(a-b)<1e-7,(a,b)


long=rows['long green belt'];front=rows['front green belt']
close(long[7],m['belt_under_cup_length_m']*1000)
close(front[6],m['other_belt_length_m']*1000)
close(long[6],m['effective_belt_width_m']*1000)
close(front[7],80)
close(long[5]+long[8],m['belt_surface_height_above_base_direct_m']*1000)
close(rows['moving Y rail 2020'][5],325)
product=rows['product 60x60x60 measured']
assert list(product[6:9])==[v*1000 for v in m['product_size_m']]
close(product[5],100)
close(rows['vacuum cup contact lower face'][5],230)
close(230-70,product[5]+product[8])
close(230-100,130)
rails=[rows['gantry X rail 2020 '+str(y)] for y in [-15,465]]
close(rails[1][4]-rails[1][7]/2-(rails[0][4]+rails[0][7]/2),460)
close(485-20,465)
start=long[4]-long[7]/2
ps1=rows['PS1 pusher head optical face 25mm'];ps2=rows['PS2 optical face 25mm'];ps3=rows['PS3 optical face 25mm']
plate=rows['A1 pusher plate']
assert ps1[9:11]==(0,1), 'PS1 beam must follow A1 +Y push axis'
close(ps1[4]+ps1[8]/2,plate[4])
close(ps1[5]-ps1[6]/2,plate[5]+plate[8])
close(ps1[3]-(front[3]-front[6]/2),50)
close(ps2[4],-215)
close(ps3[4]-(-5),50)
close(ps3[4]-ps2[4],260)
close(long[4]+long[7]/2-(rails[0][4]+rails[0][7]/2),270)
assert sum('optical face' in name for name in rows)==3
result={'checks':'passed','parts':len(rows),'survey_sha256':hashlib.sha256(survey.read_bytes()).hexdigest(),
        'units':'mm; Z=0 at machine base top',
        'poses':{'retracted_cup_z':230,'pick_cup_z':160,'extended_cup_z':130},
        'caveats':['2020 represented by 20x20 solid envelopes, grooves simplified',
                   '270 offset interpreted from positive Y belt end to front crossbeam inner edge',
                   'PS1 on pusher head; PS2 retained at original Y=-215; PS3 alone shifted +50mm from old Y=-5 to +45',
                   'previous 235mm outer span not imposed until the referenced pair and direction are reconciled',
                   '50mm inlet offset interpreted along front belt X; mounts and heights provisional',
                   'tool travel100 is not confirmation of actuator stroke or IO feedback',
                   'CAD update only; existing MuJoCo runs and Unity scene still use their old geometry']}
(ROOT/'output/cad/production_twin_v5_checks.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result,indent=2))
