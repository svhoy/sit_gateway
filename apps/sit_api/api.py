from .auth import Authenticator


def get_uwb_device_settings(auth: Authenticator) -> None:
    response, data = auth.fetch(url="settings/uwb/")

    if response.status_code == 200:
        print(f"Daten: {data}")
