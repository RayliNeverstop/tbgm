try:
    from flet.auth.oauth_provider import OAuthProvider
    print("SUCCESS: Imported OAuthProvider from flet.auth.oauth_provider")
except Exception as e:
    print(f"FAILED to import OAuthProvider: {e}")

try:
    import flet.auth.providers.google_oauth_provider
    print("WARNING: Imported flet.auth.providers.google_oauth_provider (Unexpected logic?)")
except Exception as e:
    print(f"CONFIRMED Bug in providers: {e}")
