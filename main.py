import flet as ft
from controllers.game_manager import GameManager
from views.main_layout import MainLayout
import os

def main(page: ft.Page):
    try:
        page.title = "Taiwan Basketball GM (TPBL Edition)"
        # ... (Theme setup remains)
        page.theme_mode = ft.ThemeMode.DARK 
        tpbl_navy = "#003460"
        tpbl_gold = "#CFB28B"
        deep_navy = "#0b1120"
        card_surface = "#151b2c"
        
        # Custom High Contrast Theme
        theme = ft.Theme(
            color_scheme=ft.ColorScheme(
                primary=tpbl_gold, 
                on_primary=deep_navy, 
                primary_container=tpbl_gold, 
                on_primary_container=tpbl_navy, 
                secondary=tpbl_gold,
                on_secondary=deep_navy,
                surface=card_surface,
                on_surface="#E0E0E0",
            ),
            page_transitions=ft.PageTransitionsTheme(
                windows=ft.PageTransitionTheme.CUPERTINO
            )
        )
        
        page.theme = theme
        page.dark_theme = theme
        page.bgcolor = deep_navy 

        page.window_width = 1200
        page.window_height = 800
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # --- Authentication Note ---
        # We now use DriveManager's explicit login flow (google-auth-oauthlib)
        # instead of Flet's page.login which had issues on Desktop.
        # ---------------------------
        
        # Initialize Game Manager
        
        # Initialize Game Manager
        # Use CWD + 'game_saves' to avoid Android Permission Denied on root /data
        # os.expanduser("~") was resolving to /data which is Read-Only.
        save_dir = os.path.join(os.getcwd(), "game_saves")
        if not os.path.exists(save_dir):
            try:
                os.makedirs(save_dir)
                print(f"DEBUG: Created save directory: {save_dir}")
            except Exception as e:
                print(f"DEBUG: Failed to create save dir {save_dir}: {e}")
        
        persistent_path = os.path.join(save_dir, "save_1.json")
        
        current_dir = os.path.dirname(os.path.abspath(__file__))
        template_path = os.path.join(current_dir, "data", "gamedata.json")
        
        gm = GameManager()
        
        if os.path.exists(persistent_path):
            print(f"DEBUG: Loading from Persistent Path: {persistent_path}")
            try:
                gm.initialize(persistent_path)
            except Exception as e:
                print(f"ERROR: Failed to load save file (Corrupted?): {e}")
                # Rename corrupted file to avoid crash loop
                try:
                    corrupted_path = persistent_path + ".corrupted"
                    if os.path.exists(corrupted_path):
                        os.remove(corrupted_path)
                    os.rename(persistent_path, corrupted_path)
                    print(f"DEBUG: Renamed corrupted file to {corrupted_path}")
                except Exception as rename_error:
                    print(f"DEBUG: Failed to rename corrupted file: {rename_error}")
                
                # Fallback to template
                print(f"DEBUG: Fallback - Loading Template: {template_path}")
                gm.initialize(template_path)
        else:
            print(f"DEBUG: First Run - Loading Template: {template_path}")
            gm.initialize(template_path)
            
        # FORCE Future Saves to Persistent Path & Directory
        gm.data_loader.file_path = persistent_path
        # Important: Update SaveManager to write to the new relative directory
        gm.save_manager.save_dir = save_dir
        
        print(f"DEBUG: Future Saves will go to: {persistent_path}")

        # Define Navigation Callbacks
        def start_game_flow():
            page.clean()
            app = MainLayout(page)
            page.add(app)
            page.update()

        def finalize_new_game(team_id):
            print(f"DEBUG: Finalizing New Game with Team: {team_id}")
            # Update User Team (Set the selected team as the user's team)
            gm.user_team_id = team_id
            # Force Save Initial State with new team
            gm.save_game(1)
            # Enter Game
            start_game_flow()
            
        def team_select_flow():
            page.clean()
            from views.team_select_screen import TeamSelectScreen
            # Pass page and callback
            ts_screen = TeamSelectScreen(page, on_team_selected=finalize_new_game)
            page.add(ts_screen)
            page.update()

        def new_game_flow():
            # 1. Reset Data (Load Template)
            gm.reset_game(template_path)
            # 2. Navigate to Team Selection
            team_select_flow()
            
        # Initialize Start Screen
        from views.start_screen import StartScreen
        has_save = os.path.exists(persistent_path)
        
        start_screen = StartScreen(
            page, 
            on_continue=start_game_flow, 
            on_new_game=new_game_flow, 
            save_exists=has_save
        )
        
        page.add(start_screen)
        page.update()
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(error_trace)
        page.add(
            ft.Column([
                ft.Text("Application Error", size=30, color=ft.Colors.RED),
                ft.Text(f"Error: {e}", color=ft.Colors.RED),
                ft.Container(
                    content=ft.Text(error_trace, font_family="Consolas"),
                    bgcolor="#111111",
                    padding=10,
                    border_radius=5
                )
            ], scroll=ft.ScrollMode.AUTO)
        )
        page.update()

if __name__ == "__main__":
    ft.app(target=main) # Deprecation warning on some versions, but ft.run might not be available on older ones?
    # User said: DeprecationWarning: app() is deprecated since version 0.70.0. Use run() instead.
    # So we should use ft.run if available, or keep ft.app and ignore warning.
    # However, to be safe, let's keep ft.app but acknowledge warning, OR better: use ft.app for now as it still works.
    # Actually, let's just use ft.app as the user only saw a Warning, not an Error for that.
    # The ERROR was AttributeError.
    # But if I really want to fix it:
    # try:
    #    ft.run(target=main)
    # except AttributeError:
    #    ft.app(target=main)
    # Let's stick to ft.app unless it breaks.
    pass
