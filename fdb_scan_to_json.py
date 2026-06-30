#!/usr/bin/env python
# coding: utf-8

import os
import sys
from collections import defaultdict
import json
import argparse
from versions import UrbanAirData
import pprint
import re


'''
Description:
Scans the fdb archives in versions.py and produces json files that describe the structure of the archive desctibed by their 'expver' (metadata)

Instructions:
* Requires module *ecmwf-toolbox* on ATOS

'''


os.environ["FDB5_HOME"] = os.environ["ECMWF_TOOLBOX_DIR"]
import pyfdb

def conver_deep(obj):
    'Serialize for json, recursively search key/value pairs in a dict until a set is found '
    if isinstance(obj, set):
        return sorted(obj)
    elif isinstance(obj, dict):
        return {k: conver_deep(v) for k,v in obj.items()}

def sort_by_minutes(t):
    '''
        key function to help sort the strange time formats in fdb archive
    '''
    if '-' in t:
        s,_ = t.split('-')
    else:
        s = t

    # -- regex stuff taken from fdb_scan.py
    if "h" in s and "m" in s:
      h, m = re.match(r"(\d+)h(\d+)m", s).groups()
    elif "m" in s:
      h, m = (0, re.match(r"(\d+)m", s).groups()[0])
    else:
      h, m = (s,"0")
    return int(h) * 60 + int(m) # return minutes used for sorting


def sort_time_and_levels(data):
    '''
    Sorting levels and times before writing to json
    '''
    print('Sorting levels and times')
    for level_type, l1 in data.items():
        for para_type, l2 in l1['para_type'].items():
            for para, l3 in l2.items():
                times = list(l3['time_steps'])
                times.sort(key=sort_by_minutes)
                l3['time_steps'] = times

        levels = list(l1['levels'])
        if (level_type != 'sfc'):
            levels.sort(key=int)
        else:
            levels = []
        if(level_type != 'hl'): levels.reverse()

        l1['levels'] = levels



def write_to_json(final_data, request):
    file = 'json/' + request['expver'] + '.json'
    print('Writing to', file)
    with open(file, mode='w') as file:
        json.dump(final_data,file)


def scan_param_types(request, ts_shown: bool) -> dict:
    '''
    scan fdb request and classify parameters as 'inst', 'cumul' or
    'other' deadening on time labels
    '''

    paratype = {}
    if ts_shown:
        print('Scanning parameter types (timespan)')
        for x in pyfdb.list(request, keys=True):
            keys = x['keys']
            param = keys.get('param')
            ts_now = keys.get('timespan')
            if (ts_now == 'none'):
                paratype[param] = dict(type='inst', ts=ts_now)
            elif (ts_now == 'fs'):
                paratype[param] = dict(type='cumul', ts=ts_now)
            else:
                paratype[param] = dict(type='other', ts=ts_now)
        return paratype

    print('Scanning parameter types (time labels)')

    paralog = defaultdict(set)
    for x in pyfdb.list(request, keys=True):
        keys = x['keys']
        param = keys.get('param')
        times = keys.get('step')
        paralog[param].add(times)

    for k in paralog.keys():
        for time in paralog[k]:
            if '-' in time:
                if '0-' not in time:
                    paratype[k] = dict(type='other', ts='none')
                    # break
                else:
                    paratype[k] = dict(type='cumul', ts='none')
                    # break
            else:
                paratype[k] = dict(type='inst', ts='none')
    return paratype

def scan_fdb(request, paratype):
    '''
    Scan fdb request and create nested json for each expver
    params:

        request: (dict) MARS-style fdb request
        paratype: (dict) dict containing paramter type (inst, cumul, other) or each parameter number
    '''

    # -- nested json structure
    data_tree = defaultdict(lambda: {'para_type':
        {'inst': defaultdict(lambda: defaultdict(set)),
         'cumul': defaultdict(lambda: defaultdict(set)),
         'other': defaultdict(lambda: defaultdict(set))},
                             'levels': set()}
                           )
    for x in  pyfdb.list(request, keys=True):
        keys = x['keys']

        levtype = keys.get('levtype')
        level = keys.get('levelist')
        param = keys.get('param')
        step = keys.get('step')

        paratype_loc = paratype[param]['type']
        ts_now = paratype[param]['ts']

        data_tree[levtype]['para_type'][paratype_loc][param]['time_steps'].add(step)
        data_tree[levtype]['para_type'][paratype_loc][param]['time_span'].add(ts_now)
        data_tree[levtype]['levels'].add(level)

    return data_tree #conver_deep(data_tree)


def compose_request(uad):

    request= {
        "class": "d1",
        "dataset": "on-demand-extremes-dt",
        "expver": uad["metadata"]["fdb"]["expver"],
        "stream": "oper",
        "type": "fc",
        "georef": uad["metadata"]["fdb"]["georef"],

    }
    return request

# ------------- MAIN LOOP ----------------------------------

def main():
    parser = argparse.ArgumentParser(description="Process a URL, scan fdb to json.")
    parser.add_argument("-u", "--url", help="Specify a URL to process", default=None)
    args = parser.parse_args()

    if args.url:
        uad = UrbanAirData().urls[args.url]
        print('Scanning version',args.url,':', uad['name'])
        try:
            request = compose_request(uad)
            ts_shown = UrbanAirData().urls[args.url]['metadata']['polytope']['ts_present']
            paratype_uad = scan_param_types(request,ts_shown)
            print('Creating json')
            final_data = scan_fdb(request, paratype_uad)
            final_data = conver_deep(final_data)
            sort_time_and_levels(final_data)
            write_to_json({'level_type':final_data},request)
        except Exception as e:
            print('Skipped, caught following exception:\n', e)

        return

    for url in UrbanAirData().urls:
        uad = UrbanAirData().urls[url]
        print('Scanning version',url,':', uad['name'])
        try:
            request = compose_request(uad)
            ts_shown = UrbanAirData().urls[url]['metadata']['polytope']['ts_present']
            paratype_uad = scan_param_types(request, ts_shown)
            print('Creating json')
            final_data = scan_fdb(request, paratype_uad)
            final_data = conver_deep(final_data)
            sort_time_and_levels(final_data)
            write_to_json({'level_type':final_data},request)
        except Exception as e:
            print('Skipped, caught following exception:\n', e)

if __name__=='__main__':
    main()
