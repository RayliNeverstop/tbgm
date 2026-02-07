import flet
import sys

print(f"Flet File: {flet.__file__}")
try:
    print(f"Flet __version__: {flet.__version__}")
except:
    print("No flet.__version__")

try:
    import flet.auth
    print("Imported flet.auth")
    print(dir(flet.auth))
except Exception as e:
    print(f"Error importing flet.auth: {e}")

try:
    import flet.auth.providers
    print("Imported flet.auth.providers")
    print(dir(flet.auth.providers))
except Exception as e:
    print(f"Error importing flet.auth.providers: {e}")

try:
    from flet.auth.providers import GoogleOAuthProvider
    print("Imported GoogleOAuthProvider")
except Exception as e:
    print(f"Error importing GoogleOAuthProvider: {e}")
