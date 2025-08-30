# Standard library imports
import os
import sys
import time
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, PhotoImage
from tkinter import ttk
from tkinter.ttk import Separator

# Third-party imports
import pandas as pd
from PIL import Image, ImageTk

# Project-specific imports
from config.gui_config import configure_window, center_window
from database import get_connector, get_db_path
from gui.functions.admdash_f.ML.add_items import add_item
from gui.functions.admdash_f.ML.delete_items import delete_item
from gui.functions.admdash_f.ML.search_bar import search_items, select_suggestion
from gui.functions.admdash_f.ML.stats_pnl import add_stats_panel, update_stats
from gui.functions.admdash_f.ML.update_items import UpdateItemsWindow
from gui.functions.admdash_f.ML.view_items_treeview import (
    view_items_treeview, DEFAULT_COLUMNS, DEFAULT_COLUMN_WIDTHS, NUMERIC_COLUMNS, CENTERED_COLUMNS
)
from gui.functions.admdash_f.Logs.vw_logs import (
    view_logs, view_admin_logs, clear_admin_logs, clear_employee_logs
)
from gui.functions.admdash_f.integrated_adm_sett import IntegratedAdminSettings
from gui.functions.admdash_f.bttn_tgl import (
    hide_main_buttons, show_main_buttons, show_export_buttons,
    show_delete_log_button, hide_delete_log_button
)
from gui.functions.admdash_f.checkbox_treeview import CheckboxTreeview
from gui.functions.admdash_f.error_handling import show_error
from gui.functions.admdash_f.export_func import export_to_xlsx, export_to_csv
from gui.functions.admdash_f.tab_buttons import create_tab_buttons
from gui.functions.admdash_f.table_utils import (
    reset_table_columns, clear_table, load_data, create_items_table, create_logs_table
)
from gui.functions.admdash_f.tooltip_utils import add_tooltips
from gui.functions.admdash_f.vrl import load_restock_list
from gui.functions.style.admscrl import configure_custom_scrollbar
from utils.window_icon import set_window_icon
from gui.functions.admdash_f.tfas.admin_2fa import Admin2FA