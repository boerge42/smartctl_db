# *********************************************************************************************
#
#    model.py
# ----------------
# Uwe Berger; 2025
#
# Datenbankzugriffe für web_smartctl
#
# ---------
# Have fun!
#
# *********************************************************************************************

import web

# welche DB wird benutzt (sqlite|mariadb|mysql)
db_type = "mariadb"
# entsprechende DB öffnen
if db_type == "sqlite":
    db = web.database(dbn="sqlite", db="../db/smartctl.db")
    sql_json_cmd = "json_extract"
elif db_type in ["mariadb", "mysql"]:
    db = web.database(dbn="mysql", host="nanotuxedo", db="drive_control", user="xxxx", pw="yyyy")
    sql_json_cmd = "json_value"
elif True:
    db = web.database(dbn="sqlite", db="../db/smartctl.db")
    sql_json_cmd = "json_extract"

# ***********************************************************************************
def get_device_type (computer, device_name, generation):
    sql = f"""
        select {sql_json_cmd}(data, '$.device.type') as 'device_type'
        from drive_info
        where computer='{computer}' and device_name = '{device_name}' and generation = {generation}
    """    
    rows = list(db.query(sql))
    return rows[0]["device_type"]

# ***********************************************************************
def get_device_info(computer, device_name, generation):
    sql = f"""
        SELECT data, created_at FROM drive_info
        where computer='{computer}' and device_name = '{device_name}' and generation = {generation}
        ORDER BY created_at DESC
        LIMIT 1
    """
    rows = list(db.query(sql))
    return rows[0]

# ***********************************************************************
def get_device_data(computer, device_name, generation):
    sql = f"""
        SELECT data_device_brief_overview, data_device_detail, created_at FROM drive_data
        where computer='{computer}' and device_name = '{device_name}' and generation = {generation}
        ORDER BY created_at DESC
        LIMIT 1
    """
    rows = list(db.query(sql))
    return rows[0]

# ***********************************************************************
def get_all_devices():
    # select computer, device_name, generation, created_at from drive_info;
    return list(db.select("drive_info", what="computer, device_name, generation, created_at"))

# ***********************************************************************
def get_time_serie(computer, device_name, generation, table, table_column, json_path):
    sql = f"""
        select created_at as 'timestamp', {sql_json_cmd}({table_column}, '$.{json_path}') as 'value'
        from {table}
        where computer='{computer}' and device_name = '{device_name}' and generation = {generation}
    """
    return list(db.query(sql))
