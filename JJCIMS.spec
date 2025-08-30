# -*- mode: python ; coding: utf-8 -*-

# Collect extra data/modules needed at build time (e.g., tkinterdnd2 TKDND assets)
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Database files
    # Legacy standalone employee DB removed; use database/JJCIMS.accdb as canonical DB
        ('database/JJCIMS.accdb', 'database'),
        ('database/logs.xlsx', 'database'),
        ('database/Backup', 'database/Backup'),

        # Configuration files
        ('gui/config/fernet_key.py', 'gui/config'),
        ('config/fernet_key.py', 'config'),
        ('config/admin_otp_secret.txt', 'config'),
        ('config/code_hashes.txt', 'config'),
        ('config/code_security.key', 'config'),
        ('config/backup_restore_status.json', 'config'),
        ('config/gui_config.py', 'config'),
        ('config/performance_config.py', 'config'),
        ('config/window_manager.py', 'config'),

        # Assets directory (all images and subdirectories)
        ('assets', 'assets'),
        ('assets/upi_assets', 'assets/upi_assets'),
        ('assets/ani_assets', 'assets/ani_assets'),
        ('assets/bnr_assets', 'assets/bnr_assets'),
        ('assets/bnr_assets/bu_assets', 'assets/bnr_assets/bu_assets'),
        ('assets/bnr_assets/r_assets', 'assets/bnr_assets/r_assets'),
        ('assets/tfa_su_assets', 'assets/tfa_su_assets'),
        ('assets/sett_assets', 'assets/sett_assets'),
        ('assets/Pw_rst_assets', 'assets/Pw_rst_assets'),
        ('assets/adm_sett_2fa_setup_assets', 'assets/adm_sett_2fa_setup_assets'),
        ('assets/adm_sett_2fa_setup_assets/step_1', 'assets/adm_sett_2fa_setup_assets/step_1'),
        ('assets/adm_sett_2fa_setup_assets/step_2', 'assets/adm_sett_2fa_setup_assets/step_2'),
        ('assets/adm_sett_2fa_setup_assets/step_3', 'assets/adm_sett_2fa_setup_assets/step_3'),
        ('assets/adm_sett_2fa_setup_assets/step_4', 'assets/adm_sett_2fa_setup_assets/step_4'),
        ('assets/adm_sett_2fa_setup_assets/step_5', 'assets/adm_sett_2fa_setup_assets/step_5'),

        # Icons directory (all icon files)
        ('icons', 'icons'),

        # Application icon files
        ('JJCIMS(2).ico', '.'),
        ('JJCIMS(2).png', '.'),

        # GUI modules and functions (entire directories)
        ('gui', 'gui'),
        ('gui/functions', 'gui/functions'),
        ('gui/config', 'gui/config'),
        ('utils', 'utils'),
        ('utils/assets', 'utils/assets'),
        ('utils/backups', 'utils/backups'),
        ('utils/config', 'utils/config'),
        ('utils/database', 'utils/database'),
        ('utils/gui', 'utils/gui'),
        ('utils/logs', 'utils/logs'),
        ('models', 'models'),
        ('config', 'config'),

        # Environment files
        ('env', 'env'),

        # Documentation and system files
        ('requirements.txt', '.'),
        ('INSTALLATION_GUIDE.txt', '.'),
        ('INTEGRATION_GUIDE.txt', '.'),
        ('version_info.txt', '.'),
    ] + collect_data_files('tkinterdnd2'),
    hiddenimports=[
        # Core dependencies
        'pyotp', 'qrcode', 'PIL', 'PIL.Image', 'PIL.ImageTk', 'cryptography', 'cryptography.fernet',
        'cryptography.hazmat.bindings._rust',
        
        # Extended tkinter imports
        'tkinter', 'tkinter.ttk', 'tkinter.messagebox', 'tkinter.font', 'tkinter.filedialog',
        'tkinter.commondialog',
        
        # Complete PIL imports 
        'PIL.ImageDraw', 'PIL.ImageFont', 'PIL.ImageEnhance', 'PIL.ImageFilter',
        
        # NumPy for image processing
        'numpy',
        
        # Excel and data handling
        'openpyxl', 'openpyxl.Workbook', 'openpyxl.load_workbook',
        'pandas', 'pandas.core.arrays.string_',
        
        # Database connectivity
        'pyodbc',
        
        # Standard library modules
        'datetime', 'pathlib', 'threading', 'time', 'decimal',
        'hashlib', 'json', 'collections', 'functools', 'random',
        
        # System and utilities
        'importlib.util', 'importlib.machinery',
        'shutil', 'sys', 'os',
        
        # Main GUI modules
        'gui', 'gui.admin_dashboard', 'gui.employee_dashboard', 'gui.admin_login', 
        'gui.employee_login', 'gui.loading_screen', 'gui.globals',
        
        # Admin dashboard core functions
        'gui.functions.admdash_f.admdash_imp',
        'gui.functions.admdash_f.bttn_tgl',
        'gui.functions.admdash_f.checkbox_treeview',
        'gui.functions.admdash_f.tab_buttons',
        'gui.functions.admdash_f.table_utils',
        'gui.functions.admdash_f.tooltip_utils',
        'gui.functions.admdash_f.user_roles_manager',
        'gui.functions.admdash_f.draft_manager',
        'gui.functions.admdash_f.integrated_adm_sett',
        
        # Material List (ML) functions
        'gui.functions.admdash_f.ML.add_items', 'gui.functions.admdash_f.ML.delete_items',
        'gui.functions.admdash_f.ML.search_bar', 'gui.functions.admdash_f.ML.stats_pnl',
        'gui.functions.admdash_f.ML.update_items', 'gui.functions.admdash_f.ML.view_items_treeview',
        
        # Logs functions
        'gui.functions.admdash_f.Logs.vw_logs',
        
        # View Restock List (VRL) functions
        'gui.functions.admdash_f.vrl',
        
        # Two-Factor Authentication
        'gui.functions.admdash_f.tfas.admin_2fa', 'gui.functions.admdash_f.tfas.setup_2fa_utils',
        
        # Style functions
        'gui.functions.style.admscrl',
        
        # Employee dashboard functions
        'gui.functions.emplydash_f.emplydash_imp', 'gui.functions.emplydash_f.emplydash_utils',
        'gui.functions.emplydash_f.checkout_win', 'gui.functions.emplydash_f.checkbox_treeview',
        'gui.functions.emplydash_f.utilities',
        
        # Database and backend
        'database.access_connector', 
        
        # Utility modules
        'utils.helpers', 'utils.image_effects', 'utils.code_security', 
        'utils.cache_manager', 'utils.image_manager', 'utils.image_optimizer',
        'utils.label_effects', 'utils.notification_manager', 'utils.window_icon',
        'utils.font_utils',
        
        # Configuration modules
        'config.gui_config', 'config.window_manager', 'config.fernet_key',
        'config.performance_config',
        
        # Model classes
        'models.item',
        
        # Packaging dependencies
        'pkg_resources', 'packaging', 'setuptools', 'jaraco.text', 'jaraco.functools', 'platformdirs',
        # Native drag-and-drop
        'tkinterdnd2'
    ] + collect_submodules('tkinterdnd2'),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=['hook_tkinterdnd2_runtime.py'],
    excludes=[],
    noarchive=False,
    optimize=1,  # Optimize Python bytecode
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='JJCIMS',  # Updated EXE name
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Disable UPX compression for better compatibility
    console=False,  # Enable console window to see errors
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='JJCIMS(2).ico',
    version='version_info.txt',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,  # Disable UPX compression for better compatibility
    upx_exclude=[],
    name='JJCIMS',  # Output folder inside workspace
)
