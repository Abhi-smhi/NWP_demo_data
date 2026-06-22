#!/usr/bin/env python
# coding: utf-8

'''
Scan json/aa*.json to produce description (name, units) of grib parameter IDs, write to json/param.json
'''

import json
import eccodes
from collections import defaultdict

TESTFILE = '/lus/h2resw01/scratch/swe7088/deode/Paris_500m_linear_with_mf_pgd_CY49t2_HARMONIE_AROME_Paris_200m_linear_20230820/archive/2023/08/20/18/mbr000/GRIBPFDEOD+0001h00m00s'

def get_para_name_unit(paraID: int, gid):
    info = {}
    try:
        eccodes.codes_set(gid, "paramId", paraID);
        info['name'] = eccodes.codes_get(gid, 'name');
        info['units'] = eccodes.codes_get(gid, 'units');
        info['shortName'] = eccodes.codes_get(gid, 'shortName');
    except:
        print(f'Para {paraID} not found')
    return info



# -- make a list of paramters
import glob as glob
total_params = set()
json_list = glob.glob('json/aa*.json')

for j_file in json_list:
    with open(j_file) as f:
        data = json.load(f)
        for lt in data['level_type']:
            for pt in data['level_type'][lt]['para_type']:
                for para in data['level_type'][lt]['para_type'][pt]['param']:
                    total_params.add(para)


para_codes = {}
with open(TESTFILE) as f:
    gid = eccodes.codes_grib_new_from_file(f)
    for param in total_params:
        desc = get_para_name_unit(param, gid)
        if desc: para_codes[param] = desc
    eccodes.codes_release(gid)

with open('json/para_codes.json', 'w') as f:
    json.dump(para_codes, f)


