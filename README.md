# JJC Fabrication and Parts Inventory System (JJCFPIS)

Comprehensive Windows-based inventory and user management system with role-based access, 2FA (TOTP) security, user role management, backup/restore, and integrated administrative settings.

## Key Features

- Role-based access levels (Levels 1–5)
- Two-Factor Authentication (2FA) setup & enforcement (TOTP with QR codes)
- User roles manager (create, edit, promote/demote, password + 2FA reset)
- Integrated Admin Settings (Accounts, 2FA, Roles, Backup/Restore, About)
- Inventory management (Add / Update items modules)
- Employee vs Admin login flows
- Encrypted sensitive data using Fernet keys
- Audit logging to Excel (logs.xlsx) and text logs
- Packaged via PyInstaller for distribution

## Project Structure (Highlights)

```text
main.py                # Entry point
assets/                # Images and UI assets
config/                # Core configuration + encryption key
   fernet_key.py
   admin_otp_secret.txt
   performance_config.py
   gui_config.py
   window_manager.py
database/
   JJCIMS.accdb        # Main DB
   logs.xlsx           # Activity logs
   access_connector.py
   Backup/             # Backup artifacts
gui/
   admin_dashboard.py
   employee_dashboard.py
   admin_login.py
   employee_login.py
   functions/
      admdash_f/
         integrated_adm_sett.py    # Integrated admin settings hub
         tfas/                     # 2FA setup + wizard
            tfa_su_wizard.py
            tfa_su_sett.py
      emplydash_f/
         checkout_win.py
utils/               # Helpers (image mgmt, notifications, crypto wrappers)
```

## 2FA System Overview

The 2FA system uses TOTP (pyotp) with QR code provisioning. Secrets are encrypted with a Fernet key stored in `config/fernet_key.py`. Two pathways exist:

- Stand‑alone multi-step wizard (`tfa_su_wizard.py`)
- Integrated settings variant (`tfa_su_sett.py`) aligned to mirror behavior (Steps 1–5)

Both perform:

1. Username validation & permission check (Level ≥3 typically required)
2. Existing secret detection / reset handling
3. Secret generation + QR provisioning
4. Code verification using current TOTP
5. Secret persistence (encrypted) & confirmation

## Building & Running

See `INSTALLATION_GUIDE.txt` for full environment setup (Python or EXE usage). Quick dev run:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py
```

## Updating / Packaging

```powershell
pyinstaller JJCIMS.spec
```

Outputs to `dist/`.

## Backup & Restore

- Automatic DB + key backups to `database/Backup/`
- Use Integrated Admin Settings > Backup/Restore for UI workflow
- Always include: `JJCIMS.accdb`, `logs.xlsx`, `fernet_key.py`, OTP secrets

## Security Notes

- Never expose `fernet_key.py` publicly
- Restrict file system permissions on `config/` & `database/`
- Regularly rotate secrets if compromised (use 2FA reset flow)

## Troubleshooting Snapshot

| Issue | Action |
|-------|--------|
| ODBC / Access driver error | Install Access Database Engine 2016 (64-bit) |
| Cannot find table Emp_list | Verify table exists (case-insensitive), repair DB |
| 2FA not verifying | System clock drift; re-sync time or re-scan QR |
| Missing assets | App falls back to text buttons; restore from `assets/` |

## Contributing

1. Create a branch
2. Make focused changes (code + tests if applicable)
3. Update docs (README / guides) when touching features
4. Submit PR for review

## License / Ownership

Internal system for JJC Engineering Works and General Services. Distribution restricted unless authorized.

## Version

Current: 1.0.0 (see `version_info.txt`)

---

For deeper setup and integration details, consult `INSTALLATION_GUIDE.txt` and `INTEGRATION_GUIDE.txt`.
