# -*- mode: python ; coding: utf-8 -*-

# Collect extra data/modules needed at build time (e.g., tkinterdnd2 TKDND assets)
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[
        # Database files
    # Legacy standalone employee DB removed; use backend/database/JJCIMS.accdb as canonical DB
        ('backend/database/JJCIMS.accdb', 'backend/database'),
        ('backend/database/Backup', 'backend/database/Backup'),

        # Configuration files
        ('backend/config/fernet_key.py', 'backend/config'),
        ('backend/config/admin_otp_secret.txt', 'backend/config'),
        ('backend/config/code_hashes.txt', 'backend/config'),
        ('backend/config/code_security.key', 'backend/config'),
        ('backend/config/backup_restore_status.json', 'backend/config'),
        ('backend/config/gui_config.py', 'backend/config'),
        ('backend/config/performance_config.py', 'backend/config'),
        ('backend/config/window_manager.py', 'backend/config'),

        # Assets directory (all images and subdirectories)
        ('frontend/assets', 'frontend/assets'),

        # Icons directory (all icon files)
        ('frontend/icons', 'frontend/icons'),

        # Application icon files
        ('JJCIMS(2).ico', '.'),
        ('JJCIMS(2).png', '.'),

        # GUI modules and functions (entire directories)
        ('frontend/gui', 'frontend/gui'),
        # Backend modules
        ('backend/utils', 'backend/utils'),
        ('backend/database', 'backend/database'),
        ('backend/config', 'backend/config'),

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
        'frontend.gui', 'frontend.gui.admin_dashboard', 'frontend.gui.employee_dashboard', 'frontend.gui.admin_login', 
        'frontend.gui.employee_login', 'frontend.gui.loading_screen', 'frontend.gui.globals',
        
        # Admin dashboard core functions
        'frontend.gui.functions.admdash_f.admdash_imp',
        'frontend.gui.functions.admdash_f.bttn_tgl',
        'frontend.gui.functions.admdash_f.checkbox_treeview',
        'frontend.gui.functions.admdash_f.tab_buttons',
        'frontend.gui.functions.admdash_f.table_utils',
        'frontend.gui.functions.admdash_f.tooltip_utils',
        'frontend.gui.functions.admdash_f.user_roles_manager',
        'frontend.gui.functions.admdash_f.draft_manager',
        'frontend.gui.functions.admdash_f.integrated_adm_sett',
        
        # Material List (ML) functions
        'frontend.gui.functions.admdash_f.ML.add_items', 'frontend.gui.functions.admdash_f.ML.delete_items',
        'frontend.gui.functions.admdash_f.ML.search_bar', 'frontend.gui.functions.admdash_f.ML.stats_pnl',
        'frontend.gui.functions.admdash_f.ML.update_items', 'frontend.gui.functions.admdash_f.ML.view_items_treeview',
        
        # Logs functions
        'frontend.gui.functions.admdash_f.Logs.vw_logs',
        
        # View Restock List (VRL) functions
        'frontend.gui.functions.admdash_f.vrl',
        
        # Two-Factor Authentication
        'frontend.gui.functions.admdash_f.tfas.admin_2fa', 'frontend.gui.functions.admdash_f.tfas.setup_2fa_utils',
        
        # Style functions
        'frontend.gui.functions.style.admscrl',
        
        # Employee dashboard functions
        'frontend.gui.functions.emplydash_f.emplydash_imp', 'frontend.gui.functions.emplydash_f.emplydash_utils',
        'frontend.gui.functions.emplydash_f.checkout_win', 'frontend.gui.functions.emplydash_f.checkbox_treeview',
        'frontend.gui.functions.emplydash_f.utilities',
        
        # Database and backend
        'backend.database.access_connector', 
        
        # Utility modules
        'backend.utils.helpers', 'backend.utils.image_effects', 'backend.utils.code_security', 
        'backend.utils.cache_manager', 'backend.utils.image_manager', 'backend.utils.image_optimizer',
        'backend.utils.label_effects', 'backend.utils.notification_manager', 'backend.utils.window_icon',
        'backend.utils.font_utils',
        
        # Configuration modules
        'backend.config.gui_config', 'backend.config.window_manager', 'backend.config.fernet_key',
        'backend.config.performance_config',
        
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
