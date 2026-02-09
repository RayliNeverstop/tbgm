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
        
        # --- Authentication Setup ---
        from flet.auth.providers import GoogleOAuthProvider
        
        # TODO: Replace with your actual Client ID and Secret from Google Cloud Console
        # On Android, the redirect_url is handled by Flet/Flutter internally usually, 
        # but defining one helps Flet know it's a web flow.
        page.auth_provider = GoogleOAuthProvider(
            client_id="YOUR_CLIENT_ID_HERE",
            client_secret="YOUR_CLIENT_SECRET_HERE",
            redirect_url="https://localhost/callback" 
        )
        # ---------------------------
        
        # Initialize Game Manager
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
                try:
                    corrupted_path = persistent_path + ".corrupted"
                    if os.path.exists(corrupted_path):
                        os.remove(corrupted_path)
                    os.rename(persistent_path, corrupted_path)
                    print(f"DEBUG: Renamed corrupted file to {corrupted_path}")
                except Exception as rename_error:
                    print(f"DEBUG: Failed to rename corrupted file: {rename_error}")
                
                print(f"DEBUG: Fallback - Loading Template: {template_path}")
                gm.initialize(template_path)
        else:
            print(f"DEBUG: First Run - Loading Template: {template_path}")
            gm.initialize(template_path)
            
        gm.data_loader.file_path = persistent_path
        gm.save_manager.save_dir = save_dir
        print(f"DEBUG: Future Saves will go to: {persistent_path}")

        # --- Navigation & Routing ---
        from views.start_screen import StartScreen
        from views.team_select_screen import TeamSelectScreen
        from views.main_layout import MainLayout

        def finalize_new_game(team_id):
            print(f"DEBUG: Finalizing New Game with Team: {team_id}")
            gm.user_team_id = team_id
            gm.save_game(1)
            page.go("/game")
            
        def view_pop(view):
            page.views.pop()
            top_view = page.views[-1]
            page.go(top_view.route)

        page.on_view_pop = view_pop

        def route_change(route):
            print(f"DEBUG: Route Change to {page.route}")
            page.views.clear()
            
            # Start Screen (Root)
            has_save = os.path.exists(persistent_path)
            start_screen = StartScreen(
                page, 
                on_continue=lambda: page.go("/game"), 
                on_new_game=lambda: page.go("/team_select"), 
                save_exists=has_save
            )
            page.views.append(
                ft.View(
                    "/",
                    [start_screen],
                    padding=0,
                    bgcolor=deep_navy
                )
            )

            if page.route == "/team_select":
                # Reset game data before team select
                gm.reset_game(template_path)
                
                ts_screen = TeamSelectScreen(page, on_team_selected=finalize_new_game)
                page.views.append(
                    ft.View(
                        "/team_select",
                        [ts_screen],
                        padding=0,
                        bgcolor=deep_navy
                    )
                )

            if page.route == "/game":
                app = MainLayout(page)
                page.views.append(
                    ft.View(
                        "/game",
                        [app],
                        padding=0,
                        bgcolor=deep_navy
                    )
                )
            
            page.update()

        page.on_route_change = route_change
        page.go(page.route)
        
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
