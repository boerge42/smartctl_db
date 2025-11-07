# *********************************************************************************************
#
#    utils.py
# ----------------
# Uwe Berger; 2025
#
# Helfer für web_smartctl 
#
# ---------
# Have fun!
#
# *********************************************************************************************

import json

# *******************************************************
# Formatdefinitionen für smartctl-Tabelle (xxx_smart_attributes)
# ==>> path : {th: tab_head, len: output_len, view: output?, as_link: html_link}
tab_mask_def = {
    "id":                   {'th': 'id',          'len': 3,  'view': True,  'as_link' : False},
    "name":                 {'th': 'name',        'len': 25, 'view': True,  'as_link' : False},
    "value":                {'th': 'value',       'len': 5,  'view': True,  'as_link' : True},
    "worst":                {'th': 'worst',       'len': 5,  'view': True,  'as_link' : True},
    "thresh":               {'th': 'thresh',      'len': 6,  'view': True,  'as_link' : True},
    "when_failed":          {'th': 'when_failed', 'len': 11, 'view': True,  'as_link' : False},
    "flags.value":          {'th': 'flag_value',  'len': 10, 'view': False, 'as_link' : False},
    "flags.string":         {'th': 'flag_str',    'len': 8,  'view': False, 'as_link' : False},
    "flags.prefailure":     {'th': 'prefailure',  'len': 10, 'view': True,  'as_link' : False},
    "flags.updated_online": {'th': 'upd_online',  'len': 10, 'view': True,  'as_link' : False},
    "flags.performance":    {'th': 'performance', 'len': 11, 'view': True,  'as_link' : False},
    "flags.error_rate":     {'th': 'error_rate',  'len': 10, 'view': True,  'as_link' : False},
    "flags.event_count":    {'th': 'event_count', 'len': 11, 'view': True,  'as_link' : False},
    "flags.auto_keep":      {'th': 'auto_keep',   'len': 9,  'view': True,  'as_link' : False},
    "raw.value":            {'th': 'raw',         'len': 15, 'view': True,  'as_link' : True},
    "raw.string":           {'th': 'raw_str',     'len': 20, 'view': True,  'as_link' : False},
}


# **********************************++++++++******************************
def get_nested_value(data, path, sep='.', default=None):
    for key in path.split(sep):
        if isinstance(data, dict) and key in data:
            data = data[key]
        else:
            return default
    return data

# ***********************************************************************
def json_loads(json_str):
    return(json.loads(json_str))

# ***********************************************************************************
def get_value_as_link (json_path, value, link_params):
    return f'<a href="/graph/?json_path={json_path}&{link_params}">{value}</a>'

# ***********************************************************************************
def get_json_path (json_path, json_key):
    # den momentanen JSON-Weg in einem String abbilden
    if (len(json_path) > 0) or (len(json_key) > 0) :
        # wenn key ein Integer, dann ist es der Index des vorherigen Elementes
        if len(json_path) > 0:
            if isinstance(json_key, (int)):
                json_path = f"{json_path}[{json_key}]"
            else:
                json_path = f"{json_path}.{json_key}"
        elif len(json_key) > 0:
            json_path = json_key
            
    return json_path

# ***********************************************************************************
def json_to_ascii(data, space_len, r, th, json_path, json_key, link_params):

    json_path = get_json_path(json_path, json_key)

    max_str_len = 60    # etwas magic ;-)
   
    for key, value in data.items():
        spaces=" "*space_len

        if isinstance(value, dict):
            # weiter rekursiv "abtauschen", da noch ein dict
            r = F"{r}{key}:\n"
            r = json_to_ascii(value, space_len+int(len(key)), r, th, json_path, key, link_params)
        elif isinstance(value, list):
            # ab hier wird eine Liste (auch mit den evtl. weiteren Strukturen) zeilenweise als Tabelle ausgegeben
            r = f"{r}{spaces}{key}:\n"
            json_path = get_json_path(json_path, key)
            spaces=" " * (len(spaces) + int(len(key)))
            for i, item in enumerate(value):
                r = json_to_ascii_vertical(item, r, th, space_len + int(len(key)), json_path, i, link_params)
                th = False
                r = f"{r}\n"
        else:
            # einzelner Wert, also entsprechend ausgeben
            dyn_spaces = "."*(max_str_len - len(key) - space_len)
            if isinstance(value, str):
                # nur den Wert
                r = F"{r}{spaces}{key}:{dyn_spaces}{value}\n"
            elif isinstance(value, (int, float)):
                # Wert als HTML-Link
                r = F"{r}{spaces}{key}:{dyn_spaces}{get_value_as_link(get_json_path(json_path, key), value, link_params)}\n"

    return r

# ***********************************************************************************
def json_to_ascii_vertical(data, r, th, space_len, json_path, json_key, link_params):

    json_path = get_json_path(json_path, json_key)
    spaces = ""
       
    # ggf. Tabellenkopf ausgeben
    if th == True:
        r = f"{r}\n{spaces}"
        for c in tab_mask_def.items():
            if c[1]['view']:
                r = f"{r}{c[1]['th'].center(c[1]['len'])} "
        r = f"{r}\n"
    else:
        spaces = " "*space_len
    
    if isinstance (data, (int, float)):
        # data ist nur noch ein numerischer Wert aus der aufrufenden Procedure, also einfach ausgeben
        r = f"{r}{spaces}{get_value_as_link(json_path, data, link_params)}"
    elif isinstance (data, (str)):
        # ...dito String-Wert
        r = f"{r}{spaces}{data}"

    elif isinstance (data, dict):
        # wenn data ein dict ist, dann "vertikal" in der Reihenfolge von tab_mask_defs auslesen/ausgeben
        for c in tab_mask_def.items():
            if c[1]['view']:
                value = get_nested_value(data, c[0])
                if isinstance(value, str) or (value is None) or (c[1]['as_link'] == False):
                    # Wert nicht als HTML-Link ausgeben
                    r = f"{r}{str(value).rjust(c[1]['len'])} "
                    # Wert als Link ausgeben 
                elif isinstance(value, (int, float)):      
                    r = f"{r}{get_value_as_link(get_json_path(json_path, c[0]), str(value).rjust(c[1]['len']), link_params)} "
    return r
