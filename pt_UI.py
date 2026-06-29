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
file_options = [x for x,values in uad.items() if 'json' in values['metadata']]

# -- helper for level type
lt_dict = dict(sfc='surface', pl='pressure level', hl='height level', ml='model level')

# -- empty request and file metadata
file_meta = dict(json_file = '', expver = '', collection = '', georef='',
        address='', ts_present=False, timespan='')
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
        data1 = json.load(f)

    lt_dd.options=['sfc'] # -- reset to surface every time a new archive is picked
    lt_dd.value='sfc'
    update_lto(data1)

def update_lto(data1):
    lt = data1["level_type"]
    lt_dd.options=[(lt_dict[x], x) for x in lt.keys()]

    def update_ui(*args):
        lt_val = lt_dd.value
        paratype_val = paratype_dd.value
        # -- read para_codes for names and units
        para_options = [( para_codes[x]['shortName']+':   ' + para_codes[x]['name'] + ' [' + para_codes[x]['units'] + ']', int(x))
                        if x in available_para
                        else (x + ' -- missing info--', int(x))
                        for x in list(lt[lt_val]['para_type'][paratype_val]['param'])]
        param_ms.options = para_options
        times_now = lt[lt_val]['para_type'][paratype_val]["time_steps"]

# TODO: needs to be revised for the case when the same parameter has multiple timespan values
        file_meta['timespan'] = lt[lt_val]['para_type'][paratype_val]["time_span"]
        level_opts = lt[lt_val]['levels']

        if not para_options:
            time_slider.options = (' ',)
            time_slider.disabled = True
            compute_button.disabled = True
            level_ms.options = []

        else:
            level_ms.options = level_opts
            time_slider.options = times_now
            # time_slider.index = (0, len(times_now) - 1)
            time_slider.disabled = False
            compute_button.disabled = False


    update_ui()

    lt_dd.observe(update_ui, names='value')
    paratype_dd.observe(update_ui, names='value')


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

        if (not param_ms.value or (not level_ms.value  and lt_dd.value != 'sfc')):
            print(f" \t WARNING : empty parameters or levels\n")

        if (paratype_dd.value == 'cumul' and time_list[0] == '0'):
            print(f" \t WARNING : cumul paratype contains time-step 0\n")

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
        out_request,
        out_log
    ],
    layout=main_layout
)

def main_loop():
    update_file()
    version_dd.observe(update_file, names='value')
    compute_button.on_click(create_request)
    download_button.on_click(download_request)

    display(ui)
