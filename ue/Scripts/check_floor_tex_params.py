# -*- coding: utf-8 -*-
import unreal

for p in ('/Game/RobotGame/Art/Environment/M_SteelLight', '/Game/RobotGame/Art/Environment/M_Steel'):
    mi = unreal.EditorAssetLibrary.load_asset(p)
    if mi:
        tps = mi.get_editor_property('texture_parameter_values')
        unreal.log('=== ' + p + ' ===')
        for tp in tps:
            name = tp.get_editor_property('parameter_info').name
            val = tp.get_editor_property('parameter_value')
            unreal.log('  tex param: ' + str(name) + ' = ' + (val.get_name() if val else 'None'))

with open(r'C:\Users\25227\Documents\robot_game\docs\floor_tex_params.txt', 'w') as f:
    f.write('FLOOR_TEX_PARAMS_DONE\n')
