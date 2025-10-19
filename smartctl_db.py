# ***********************************************************************************
#                               smartctl_db.py
#                             ==================
#                              Uwe Berger, 2025
#
# smartctl-Ausgaben (json-Format; Schalter -j) für übergebene Drives auslesen und
# in einer entsp. Datenbank protokollieren.
#
# ---------
# Have fun!
#
# ***********************************************************************************
# Übergabeparameter (Script):
# ---------------------------
# Die zu prokollierenden Drives sind in einer Textdatei hinterlegt, deren Name als
# (einziges) Parameter dem Script zu übergeben ist. Das Format der Textdatei sieht
# wie folgt aus:
# Jede Zeile ein Drive mit folgenden Angaben (Beispiel):
# /dev/sda, nvme
#     |      |
#     |      Drive-Typ (smartctl-Option -d ...)
#     Drive-Name
#
# Hilfreich sind dazu u.a. folgende Kommandos (RTFM...):
#   > smartctl --scan
#   > diskutil list     (MacOS)
#
#
# ***********************************************************************************
# Exit-Codes smartctl:
# --------------------
# Im Exit-Status von smartctl sind einige interessante Ergebnisse über den
# Zustand der Festplatte "verborgen", welche ggf. ebenfalls ausgewertet und/oder
# protokolliert werden sollten (siehe auch man-Page von smartctl):
#
# Bit 0: Command line did not parse.
#
# Bit 1: Device open failed, device did not return an IDENTIFY DEVICE structure, or 
#        device is in a low-power mode (see '-n' option above).
#
# Bit 2: Some SMART or other ATA command to the disk failed, or there was a checksum
#        error in a SMART data structure (see '-b' option above).
#
# Bit 3: SMART status check returned "DISK FAILING".
#
# Bit 4: We found prefail Attributes <= threshold.
#
# Bit 5: SMART status check returned "DISK OK" but we found that some (usage or prefail)
#        Attributes have been <= threshold at some time in the past.
#
# Bit 6: The device error log contains records of errors.
#
# Bit 7: The device self-test log contains records of errors. 
#        [ATA only] Failed self-tests outdated by a newer successful extended self-test
#         are ignored.
#
#
# ***********************************************************************************
# Voraussetzungen:
# ----------------
# smartctl, Version > xxx; wg. Option -j
# pip3 install mysql.connect (--break-system-packages)
# 
#
# ***********************************************************************************
# ToDo:
# -----
#   * Error-Code von smartctl nochmal genauer ansehen und evtl. verarbeiten
#   * get_json_drive_details kann entfallen; einfach eine Liste aller Keys...
#   * Komprimierung json in Tabellenspalten
#
#
# ***********************************************************************************
import subprocess
import platform
import json
import sys
from datetime import datetime

# ***********************************************************************************
# je nach DB-Type entsp. Modul einbinden und DB-Connection öffnen
# --> sqlite|mariadb|
db_type = "mariadb"
if db_type == "sqlite":
    import sqlite3
    connect_data = "smartctl.db"
    conn = sqlite3.connect(connect_data)
elif db_type == "mariadb":
    import mysql.connector
    conn = mysql.connector.connect(
                    host='nanotuxedo',
                    user='xxxx',
                    password='yyyy',
                    database='drive_control',
                    connection_timeout=10
                )
else:
    print("Kein sinnvoller DB-Typ angegeben!")
    exit(1)

# ***********************************************************************************
# je nach Betriebssystem den Aufruf von smartctl festlegen
system = platform.system()
#print(system)
if system == "Windows":
    smartctl_cmd = "c:/tools/smartctl/bin/smartctl.exe"
elif system == "Linux":
    smartctl_cmd = "smartctl"
elif system == "Darwin":
    smartctl_cmd = "smartctl"
elif True:
    smartctl_cmd = "smartctl"

# ***********************************************************************************
create_table_drive_info_str =  """
    create table if not exists drive_info (
        computer varchar(100) not null,
        device_name varchar(100) not null,
        generation int not null default 1,
        data json,
        created_at datetime default 0,
        primary key (computer, device_name, generation)
    )
"""

# ***********************************************************************************
create_table_drive_data_str = """
    create table if not exists drive_data (
        computer varchar(100) not null,
        device_name varchar(100) not null,
        generation int not null default 1,
        created_at datetime default 0,
        data_device_brief_overview json,
        data_device_detail json,
        primary key (computer, device_name, generation, created_at)
    )
"""

# ***********************************************************************************
# ...nicht alle sind bei den unterschiedlichen Device-Typen definiert!
drive_infos_keys = [
    "device",
    "model_family",
    "model_name",
    "serial_number",
    "firmware_version",
    "user_capacity",
    "form_factor",
    "rotation_rate",
]

# ***********************************************************************************
drive_brief_overview_keys = [
    "smart_status",
    "temperature",
    "power_cycle_count",
    "power_on_time",
    "smartctl",
]

# ***********************************************************************************
drive_detail_keys = [
    {"types":["nvme", "sntasmedia"],              "keys":[
                                                        "nvme_smart_health_information_log",
                                                    ]},
    {"types":["sat"],                             "keys":[
                                                        "ata_smart_attributes",
                                                    ]},
    {"types":["dummy"],                           "keys":[
                                                        "",
                                                    ]},

]

# ***********************************************************************************
def get_drive_cmds():
    try:
        drive_list = []
        if len(sys.argv) == 2:
            with open(sys.argv[1], "r") as file:
                for line in file:
                    line=line.strip()
                    line=line.replace(" ", "")
                    if len(line) > 0:
                        line=line.split(",")
                        l=[smartctl_cmd, "-a", "-j", line[0], "-d", line[1]]
                        drive_list.append(l)
    except Exception as e:
        print(f"Fehler in get_drive_cmds(): {e}")
    return drive_list

# ***********************************************************************************
def get_smartctl_exit_status(json_str):
    return json_str["smartctl"]["exit_status"]

# ***********************************************************************************
def get_smartctl_messages(json_str):
    return json_str["smartctl"]["messages"]

# ***********************************************************************************
def get_drive_type(json_str):
    return json_str["device"]["type"]

# ***********************************************************************************
def get_drive_name(json_str):
    return json_str["device"]["name"]

# ***********************************************************************************
def get_is_bit_set(v, b):
    if (v & (1<<b)):
        ret = True 
    else: 
        ret = False
    return ret

# ***********************************************************************************
def get_json(json_str, keys):
    new_json = {}
    for key in keys:
        if key in json_str:
            new_json[key] = json_str[key]
    return json.dumps(new_json, indent=2)

# ***********************************************************************************
def get_json_drive_details(json_str, drive_type, keys):
    new_json = {}
    for type_keys in keys:
        if drive_type in type_keys["types"]:
            new_json = get_json(json_str, type_keys["keys"])
            break
    return new_json

# ***********************************************************************************
def insert_into_db(json_str):
    
    cursor = conn.cursor()

    # eventuell Tabellen anlegen
    cursor.execute(create_table_drive_info_str)
    cursor.execute(create_table_drive_data_str)

    # Daten aus json etc. ermitteln
    computer = platform.node()
    device_name = get_drive_name(json_str)
    data_device_info = get_json(json_str, drive_infos_keys)
    data_device_brief_overview = get_json(json_str, drive_brief_overview_keys)
    data_drive_details = get_json_drive_details(json_str, get_drive_type(smartctl_out_json), drive_detail_keys)
    created_at = datetime.now()

    # DB-Inserts...
    # ...wenn sich die feststehenden data_device_infos zu einer bestimmten Platte geändert haben (Plattentausch), 
    # dann einen neuen Datensatz in Tabelle device_info mit neuer "generation" einfügen
    sql = f"select count(*) from drive_info where computer='{computer}' and device_name='{device_name}' and data='{data_device_info}'"
    cursor.execute(sql)
    existing_count,  = cursor.fetchone()
    sql = f"select ifnull(max(generation), 0) from drive_info where computer='{computer}' and device_name='{device_name}'"
    cursor.execute(sql)
    generation,  = cursor.fetchone()
    if existing_count == 0:
        generation = generation + 1
        sql = f"insert into drive_info values ('{computer}', '{device_name}', {generation}, '{data_device_info}', '{created_at}')"
        cursor.execute(sql)

    # ...zu aktuellem device die weiteren (veränderlichen) Daten in Tabelle drive_data protokollieren
    sql = f"insert into drive_data values ('{computer}', '{device_name}', {generation}, '{created_at}', '{data_device_brief_overview}', '{data_drive_details}')"
    cursor.execute(sql)


# ***********************************************************************************
# ***********************************************************************************
# ***********************************************************************************

# Drive-Liste einlesen
drives_cmds = get_drive_cmds()
if len(drives_cmds) == 0:
    print("Keine, mehr als eine und/oder leere Drive-Liste übergeben!")
    exit(1)

# für jedes Drive...
for cmd in drives_cmds:
    
    # wenn Bit 1 vom Error-Code smartctl gesetzt, dann ein zweites Mal probieren, 
    # da Drive u.U. erst aufgeweckt werden muss...
    exec_count = 0
    while exec_count < 2:
        result = subprocess.run(cmd, capture_output=True, text=True)
        smartctl_out_json = json.loads(result.stdout)
        if get_is_bit_set(get_smartctl_exit_status(smartctl_out_json), 1) != True:
            break
        exec_count = exec_count + 1

    # wenn 0.Bit des Exit-Status nicht gesetzt ist, Daten in DB protokollieren
    if get_is_bit_set(get_smartctl_exit_status(smartctl_out_json), 0) != True:
        try:
            insert_into_db(smartctl_out_json)
        except Exception as e:
            # ...eventuell detailiertere Fehlermeldung...
            print(f"Fehler in insert_into_db(): {e}")
            exit(1)
    else:
        print(f"Fehler bei {cmd}")
        # detailierte Fehlermeldungen (smartctl) auflisten...
        print("Exitcode (smartctl): ", get_smartctl_exit_status(smartctl_out_json))
        for m in get_smartctl_messages(smartctl_out_json):
            print(m["string"])

# DB commit/schliessen
conn.commit()
conn.close()
