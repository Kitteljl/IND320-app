"""Central place for reading secrets, so no passwords appear in code."""

import os
import tomllib
from pathlib import Path

SECRETS_PATH = Path(__file__).parent / ".streamlit" / "secrets.toml"


def get_secret(section: str, key: str) -> str:
    # 1. Streamlit (running in the app, locally or on Streamlit Cloud)
    try:
        import streamlit as st
        return st.secrets[section][key]
    except Exception:
        pass

    # 2. Local secrets file (used from the notebook)
    if SECRETS_PATH.exists():
        with open(SECRETS_PATH, "rb") as f:
            data = tomllib.load(f)
        if section in data and key in data[section]:
            return data[section][key]

    # 3. Environment variable, e.g. MONGO_URI
    env_name = f"{section}_{key}".upper()
    if env_name in os.environ:
        return os.environ[env_name]

    raise KeyError(f"Secret [{section}] {key} not found")