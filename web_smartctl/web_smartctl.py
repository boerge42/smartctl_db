# *********************************************************************************************
#
#  web_smartctl.py
# -----------------
#  Uwe Berger; 2025
#
# web.py - main
#
# Web-Frontend zur smartctl-DB.
# (Zugriffsparameter zur DB sind in model.py zu finden und auch dort anzupassen.)
#
#
# ---------
# Have fun!
#
# *********************************************************************************************

import web
import model
import utils
import graphs


from web.template import ALLOWED_AST_NODES
ALLOWED_AST_NODES.append('Constant')


# define url mappings
urls = (
        "/", "Index",
        "/details/", "Details",
        "/graph/", "Graph",
    )


web.config.debug = False

# define Templates
render = web.template.render("templates", base="base")

app = web.application(urls, globals())

session = web.session.Session(app, web.session.DiskStore('sessions'))


# ***************************************************************
# Startseite mit allen Devices in DB als Tabelle
class Index:

	# ****************************
    def GET(self):
        devices = model.get_all_devices()
        # einen Spaltenwert konvertieren
        for i in range(0, len(devices)):
            if devices[i]['smartctl_exit_status'] is not None:
                devices[i]['smartctl_exit_status'] = f"0b{format(int(devices[i]['smartctl_exit_status']), '08b')}"
        return render.index(devices)

# ***************************************************************
# (letzte) smartclt-Informationen zu einem Device
class Details:

	# ****************************
    def GET(self):
        i = web.input(computer=None, device_name=None, generation=None)
        ret = model.get_device_info(i.computer, i.device_name, i.generation)
        link_params=f"computer={i.computer}&device_name={i.device_name}&generation={i.generation}&table=drive_info&table_column=data"
        tbl_info = utils.json_to_ascii(utils.json_loads(ret.data), 0, "", False, "", "", link_params)
        tbl_info = f"<code>{tbl_info}</code>"
        datetime_info = ret.created_at
        ret = model.get_device_data(i.computer, i.device_name, i.generation)
        link_params=f"computer={i.computer}&device_name={i.device_name}&generation={i.generation}&table=drive_data&table_column=data_device_brief_overview"
        tbl_brief = utils.json_to_ascii(utils.json_loads(ret.data_device_brief_overview), 0, "", False, "", "", link_params)
        tbl_brief = f"<code>{tbl_brief}</code>"
        link_params=f"computer={i.computer}&device_name={i.device_name}&generation={i.generation}&table=drive_data&table_column=data_device_detail"
        if model.get_device_type(i.computer, i.device_name, i.generation) in ["sat", "ata", "scsi"]:
            tbl_detail = utils.json_to_ascii(utils.json_loads(ret.data_device_detail), 0, "", True, "", "", link_params)
        else:
            tbl_detail = utils.json_to_ascii(utils.json_loads(ret.data_device_detail), 0, "", False, "", "", link_params)
        tbl_detail = f"<code>{tbl_detail}</code>"
        datetime_data = ret.created_at
        return render.details(tbl_info, tbl_brief, tbl_detail, i.computer, i.device_name, i.generation, datetime_info, datetime_data)

# ***************************************************************
# Linien-Diagram zu einer Messreihe
class Graph:

	# ****************************
    def GET(self):
        i = web.input(computer=None, device_name=None, generation=None, table=None, table_column=None, json_path=None, description=None)
        graph_data = model.get_time_serie(i.computer, i.device_name, i.generation, i.table, i.table_column, i.json_path)
        graph_div = graphs.generate_line_graph(graph_data, i.computer, i.device_name, i.generation, i.json_path, i.description)
        return render.graph(graph_div)

# ***************************************************************
# ***************************************************************
# ***************************************************************

if __name__ == "__main__":
    app.run()
