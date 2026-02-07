try:
    import flet
    print(f"Flet Version: {flet.version.version}")
    
    from flet.auth.providers import GoogleOAuthProvider
    print("Successfully imported GoogleOAuthProvider")
    
    import flet.auth.providers
    print(dir(flet.auth.providers))
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
