# *********************************************************************************************
#
#    model.py
# ----------------
# Uwe Berger; 2025
#
# Datenbankzugriffe für web_smartctl
#
#
# DB (sqlite|mariadb): smartctl.db ==> smartctl-history
# =====================================================
# Tabelle: drive_info
# -------------------
#    create table if not exists drive_info (
#        computer varchar(100) not null,
#        device_name varchar(100) not null,
#        generation int not null default 1,
#        data json,
#        created_at datetime default 0,
#        primary key (computer, device_name, generation)
#    )
#
# Tabelle: drive_data
# -------------------
#    create table if not exists drive_data (
#        computer varchar(100) not null,
#        device_name varchar(100) not null,
#        generation int not null default 1,
#        created_at datetime default 0,
#        data_device_brief_overview json,
#        data_device_detail json,
#        primary key (computer, device_name, generation, created_at)
#    )
#
#
#
# DB (sqlite): smart_attribute.db ==> Hover-Texte
# ===============================================
# Tabelle: smart_attribute_description
# ------------------------------------
#create table if not exists smart_attribute_description (
#    id int not null,
#    description_de text default "",
#    primary key (id)
#    )
#
# Tabelle: smart_attribute_name
# -----------------------------
#create table if not exists smart_attribute_name (
#    name varchar(200),
#    id int not null,
#    primary key (name)
#    )
#
#
#
# ---------
# Have fun!
#
# *********************************************************************************************

import web

# welche DB wird benutzt (sqlite|mariadb|mysql)
db_type = "sqlite"
# entsprechende DB öffnen
if db_type == "sqlite":
    db = web.database(dbn="sqlite", db="smartctl.db")
    sql_json_cmd = "json_extract"
elif db_type in ["mariadb", "mysql"]:
    db = web.database(dbn="mysql", host="nanotuxedo", db="drive_control", user="xxx", pw="yyy")
    sql_json_cmd = "json_value"
elif True:
    db = web.database(dbn="sqlite", db="../db/smartctl.db")
    sql_json_cmd = "json_extract"

# Hover-Texte Attribute
try:
    db_attr = web.database(dbn="sqlite", db="smart_attribute.db")
except:
    pass

# ***********************************************************************************
def get_hover(key):
    try:
        sql = f"""
            SELECT sn.name, sd.description_de 
            FROM smart_attribute_name sn 
            JOIN smart_attribute_description sd ON sn.id = sd.id 
            WHERE sn.name = '{key}';
        """
        rows = list(db_attr.query(sql))
    except:
        rows = []
    if len(rows):
        hover_txt = rows[0]["description_de"]
        return f'<span title="{hover_txt}">{key}</span>'
    else:
        return key

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
    sql = f"""
        SELECT 
            i.computer as computer,
            i.device_name as device_name,
            i.generation as generation,
            i.created_at AS device_created_at,
            d.created_at AS last_device_data,
            {sql_json_cmd}(d.data_device_brief_overview, '$.smartctl.exit_status') as smartctl_exit_status,
            {sql_json_cmd}(d.data_device_brief_overview, '$.temperature.current') as temperature,
            {sql_json_cmd}(d.data_device_brief_overview, '$.power_cycle_count') as power_cycle_count,
            {sql_json_cmd}(d.data_device_brief_overview, '$.power_on_time.hours') as power_on_time
        FROM drive_info i
        LEFT JOIN drive_data d
            ON d.computer = i.computer
            AND d.device_name = i.device_name
            AND d.generation = i.generation
            AND d.created_at = (
                SELECT MAX(created_at)
                FROM drive_data
                WHERE computer = i.computer
                AND device_name = i.device_name
                AND generation = i.generation
            )
        ORDER BY i.computer, i.device_name;
    """
    return list(db.query(sql))

# ***********************************************************************
def get_time_serie(computer, device_name, generation, table, table_column, json_path):
    sql = f"""
        select created_at as 'timestamp', {sql_json_cmd}({table_column}, '$.{json_path}') as 'value'
        from {table}
        where computer='{computer}' and device_name = '{device_name}' and generation = {generation}
    """
    return list(db.query(sql))
