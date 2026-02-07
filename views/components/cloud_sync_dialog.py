import flet as ft
from controllers.game_manager import GameManager
from controllers.drive_manager import DriveManager
from utils.localization import tr
import os

class CloudSyncDialog(ft.AlertDialog):
    def __init__(self, page: ft.Page):
        super().__init__()
        self.page_ref = page
        self.gm = GameManager()
        self.drive = DriveManager()
        self.title = ft.Text(tr("Cloud Sync (Google Drive)"))
        self.modal = True
        
        self.status_text = ft.Text("Checking connection...", italic=True)
        self.local_info = ft.Text("Local: ...")
        self.cloud_info = ft.Text("Cloud: Checking...")
        
        self.btn_upload = ft.ElevatedButton(
            "Upload to Cloud (Overwrite)", 
            icon=ft.Icons.CLOUD_UPLOAD, 
            on_click=self._on_upload,
            disabled=True,
            bgcolor="#2E7D32", 
            color="#FFFFFF"
        )
        
        self.btn_download = ft.ElevatedButton(
            "Download from Cloud (Overwrite Local)", 
            icon=ft.Icons.CLOUD_DOWNLOAD, 
            on_click=self._on_download,
            disabled=True,
            bgcolor="#C62828",
            color="#FFFFFF"
        )
        
        self.content = ft.Container(
            content=ft.Column([
                self.status_text,
                ft.Divider(),
                ft.Row([
                    ft.Column([
                        ft.Text("Local Save", weight="bold"),
                        self.local_info
                    ], expand=True),
                    ft.Column([
                        ft.Text("Cloud Save", weight="bold"),
                        self.cloud_info
                    ], expand=True)
                ]),
                ft.Divider(),
                ft.Row([self.btn_upload], alignment=ft.MainAxisAlignment.CENTER),
                ft.Container(height=10),
                ft.Row([self.btn_download], alignment=ft.MainAxisAlignment.CENTER),
            ], width=500, height=300),
            padding=10
        )
        
        self.actions = [
            ft.TextButton("Close", on_click=self.close_dialog)
        ]
        
        # Initial Check
        self._check_status()

    def _check_status(self):
        # 1. Local Status
        save_path = os.path.join(self.gm.save_manager.save_dir, "save_1.enc")
        if os.path.exists(save_path):
             size = os.path.getsize(save_path) / 1024
             self.local_info.value = f"Exists ({size:.1f} KB)\nEncrypted"
             self.btn_upload.disabled = False
        else:
             self.local_info.value = "No Save Found"
             self.btn_upload.disabled = True
             
        # 2. Cloud Status
        if not self.drive.service:
             self.status_text.value = "Not Connected to Google."
             self.cloud_info.value = "Offline"
             self.btn_upload.disabled = True
             self.btn_download.disabled = True
             return

        try:
             files = self.drive.list_cloud_saves()
             target = next((f for f in files if f['name'] == 'save_1.enc'), None)
             
             if target:
                 self.cloud_info.value = f"Exists (ID: ...{target['id'][-6:]})"
                 self.status_text.value = "Ready to Sync."
                 self.btn_download.disabled = False
             else:
                 self.cloud_info.value = "Not Found"
                 self.status_text.value = "Cloud Empty."
                 self.btn_download.disabled = True
                 
             # Enable upload if local exists and connected
             if self.local_info.value != "No Save Found":
                 self.btn_upload.disabled = False
                 
        except Exception as e:
             self.cloud_info.value = f"Error: {e}"

        self.update()

    def _on_upload(self, e):
        self.status_text.value = "Uploading..."
        self.status_text.update()
        
        save_path = os.path.join(self.gm.save_manager.save_dir, "save_1.enc")
        if not os.path.exists(save_path): return
        
        success, msg = self.drive.upload_save(save_path, "save_1.enc")
        self.status_text.value = f"Upload: {msg}"
        self.status_text.update()
        self._check_status()

    def _on_download(self, e):
        self.status_text.value = "Downloading..."
        self.status_text.update()
        
        save_path = os.path.join(self.gm.save_manager.save_dir, "save_1.enc")
        success, msg = self.drive.download_save("save_1.enc", save_path)
        
        if success:
            self.status_text.value = "Download Success! You may need to reload."
            # Reload Current Game if running?
            # Ideally restart app or reload data
        else:
            self.status_text.value = f"Download Failed: {msg}"
            
        self.status_text.update()
        self._check_status()

    def close_dialog(self, e):
        self.open = False
        self.page_ref.update()
