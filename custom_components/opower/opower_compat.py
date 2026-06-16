"""Compatibility patches for the upstream opower package."""

from __future__ import annotations

from inspect import getsource
import re
from typing import Any

import aiohttp
from opower.const import USER_AGENT
from opower.exceptions import InvalidAuth
from opower.utilities.portlandgeneral import PortlandGeneral

PGE_TOKEN_ENDPOINT = "https://api.portlandgeneral.com/pg-token-implicit/token"
PGE_TOKEN_CLIENT_ID = "rHuS10KrfsLwFAr2sZ7MHh7oHELGx6YK"
_PATCHED_ATTR = "_ha_opower_pge_login_patched"


def _get_upstream_pge_login_source() -> str:
    """Return the current upstream PGE login source."""
    return getsource(PortlandGeneral.async_login)


def _get_firebase_api_key() -> str:
    """Extract the upstream Firebase API key from the installed opower package."""
    source = _get_upstream_pge_login_source()
    match = re.search(r'"key": "([^"]+)"', source)
    if match is None:
        raise RuntimeError("Unable to determine the Portland General login API key")
    return match.group(1)


def ensure_portland_general_login_fix() -> None:
    """Patch stale Portland General Electric login constants in opower."""
    if getattr(PortlandGeneral.async_login, _PATCHED_ATTR, False):
        return

    source = _get_upstream_pge_login_source()
    if PGE_TOKEN_ENDPOINT in source and PGE_TOKEN_CLIENT_ID in source:
        return

    firebase_api_key = _get_firebase_api_key()

    async def _async_login(
        self: PortlandGeneral,
        session: aiohttp.ClientSession,
        username: str,
        password: str,
        login_data: dict[str, Any],
    ) -> str:
        """Login to Portland General Electric using the current public web constants."""
        del login_data

        async with session.post(
            "https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword",
            headers={
                "authority": "identitytoolkit.googleapis.com",
                "User-Agent": USER_AGENT,
                "accept": "*/*",
                "content-type": "application/json",
                "origin": "https://portlandgeneral.com",
                "referer": "https://portlandgeneral.com/",
            },
            json={
                "email": username,
                "password": password,
                "returnSecureToken": True,
            },
            params={"key": firebase_api_key},
            raise_for_status=False,
        ) as resp:
            if resp.status == 400:
                raise InvalidAuth("Username and password failed")
            result = await resp.json()

        async with session.post(
            PGE_TOKEN_ENDPOINT,
            params={
                "client_id": PGE_TOKEN_CLIENT_ID,
                "response_type": "token",
                "redirect_uri": "",
            },
            headers={
                "content-length": "0",
                "User-Agent": USER_AGENT,
                "accept": "*/*",
                "content-type": "application/json",
                "origin": "https://portlandgeneral.com",
                "referer": "https://portlandgeneral.com/",
                "idp_access_token": result.get("idToken"),
            },
            raise_for_status=False,
        ) as resp:
            result = await resp.json()
            if resp.status == 500:
                raise InvalidAuth(
                    "Username and Password Succeeded, but api responded with "
                    + str(result["errorResponse"])
                    + ". Code 500 could mean the client_id const is incorrect."
                )
            if "errorResponse" in result:
                raise InvalidAuth(
                    "Username and Password Succeeded, but api responded with "
                    + str(result["errorResponse"])
                )
            return str(result.get("access_token"))

    setattr(_async_login, _PATCHED_ATTR, True)
    PortlandGeneral.async_login = _async_login
