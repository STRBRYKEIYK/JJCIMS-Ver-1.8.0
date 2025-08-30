# 2FA Setup Wizard Integration Guide

This document explains how to integrate the 2FA Setup Wizard into the Admin Settings panel.

## Import the Wizard

```python
from gui.functions.admdash_f.tfas.tfa_su_sett import create_2fa_setup_frame
```

## Create and Embed the Wizard

```python
# Inside your admin settings class or function
def show_2fa_setup_section(self, username=None):
    # Clear previous content in the settings frame
    for widget in self.settings_frame.winfo_children():
        widget.destroy()
    
    # Create the 2FA setup wizard with callbacks
    self.current_wizard = create_2fa_setup_frame(
        parent=self.settings_frame,
        username=username,  # Pass the current admin username or a specific username
        colors={
            "bg": "#000000",  # Match your admin panel background
            "header": "#800000"  # Match your header color
        },
        on_complete=self.on_2fa_setup_complete,  # Optional success callback
        on_cancel=self.on_2fa_setup_cancel,      # Optional cancel callback
        start_step=1                             # Start at step 1 (default)
    )
    
def on_2fa_setup_complete(self):
    # This will be called when 2FA setup is completed
    print("2FA Setup completed!")
    # You can update UI, refresh settings, show a success message, etc.
    
def on_2fa_setup_cancel(self):
    # This will be called when user cancels 2FA setup
    print("2FA Setup cancelled!")
    # You can update UI, hide the 2FA section, etc.
```

## Navigate to Specific Steps

You can navigate to specific steps in the wizard programmatically:

```python
# Navigate to the key setup page directly
self.current_wizard.navigate_to_step(5)
```

## Clean Up

When removing the wizard from the UI or switching to another settings section:

```python
if hasattr(self, 'current_wizard') and self.current_wizard:
    self.current_wizard.cleanup()
    self.current_wizard = None
```

## Frame Reference

The wizard's frame is accessible via the `frame` property:

```python
wizard = create_2fa_setup_frame(parent=container, username="admin")
wizard.frame.pack(fill="both", expand=True)
```

## Wizard Parameters

- `parent`: The parent widget to contain the wizard
- `username`: Username for 2FA setup
- `db_path`: Path to Access database (optional)
- `fernet_key_path`: Path to Fernet key file (optional)
- `colors`: Dictionary with "bg" and "header" color values (optional)
- `start_step`: Initial step to show (1-5, default is 1)
- `on_complete`: Callback function when setup is complete (optional)
- `on_cancel`: Callback function when setup is cancelled (optional)

## Styling Notes

- The wizard is designed to fit within a 1400×841 frame
- Colors can be customized to match your admin panel's theme
- Asset paths have been updated to use "adm_sett_2fa_setup_assets" folder
