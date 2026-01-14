# *********************************************************************************************
#
#            smart_attribute_edit.py
# -----------------------------------------------
# Uwe Berger; 2026 (vibe coding via copilot.com!)
#
# Editor fuer die sqliteDB, welche die Hover-Texte der SMART-Attribute beinhaltet.
#
# ---------
# Have fun!
#
# *********************************************************************************************

import sys
import sqlite3
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QTextEdit, QLabel, QTreeWidget, QTreeWidgetItem,
    QMessageBox, QFrame
)
from PyQt5.QtCore import Qt

DB_FILE = "smart_attribute.db"

SCHEMA_DESCRIPTION = """
CREATE TABLE IF NOT EXISTS smart_attribute_description (
    id INTEGER NOT NULL PRIMARY KEY,
    description_de TEXT DEFAULT ""
);
"""

SCHEMA_NAME = """
CREATE TABLE IF NOT EXISTS smart_attribute_name (
    name VARCHAR(200) NOT NULL PRIMARY KEY,
    id INTEGER NOT NULL
);
"""


class SmartEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SMART-Attribute Editor (Tree links, Eingaben rechts, Buttons unten)")
        self.conn = sqlite3.connect(DB_FILE)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()

        central = QWidget()
        main_layout = QVBoxLayout(central)   # Hauptlayout vertikal

        # Oberer Bereich: Tree links, Eingaben rechts
        top_layout = QHBoxLayout()

        # TreeWidget links
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["ID", "Beschreibung / Name"])
        self.tree.setEditTriggers(QTreeWidget.DoubleClicked | QTreeWidget.SelectedClicked)
        top_layout.addWidget(self.tree, 2)

        # Rechter Bereich mit Eingaben
        right_layout = QVBoxLayout()

        # Frame für Beschreibung
        desc_frame = QFrame()
        desc_frame.setFrameShape(QFrame.StyledPanel)
        desc_layout = QVBoxLayout(desc_frame)
        self.desc_id_edit = QLineEdit()
        self.desc_text_edit = QTextEdit()
        btn_add_desc = QPushButton("Beschreibung hinzufügen/aktualisieren")
        desc_layout.addWidget(QLabel("ID"))
        desc_layout.addWidget(self.desc_id_edit)
        desc_layout.addWidget(QLabel("Beschreibung"))
        desc_layout.addWidget(self.desc_text_edit)
        desc_layout.addWidget(btn_add_desc)
        right_layout.addWidget(desc_frame)

        # Frame für Name
        name_frame = QFrame()
        name_frame.setFrameShape(QFrame.StyledPanel)
        name_layout = QVBoxLayout(name_frame)
        self.name_id_edit = QLineEdit()
        self.name_text_edit = QLineEdit()
        btn_add_name = QPushButton("Name hinzufügen/aktualisieren")
        name_layout.addWidget(QLabel("ID (Referenz)"))
        name_layout.addWidget(self.name_id_edit)
        name_layout.addWidget(QLabel("Name"))
        name_layout.addWidget(self.name_text_edit)
        name_layout.addWidget(btn_add_name)
        right_layout.addWidget(name_frame)

        top_layout.addLayout(right_layout, 1)
        main_layout.addLayout(top_layout)

        # Unterer Bereich: Buttons über volle Breite in einem Frame
        bottom_frame = QFrame()
        bottom_frame.setFrameShape(QFrame.StyledPanel)
        bottom_layout = QHBoxLayout(bottom_frame)
        btn_delete = QPushButton("Ausgewähltes löschen")
        btn_refresh = QPushButton("Refresh")
        btn_exit = QPushButton("Beenden")
        bottom_layout.addWidget(btn_delete)
        bottom_layout.addWidget(btn_refresh)
        bottom_layout.addStretch(1)
        bottom_layout.addWidget(btn_exit)
        main_layout.addWidget(bottom_frame)

        self.setCentralWidget(central)

        # Signale
        btn_add_desc.clicked.connect(self.add_or_update_description)
        btn_add_name.clicked.connect(self.add_or_update_name)
        btn_delete.clicked.connect(self.delete_selected)
        btn_refresh.clicked.connect(self.load_tree)
        btn_exit.clicked.connect(QApplication.quit)
        self.tree.itemChanged.connect(self.update_item_in_db)
        self.tree.itemSelectionChanged.connect(self.on_item_selected)

        self.load_tree()

    def _ensure_schema(self):
        cur = self.conn.cursor()
        cur.execute(SCHEMA_DESCRIPTION)
        cur.execute(SCHEMA_NAME)
        self.conn.commit()

    def add_or_update_description(self):
        id_val = self.desc_id_edit.text().strip()
        desc_val = self.desc_text_edit.toPlainText().strip()
        if not id_val:
            QMessageBox.warning(self, "Fehler", "ID darf nicht leer sein!")
            return
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO smart_attribute_description (id, description_de) VALUES (?, ?) "
            "ON CONFLICT(id) DO UPDATE SET description_de=excluded.description_de",
            (id_val, desc_val)
        )
        self.conn.commit()
        self.load_tree()

    def add_or_update_name(self):
        id_val = self.name_id_edit.text().strip()
        name_val = self.name_text_edit.text().strip()
        if not id_val or not name_val:
            QMessageBox.warning(self, "Fehler", "ID und Name dürfen nicht leer sein!")
            return
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO smart_attribute_name (name, id) VALUES (?, ?) "
            "ON CONFLICT(name) DO UPDATE SET id=excluded.id",
            (name_val, id_val)
        )
        self.conn.commit()
        self.load_tree()

    def load_tree(self):
        self.tree.clear()
        cur = self.conn.cursor()

        cur.execute("SELECT id, description_de FROM smart_attribute_description ORDER BY id")
        descriptions = cur.fetchall()

        id_to_item = {}
        for desc in descriptions:
            full_desc = desc["description_de"] or ""
            first_line = full_desc.splitlines()[0] if full_desc else ""
            top = QTreeWidgetItem([str(desc["id"]), first_line])
            top.setFlags(top.flags() | Qt.ItemIsEditable)
            self.tree.addTopLevelItem(top)
            id_to_item[desc["id"]] = top

        cur.execute("SELECT name, id FROM smart_attribute_name ORDER BY id, name")
        names = cur.fetchall()

        orphans = []
        for n in names:
            parent = id_to_item.get(n["id"])
            if parent:
                child = QTreeWidgetItem(["", n["name"]])
                child.setFlags(child.flags() | Qt.ItemIsEditable)
                parent.addChild(child)
            else:
                orphans.append(n)

        if orphans:
            orphan_root = QTreeWidgetItem(["", "(Verwaiste Namen – keine Beschreibung vorhanden)"])
            orphan_root.setFlags(orphan_root.flags() & ~Qt.ItemIsEditable)
            self.tree.addTopLevelItem(orphan_root)
            for n in orphans:
                child = QTreeWidgetItem([str(n["id"]), n["name"]])
                child.setFlags(child.flags() | Qt.ItemIsEditable)
                orphan_root.addChild(child)

        self.tree.expandAll()

    def delete_selected(self):
        item = self.tree.currentItem()
        if not item:
            return
        parent = item.parent()
        cur = self.conn.cursor()

        if parent is None:
            id_val = item.text(0).strip()
            cur.execute("DELETE FROM smart_attribute_description WHERE id=?", (id_val,))
            cur.execute("DELETE FROM smart_attribute_name WHERE id=?", (id_val,))
        else:
            name_val = item.text(1).strip()
            id_val = parent.text(0).strip() or item.text(0).strip()
            cur.execute("DELETE FROM smart_attribute_name WHERE id=? AND name=?", (id_val, name_val))

        self.conn.commit()
        self.load_tree()

    def update_item_in_db(self, item, column):
        parent = item.parent()
        cur = self.conn.cursor()

        if parent is None and column == 1:
            id_val = item.text(0).strip()
            new_desc = item.text(1)
            cur.execute("UPDATE smart_attribute_description SET description_de=? WHERE id=?", (new_desc, id_val))
        elif parent is not None and column == 1:
            id_val = parent.text(0).strip() or item.text(0).strip()
            new_name = item.text(1).strip()
            cur.execute(
                "INSERT INTO smart_attribute_name (name, id) VALUES (?, ?) "
                "ON CONFLICT(name) DO UPDATE SET id=excluded.id",
                (new_name, id_val)
            )
        self.conn.commit()

    def on_item_selected(self):
        item = self.tree.currentItem()
        if not item:
            return
        parent = item.parent()

        if parent is None:
            # Beschreibung ausgewählt
            id_val = item.text(0).strip()
            cur = self.conn.cursor()
            cur.execute("SELECT description_de FROM smart_attribute_description WHERE id=?", (id_val,))
            row = cur.fetchone()
            desc_val = row["description_de"] if row else ""
            self.desc_id_edit.setText(id_val)
            self.desc_text_edit.setPlainText(desc_val)
            self.name_id_edit.setText(id_val)
            self.name_text_edit.clear()
        else:
            # Name ausgewählt
            id_val = parent.text(0).strip()
            name_val = item.text(1).strip()
            self.name_id_edit.setText(id_val)
            self.name_text_edit.setText(name_val)

            cur = self.conn.cursor()
            cur.execute("SELECT description_de FROM smart_attribute_description WHERE id=?", (id_val,))
            row = cur.fetchone()
            if row:
                self.desc_id_edit.setText(id_val)
                self.desc_text_edit.setPlainText(row["description_de"])
            else:
                self.desc_id_edit.setText(id_val)
                self.desc_text_edit.setPlainText("(keine Beschreibung vorhanden)")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SmartEditor()
    window.resize(1000, 600)
    window.show()
    sys.exit(app.exec_())
