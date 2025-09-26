import json
from pathlib import Path

from PyQt5 import QtWidgets, QtCore, QtGui


class FolderListWidget(QtWidgets.QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)
        self.status_dict = {}
        self.highlight_color = QtGui.QColor(0, 120, 215, 180)
        self.current_item_name = None  # store name, not the QListWidgetItem

    # --- helper: get item by folder name (basename) ---
    def _find_item_by_name(self, name):
        for i in range(self.count()):
            it = self.item(i)
            if it.text().split()[0] == name:
                return it
        return None

    # --- státusz szerinti alap háttér ---
    def _apply_status_color(self, item):
        transparency = 125
        name = item.text().split()[0]
        status = self.status_dict.get(name)
        if status == "not_done":
            item.setBackground(QtGui.QColor(255, 0, 0, transparency))
        elif status == "in_progress":
            item.setBackground(QtGui.QColor(255, 255, 0, transparency))
        elif status == "done":
            item.setBackground(QtGui.QColor(0, 255, 0, transparency))
        else:
            item.setBackground(QtGui.QColor("#303436"))

    # --- státusz beállítása + visszaállítás rendszere ---
    def set_status(self, item, status_or_none):
        name = item.text().split()[0]
        self.status_dict[name] = status_or_none
        self._apply_status_color(item)
        # ha ez a jelenlegi név, tartsuk meg a kiemelést
        if self.current_item_name == name:
            item.setBackground(self.highlight_color)

    # --- kiemelés név alapján ---
    def highlight_by_name(self, name):
        # először alap státuszok visszaállítása
        for i in range(self.count()):
            self._apply_status_color(self.item(i))

        # keres és kiemel
        it = self._find_item_by_name(name)
        if it:
            it.setBackground(self.highlight_color)
            self.setCurrentItem(it)
            self.current_item_name = name
            self.scrollToItem(it)
        else:
            # ha nincs ilyen elem, töröljük a current nevet
            self.current_item_name = None
            self.setCurrentItem(None)

    # --- kattintás ---
    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        if event.button() == QtCore.Qt.LeftButton:
            item = self.itemAt(event.pos())
            if item:
                self.highlight_by_name(item.text().split()[0])

    # --- jobb klikk menü (rövidítve) ---
    def show_context_menu(self, pos):
        item = self.itemAt(pos)
        if not item:
            return

        menu = QtWidgets.QMenu(self)
        not_done = menu.addAction("Not Done")
        in_progress = menu.addAction("In Progress")
        done = menu.addAction("Done")
        remove = menu.addAction("Remove Status")
        delete_folder = menu.addAction("Delete Folder")

        action = menu.exec_(self.mapToGlobal(pos))

        if action == not_done:
            self.set_status(item, "not_done")
        elif action == in_progress:
            self.set_status(item, "in_progress")
        elif action == done:
            self.set_status(item, "done")
        elif action == remove:
            self.set_status(item, None)
        elif action == delete_folder:
            # ... törlés kód (ugyanaz mint korábban) ...
            pass


# -------- INNENTŐL MODEL HA MARAD ----------------
    # --- load_status_action (javított, nem használ érvénytelen item objektumokat) ---
    def load_status_action(self):
        main_folder = self.window().main_folder
        loaded_status_action = None

        if main_folder is not None:
            folder_path = Path(main_folder)
            load_path = folder_path / f"{folder_path.name}_status_action.json"

            if not load_path.exists():
                QtWidgets.QMessageBox.warning(self, "Hiba", f"A fájl nem található:\n{load_path}")
                return

            try:
                with load_path.open("r", encoding="utf-8") as f:
                    loaded_status_action = json.load(f)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Hiba", f"Nem sikerült betölteni:\n{e}")
                return

        return loaded_status_action


    def save_status_action(self):
        main_folder = self.window().main_folder
        if main_folder is not None:
            folder_path = Path(main_folder)
            save_path = folder_path / f"{folder_path.name}_status_action.json"

            try:
                with save_path.open("w", encoding="utf-8") as f:
                    json.dump(self.status_dict, f, indent=4, ensure_ascii=False)

                QtWidgets.QMessageBox.information(
                    self, "Siker", f"Státuszok elmentve ide:\n{save_path}"
                )
                self.window().change_info_label("Status Saved!")
            except Exception as e:
                QtWidgets.QMessageBox.critical(
                    self, "Hiba", f"Nem sikerült menteni:\n{e}"
                )