import os
from dotenv import load_dotenv
from sentinelhub import SHConfig

load_dotenv()  # reads .env from the current working directory


def get_config():
    client_id = os.getenv("SH_CLIENT_ID")
    client_secret = os.getenv("SH_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError(
            "SH_CLIENT_ID / SH_CLIENT_SECRET not found.\n"
            "Make sure you have a .env file in the project root with:\n"
            "  SH_CLIENT_ID=your-client-id\n"
            "  SH_CLIENT_SECRET=your-client-secret\n"
            "and that it's NOT committed to git (check .gitignore)."
        )

    config = SHConfig()
    config.sh_client_id = client_id
    config.sh_client_secret = client_secret
    config.sh_base_url = "https://sh.dataspace.copernicus.eu"
    config.sh_token_url = "https://identity.dataspace.copernicus.eu/auth/realms/CDSE/protocol/openid-connect/token"

    return config