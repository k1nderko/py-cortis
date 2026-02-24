# -*- coding: utf-8 -*-
"""
Задание 2: Интерфейс списка пациентов (Python + PyQt).
Чтение из clientList (JSON), отображение при deleted != 1,
контекстное меню: «Сформировать выходную форму», «Удалить строку».
"""
import json
import os
import sys


def parse_fio(fio_str):
    """Разбивает ФИО на фамилию, имя, отчество. Возвращает (lastName, firstName, patrName)."""
    parts = (fio_str or '').strip().split()
    last = parts[0] if len(parts) > 0 else ''
    first = parts[1] if len(parts) > 1 else ''
    patr = parts[2] if len(parts) > 2 else ''
    return last, first, patr


def short_name(last_name, first_name, patr_name):
    """Фамилия И.О."""
    i = (first_name[:1] + '.') if first_name else ''
    o = (patr_name[:1] + '.') if patr_name else ''
    return f"{last_name} {i}{o}".strip()


try:
    from PyQt5.QtWidgets import (
        QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
        QMenu, QDialog, QVBoxLayout, QLabel, QDialogButtonBox,
        QHeaderView, QMessageBox, QAbstractItemView,
    )
    from PyQt5.QtCore import Qt
    HEADER_STRETCH = QHeaderView.Stretch
    SELECT_ROWS = QAbstractItemView.SelectRows
    SINGLE_SELECT = QAbstractItemView.SingleSelection
    CONTEXT_MENU = Qt.CustomContextMenu
    BTN_OK = QDialogButtonBox.Ok
except ImportError:
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QTableWidget, QTableWidgetItem,
        QMenu, QDialog, QVBoxLayout, QLabel, QDialogButtonBox,
        QHeaderView, QMessageBox, QAbstractItemView,
    )
    from PyQt6.QtCore import Qt
    HEADER_STRETCH = QHeaderView.ResizeMode.Stretch
    SELECT_ROWS = QAbstractItemView.SelectionBehavior.SelectRows
    SINGLE_SELECT = QAbstractItemView.SelectionMode.SingleSelection
    CONTEXT_MENU = Qt.ContextMenuPolicy.CustomContextMenu
    BTN_OK = QDialogButtonBox.StandardButton.Ok

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CLIENT_LIST_PATH = os.path.join(SCRIPT_DIR, 'clientList')


def load_clients():
    """Читает JSON из clientList, добавляет deleted=0 если нет."""
    path = CLIENT_LIST_PATH
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    if not isinstance(data, list):
        data = [data]
    for row in data:
        if 'deleted' not in row:
            row['deleted'] = 0
    return data


def save_clients(clients):
    """Сохраняет список в clientList."""
    with open(CLIENT_LIST_PATH, 'w', encoding='utf-8') as f:
        json.dump(clients, f, ensure_ascii=False, indent=2)


class OutputFormDialog(QDialog):
    """Выходная форма с данными о пациенте."""
    def __init__(self, client_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle('Выходная форма')
        self.setMinimumWidth(400)
        layout = QVBoxLayout(self)
        last, first, patr = parse_fio(client_data.get('fio', ''))
        short = short_name(last, first, patr)
        birth = client_data.get('birth_date', '')
        lines = [
            f"ФИО: {client_data.get('fio', '')}",
            f"Фамилия И.О.: {short}",
            f"Фамилия: {last}",
            f"Имя: {first}",
            f"Отчество: {patr}",
            f"Дата рождения: {birth}",
        ]
        for line in lines:
            layout.addWidget(QLabel(line))
        bbox = QDialogButtonBox(BTN_OK)
        bbox.accepted.connect(self.accept)
        layout.addWidget(bbox)


class PatientsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Список пациентов')
        self.clients = []
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(['ФИО', 'Фамилия И.О.', 'Дата рождения'])
        self.table.horizontalHeader().setSectionResizeMode(HEADER_STRETCH)
        self.table.setSelectionBehavior(SELECT_ROWS)
        self.table.setSelectionMode(SINGLE_SELECT)
        self.table.setContextMenuPolicy(CONTEXT_MENU)
        self.table.customContextMenuRequested.connect(self.show_context_menu)
        self.setCentralWidget(self.table)
        self.refresh_data()

    def refresh_data(self):
        self.clients = load_clients()
        visible = [c for c in self.clients if c.get('deleted', 0) != 1]
        self.table.setRowCount(len(visible))
        for i, c in enumerate(visible):
            last, first, patr = parse_fio(c.get('fio', ''))
            self.table.setItem(i, 0, QTableWidgetItem(c.get('fio', '')))
            self.table.setItem(i, 1, QTableWidgetItem(short_name(last, first, patr)))
            self.table.setItem(i, 2, QTableWidgetItem(c.get('birth_date', '')))
        self._visible = visible

    def _current_client_data(self):
        row = self.table.currentRow()
        if row < 0 or row >= len(self._visible):
            return None
        return self._visible[row]

    def _current_client_index_in_full(self):
        """Индекс выбранного пациента в полном списке self.clients."""
        cd = self._current_client_data()
        if not cd:
            return -1
        try:
            return self.clients.index(cd)
        except ValueError:
            return -1

    def show_context_menu(self, pos):
        row = self.table.rowAt(pos.y())
        if row < 0:
            return
        self.table.selectRow(row)
        menu = QMenu(self)
        act_form = menu.addAction('Сформировать выходную форму')
        act_del = menu.addAction('Удалить строку')
        exec_fn = getattr(menu, 'exec_', getattr(menu, 'exec', None))
        action = exec_fn(self.table.mapToGlobal(pos)) if exec_fn else None
        if action == act_form:
            self.show_output_form()
        elif action == act_del:
            self.delete_row()

    def show_output_form(self):
        cd = self._current_client_data()
        if not cd:
            QMessageBox.warning(self, 'Внимание', 'Выберите строку.')
            return
        dlg = OutputFormDialog(cd, self)
        getattr(dlg, 'exec_', getattr(dlg, 'exec'))()

    def delete_row(self):
        idx = self._current_client_index_in_full()
        if idx < 0:
            QMessageBox.warning(self, 'Внимание', 'Выберите строку.')
            return
        self.clients[idx]['deleted'] = 1
        save_clients(self.clients)
        self.refresh_data()


def main():
    app = QApplication(sys.argv)
    w = PatientsWindow()
    w.resize(700, 500)
    w.show()
    sys.exit(app.exec_() if hasattr(app, 'exec_') else app.exec())


if __name__ == '__main__':
    main()
