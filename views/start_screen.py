import flet as ft
import os

class StartScreen(ft.Container):
    # ... (existing imports)
    async def _handle_google_login(self, e):
        """Triggers Flet's OAuth Flow (Mobile Compatible)."""
        self.login_status.value = "Launching Login..."
        self.login_status.update()
        try:
            await self.main_page.login(self.main_page.auth_provider)
        except Exception as ex:
             self.login_status.value = f"Login Error: {ex}"
             self.login_status.update()

    def on_login(self, e):
        """Callback when Flet Login succeeds."""
        print("DEBUG: Google Login Success!")
        token = self.main_page.auth.token.access_token # Flet Auth Token
        
        # Init Drive Manager
        from controllers.drive_manager import DriveManager
        dm = DriveManager()
        success, msg = dm.set_credentials(token)
        
        if success:
             self.login_status.value = f"✅ Connected"
             self.login_status.color = ft.Colors.GREEN
             self.btn_cloud.disabled = False # Enable Sync
        else:
             self.login_status.value = f"❌ Drive Error: {msg}"
             self.login_status.color = ft.Colors.RED
        self.login_status.update()
        self.btn_cloud.update()

    def _open_cloud_sync(self, e):
        from views.components.cloud_sync_dialog import CloudSyncDialog
        dlg = CloudSyncDialog(self.main_page)
        self.main_page.overlay.append(dlg)
        dlg.open = True
        self.main_page.update()

    def __init__(self, page: ft.Page, on_continue=None, on_new_game=None, save_exists=False):
        super().__init__()
        self.main_page = page
        self.on_continue = on_continue
        self.on_new_game = on_new_game
        self.expand = True
        self.alignment = ft.Alignment(0, 0)
        self.save_exists = save_exists
        
        # Attach On Login Callback to Page (Hack for access within Screen)
        # Note: Flet's page.on_login is global. 
        # We should set it in main.py, or hijack it here carefully.
        self.main_page.on_login = self.on_login
        
        # UI Components
        self.title_text = ft.Text("Taiwan Basketball GM", size=40, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER)
        self.subtitle_text = ft.Text("TPBL Edition", size=20, color=ft.Colors.GREY_400)
        
        # Continue Button
        self.btn_continue = ft.ElevatedButton(
            "繼續遊戲 (Continue)", 
            icon=ft.Icons.PLAY_ARROW,
            height=50,
            width=260,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                bgcolor=ft.Colors.PRIMARY,
                color=ft.Colors.ON_PRIMARY,
            ),
            on_click=self._handle_continue,
            disabled=not self.save_exists
        )
        
        # New Game Button
        self.btn_new = ft.ElevatedButton(
            "新遊戲 (New Game)", 
            icon=ft.Icons.ADD,
            height=50,
            width=260,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=10),
                bgcolor="#3E4760",
            ),
            on_click=self._handle_new_game_request
        )

        # Cloud Section
        self.login_status = ft.Text("Not Logged In", size=12, color=ft.Colors.GREY)
        
        self.btn_google = ft.ElevatedButton(
            "Login with Google",
            icon=ft.Icons.LOGIN,
            on_click=self._handle_google_login,
            bgcolor="#FFFFFF",
            color="#000000",
            width=260
        )
        
        self.btn_cloud = ft.IconButton(
            ft.Icons.CLOUD_SYNC,
            on_click=self._open_cloud_sync,
            tooltip="Cloud Save Sync",
            disabled=True # Disabled until Login
        )

        self.content = ft.Column([
            ft.Icon(ft.Icons.SPORTS_BASKETBALL, size=100, color=ft.Colors.PRIMARY),
            ft.Container(height=20),
            self.title_text,
            self.subtitle_text,
            ft.Container(height=50),
            self.btn_continue,
            ft.Container(height=10),
            self.btn_new,
            ft.Container(height=10),
            ft.Container(content=ft.Divider(), width=100),
            ft.Text("Cloud Services", size=14, weight="bold"),
            self.btn_google,
            self.login_status,
            self.btn_cloud, # Icon Button
            
            ft.Container(height=20),
            ft.Text("Ver 1.0.0", color=ft.Colors.GREY_700)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

    def _handle_continue(self, e):
        if self.on_continue:
            self.on_continue()

    def _handle_new_game_request(self, e):
        print("DEBUG: New Game Button Clicked")
        if self.save_exists:
            print(f"DEBUG: Save Exists ({self.save_exists}) - Opening Dialog")
            
            def close_dlg(e):
                self.confirm_dialog.open = False
                self.main_page.update()

            self.confirm_dialog = ft.AlertDialog(
                title=ft.Text("警告 (Warning)"),
                content=ft.Text("確定要開始新遊戲嗎？現有的存檔將被覆蓋。\n(Start new game? Current save will be lost.)"),
                actions=[
                    ft.TextButton("取消 (Cancel)", on_click=close_dlg),
                    ft.TextButton("確定 (Confirm)", on_click=self._execute_new_game, style=ft.ButtonStyle(color=ft.Colors.ERROR))
                ],
                actions_alignment=ft.MainAxisAlignment.END,
                modal=True
            )
            
            # Use Overlay to avoid page.dialog issues
            self.main_page.overlay.append(self.confirm_dialog)
            self.confirm_dialog.open = True
            self.main_page.update()
        else:
            print("DEBUG: No Save - executing direct")
            self._execute_new_game(None)

    def _execute_new_game(self, e):
        print("DEBUG: Executing New Game Logic")
        try:
            # Close dialog if it exists
            if hasattr(self, 'confirm_dialog') and self.confirm_dialog:
                self.confirm_dialog.open = False
                self.main_page.update()
        except: pass

        if self.on_new_game:
            self.on_new_game()
