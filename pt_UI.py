from versions import UrbanAirData
import json
import ipywidgets as widgets
from IPython.display import display, HTML
from datetime import datetime
from ipyfilechooser import FileChooser



uad = UrbanAirData().urls
with open('json/para_codes.json') as f:
    para_codes = json.load(f)

available_para = list(para_codes.keys())

# -- only those urls in version.py that have an associated json
file_options = [x for x,values in uad.items() if 'json' in values['metadata']]# and values['metadata']['polytope']['ts_present']]

# -- helper for level type
lt_dict = dict(sfc='surface', pl='pressure level', hl='height level', ml='model level')

# -- empty request and file metadata
file_meta = dict(json_file = '', expver = '', collection = '', georef='',
        address='', ts_present=False, timespan='', t_match=True )

datfile= {}
request= {}



#--------------------------UI ELEMENTS -------------------------------------------
version_dd = widgets.Dropdown(
    options=file_options,
    value=file_options[0],
    # description="Version no.:",
    layout=widgets.Layout(width="100px"),
    # style={"description_width": "120px"},
)

lt_dd = widgets.Dropdown(
    # description="Level type.:",
    layout=widgets.Layout(width="200px"),
    # style={"description_width": "120px"},
)

paratype_dd = widgets.Dropdown(
    # description="Parameters.:",
    options = [('instantaneous', 'inst'), ('cumulative', 'cumul'), ('other', 'other')],
    value = 'inst',
    layout=widgets.Layout(width="200px"),
    # style={"description_width": "120px"},
)

param_ms = widgets.SelectMultiple(
    # description="Parameters.:",
    options = [],
    layout=widgets.Layout(width="600px", height='400px'),
    # style={"description_width": "120px"},
)


time_slider = widgets.SelectionRangeSlider(
    # description="Time steps :",
    layout=widgets.Layout(width="80%"),
    options = (0,0),
    continuous_update=False
)

compute_button = widgets.Button(
    description='Create request',
    layout=widgets.Layout(pos="60%")
)

download_button = widgets.Button(
    description='Download',
    layout=widgets.Layout(pos="60%")
)

button_cont = widgets.HBox([compute_button, download_button])
#button_cont.layout.display = 'flex'
button_cont.layout.justify_content = 'space-around'
button_cont.layout.align_items = 'flex-start'
button_cont.layout.height = '100px'
button_cont.layout.width = '80%'


level_ms = widgets.SelectMultiple(
    # description="Levels :",
    layout=widgets.Layout(width="100px",height='400px'),
    # style={"description_width": "120px"},
)


format_dd = widgets.Dropdown(
    options=['grib', 'netCDF'],
    value='grib',
    description="Format :",
    layout=widgets.Layout(width='20%'),
)


fc = FileChooser(path='.', select_default=False)
fc.title = '<b>Select Directory and Enter Filename</b>'


out = widgets.Output( layout=widgets.Layout(width="80%"))
out_request = widgets.Output(layout=widgets.Layout(width="80%"))
out_log = widgets.Output(layout=widgets.Layout(width="80%"))

#------------------------------------------------------------------------------
#------------------------- Functions ------------------------------------------
#------------------------------------------------------------------------------

def update_file(*args):
    version = version_dd.value
    json_file = uad[version]['metadata']['json']
    dt = uad[version]["metadata"]["date"]
    dt = datetime.strptime(dt, "%Y-%m-%dT%H:%M:%SZ")


    # -- update file_meta
    file_meta['json_file'] = json_file
    file_meta['expver'] = uad[version]['metadata']['fdb']['expver']
    file_meta['collection'] = uad[version]["metadata"]["polytope"]["collection"]
    file_meta['georef'] = uad[version]["metadata"]["fdb"]["georef"]
    file_meta['address'] = uad[version]["metadata"]["polytope"]["url"]
    file_meta['ts_present'] =  uad[version]["metadata"]["polytope"]["ts_present"]

    file_meta['desc'] =  uad[version]["metadata"]["desc"]
    file_meta['range'] =  uad[version]["metadata"]["forecast_range"].strip('PT')
    file_meta['nx'] =  uad[version]["metadata"]["nx"]
    file_meta['ny'] =  uad[version]["metadata"]["nx"]
    file_meta['dx'] =  uad[version]["metadata"]["dx"]

    file_meta['date'] = dt.strftime("%Y%m%d")
    file_meta['time'] =  dt.strftime("%H%M")

    with out:
        out.clear_output(wait=False)
        print(f"\t\t --- ARCHIVE SUMMARY ---\n")
        print(f"Archive name: {uad[version]['name']}")
        print('expver :', file_meta['expver'])
        print('collection:', file_meta['collection'])
        print('description:', file_meta['desc'])
        print('date:', file_meta['date'])
        print('time:', file_meta['time'])
        print('range:', file_meta['range'])
        print('nx:', file_meta['nx'])
        print('ny:', file_meta['ny'])
        print('dx:', file_meta['dx'])


    with open(json_file) as f:
        datfile[0] = json.load(f)

    lt_dd.options=['sfc'] # --
    lt_dd.value='sfc'# -- reset to surface every time a new archive is picked
    lt = datfile[0]["level_type"]
    lt_dd.options=[(lt_dict[x], x) for x in lt.keys()]
    update_levels()

def check_request_doable(*args):
    time_slider.disabled = False
    compute_button.disabled = False
    warn = ''
    if (not param_ms.options) or  (not param_ms.value):
        time_slider.options = (' ',)
        time_slider.disabled = True
        compute_button.disabled = True
        warn += '\n * No parameters available or chosen'

    if (not file_meta['t_match']):
        time_slider.options = (' ',)
        time_slider.disabled = True
        compute_button.disabled = True
        warn += '\n * Chosen paramters were stored at different frequencies'

    if (not level_ms.value  and lt_dd.value != 'sfc'):
        compute_button.disabled = True
        warn += '\n * No levels chosen'

    with out_log:
        out_log.clear_output(wait=False)
        print('\t\t --- INFO ---')
        if warn:
            print('Cannot make request:', warn)
        else:
            print("Good to go! Create request")


def update_paras(*args):
    lt = datfile[0]["level_type"]
    lt_val = lt_dd.value

    paratype_val = paratype_dd.value
    # -- read para_codes for names and units
    para_options = [( para_codes[x]['shortName']+':   ' + para_codes[x]['name'] + ' [' + para_codes[x]['units'] + ']', int(x))
                    if x in available_para
                    else (x + ' -- missing info--', int(x))
                    for x in list(lt[lt_val]['para_type'][paratype_val].keys())]
    param_ms.options = para_options
    update_time_steps()

def update_levels(*args):
    lt = datfile[0]["level_type"]
    lt_val = lt_dd.value
    level_ms.options = list(lt[lt_val]['levels'])
    update_paras()


def update_time_steps(*args):
    lt = datfile[0]["level_type"]
    lt_val = lt_dd.value
    paratype_val = paratype_dd.value

    times_now = []
    t_list = []
    if param_ms.value and lt_val:
        file_meta['timespan'] = lt[lt_val]['para_type'][paratype_val][str(param_ms.value[0])]["time_span"]

        t_list = [lt[lt_val]['para_type'][paratype_val][str(x)]["time_steps"]  for x in param_ms.value]
        file_meta['t_match'] = all(l == t_list[0] for l in t_list) or (len(t_list) == 1)
        times_now = t_list[0]

    if times_now:
        time_slider.options = times_now
    else:
        time_slider.options = (' ',)

    check_request_doable()


def delim_txt_list(l_in):
    lim = '/'
    return lim.join(map(str, l_in))


def create_request(*args):
    import pprint

    request['class'] = 'd1'
    request['dataset'] = 'on-demand-extremes-dt'
    request['stream'] =  'oper'
    request['type'] =  'fc'
    if file_meta['ts_present']:
        request[ 'timespan']=  list(file_meta['timespan'])[0]
    else:
        request.pop('timespan', None)

    request['georef'] = file_meta['georef']
    request['expver'] = file_meta['expver']
    request['date'] = file_meta['date']
    request['time'] = file_meta['time']
    request['format'] = format_dd.value
    request['levtype'] = lt_dd.value

    time_list = time_slider.options[time_slider.index[0]: time_slider.index[1]+1]
    request['step'] =  delim_txt_list(time_list)
    request['param'] = delim_txt_list(param_ms.value)
    if lt_dd.value != 'sfc':
        request['levelist'] = delim_txt_list(level_ms.value)

    with out_log:
        out_log.clear_output(wait=False)

    with out_request:
        out_request.clear_output(wait=False)
        print(f"\t\t --- Polytope request ---\n")


        pprint.pprint(request)

def download_request(*args):
    import earthkit.data as edata
    from pathlib import Path

    file = fc.value
    Path(file).touch()

    with out_log:
        out_log.clear_output(wait=False)
        print('\t\t --- Download status ---\n')
        if not request:
            print('Empty request, skipping')
            return
        if not fc.value:
            print('No filename provided, skipping')
            return
        print(f'Starting ...')
        print(f'File : {file}')

    try:
        dataNOW = edata.from_source("polytope", file_meta["collection"], request,
                      address=file_meta['address'], stream=False)
        dataNOW.to_target('file', file)

    except Exception as e:
        msg = f'Failure caught exception at\n {e}'

    finally:
        msg = f'Success!\nData downloaded at {file}'

    with out_log:
        print(msg)


#------------------------------------------------------------------------------
#------------------------ Layout and UI ---------------------------------------
#------------------------------------------------------------------------------

main_layout = widgets.Layout(
    width="70%",
    padding="20px",
   border="2px solid #ddd",
   display='flex',
   justify_content = 'space-between'

)


# ---------- Two-column layout for the level and params ----------

select_para_level_type = widgets.HBox(
    [
        widgets.VBox(
            [widgets.HTML("<b>Level type:</b> "), lt_dd],
            layout=widgets.Layout(width="50%")
            ),
        widgets.VBox(
            [widgets.HTML("<b>Parameter type:</b>") , paratype_dd],
            layout=widgets.Layout(width="50%")
        ),
    ]
)

param_title =  widgets.HTML("<b>Parameters:</b>")
level_title =  widgets.HTML("<b>Levels:</b>")

select_para_level = widgets.HBox(
    [
        widgets.VBox(
            [level_title, level_ms],
            layout=widgets.Layout(width="20%", padding="0 0 0 10px")
        ),
        widgets.VBox(
            [param_title, param_ms],
            layout=widgets.Layout(width="80%", padding="0 10px 0 0")
        ),
    ],
    layout=widgets.Layout(width= '80%')
)

file_controls = widgets.HBox(
    [
             format_dd, fc,
    ],
)
file_controls.layout.display = 'flex'
file_controls.layout.justify_content = 'space-between'
file_controls.layout.align_items = 'center'
#file_controls.layout.height = '100px'
file_controls.layout.width = '80%'



# -- assemble ui
ui = widgets.VBox(
    [
        widgets.HTML("<b>Archive version:</b> "),
        version_dd,
        out,
        select_para_level_type,
        select_para_level,
        widgets.HTML("\n\n<b>Time-steps:</b>"),
        time_slider,
        file_controls,
        button_cont, # for compute button
        out_log,
        out_request,
    ],
    layout=main_layout
)

def main_loop():
    update_file() # start of options

    version_dd.observe(update_file, names='value')
    lt_dd.observe(update_levels, names='value')
    paratype_dd.observe(update_paras, names='value')
    param_ms.observe(update_time_steps, names='value')
    level_ms.observe(check_request_doable, names='value')
    time_slider.observe(check_request_doable, names='value')

    compute_button.on_click(create_request)
    download_button.on_click(download_request)


    display(ui)
