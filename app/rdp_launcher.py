"""
RDP Launcher - Launches Windows Remote Desktop (mstsc.exe) with a generated .rdp file.
Uses cmdkey to pre-store credentials so user doesn't need to re-enter password.
This is the most reliable approach on Windows - used by mRemoteNG, RoyalTS, etc.
"""
import os
import sys
import subprocess
import tempfile
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

MSTSC_PATH = r"C:\Windows\System32\mstsc.exe"


def _find_mstsc() -> str:
    """Find mstsc.exe on the system."""
    candidates = [
        r"C:\Windows\System32\mstsc.exe",
        r"C:\Windows\SysWOW64\mstsc.exe",
        r"C:\Windows\SysNative\mstsc.exe",
    ]
    for path in candidates:
        if os.path.isfile(path):
            return path
    # Last resort: use where.exe
    try:
        result = subprocess.run(["where", "mstsc.exe"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            found = result.stdout.strip().splitlines()[0]
            if os.path.isfile(found):
                return found
    except Exception:
        pass
    return r"C:\Windows\System32\mstsc.exe"  # Default fallback


def _get_rdp_file_dir() -> str:
    """Get temp directory for .rdp files."""
    d = os.path.join(tempfile.gettempdir(), "MultiRemote_RDP")
    os.makedirs(d, exist_ok=True)
    return d


def build_rdp_file(
    ip: str,
    port: int = 3389,
    username: str = "",
    domain: str = "",
    width: int = 1920,
    height: int = 1080,
    color_depth: int = 32,
    use_h264: bool = True,
    network_type: int = 6,
    smart_sizing: bool = True,
    enable_nla: bool = True,
    compress: bool = True,
    fullscreen: bool = False,
    audio_mode: int = 1,
) -> str:
    """
    Build a .rdp configuration file and return its path.
    """
    address = f"{ip}:{port}" if port != 3389 else ip

    # NLA/CredSSP settings
    auth_level = 0  # 0 = Connect and do not warn on certificate issues
    credSSP = 1 if enable_nla else 0

    # Screen mode: 2 = fullscreen, 1 = windowed
    screen_mode = 2 if fullscreen else 1

    # Network connection type mapping
    # 1=Modem, 2=Low-band, 3=Satellite, 4=High-latency, 5=WAN, 6=LAN, 7=Auto
    conn_type = min(max(network_type, 1), 7)

    # Color depth bits
    bpp = color_depth if color_depth in (8, 15, 16, 24, 32) else 32

    lines = [
        f"full address:s:{address}",
        f"desktopwidth:i:{width}",
        f"desktopheight:i:{height}",
        f"session bpp:i:{bpp}",
        f"screen mode id:i:{screen_mode}",
        f"use multimon:i:0",
        f"compression:i:{1 if compress else 0}",
        f"keyboardhook:i:2",
        f"audiomode:i:{audio_mode}",
        f"audiocapturemode:i:0",
        f"videoplaybackmode:i:{1 if use_h264 else 0}",
        f"connection type:i:{conn_type}",
        f"networkautodetect:i:1",
        f"bandwidthautodetect:i:1",
        f"displayconnectionbar:i:{1 if fullscreen else 0}",
        f"disable wallpaper:i:0",
        f"allow font smoothing:i:1",
        f"disable full window drag:i:0",
        f"disable menu anims:i:0",
        f"bitmapcachepersistenable:i:1",
        f"autoreconnection enabled:i:1",
        f"authentication level:i:{auth_level}",
        f"enablecredsspsupport:i:{credSSP}",
        f"prompt for credentials:i:0",
        f"promptcredentialonce:i:1",
        f"negotiate security layer:i:1",
        f"smart sizing:i:{1 if smart_sizing else 0}",
        f"redirectclipboard:i:1",
        f"redirectprinters:i:0",
        f"redirectcomports:i:0",
        f"redirectsmartcards:i:0",
    ]

    if username:
        lines.append(f"username:s:{username}")
    if domain and domain.strip():
        lines.append(f"domain:s:{domain.strip()}")

    content = "\r\n".join(lines) + "\r\n"
    safe_ip = ip.replace(".", "_").replace(":", "_")
    rdp_path = os.path.join(_get_rdp_file_dir(), f"session_{safe_ip}_{port}.rdp")
    with open(rdp_path, "w", encoding="utf-8") as f:
        f.write(content)

    logger.info(f"RDP file created: {rdp_path}")
    return rdp_path


def store_credentials(ip: str, port: int, username: str, password: str, domain: str = ""):
    """
    Use Windows cmdkey to store credentials for the target server.
    This allows mstsc.exe to connect without prompting for password.
    """
    if not password or not username:
        logger.info("No credentials to store (username or password empty)")
        return False

    # cmdkey target format
    target = f"TERMSRV/{ip}"
    if port != 3389:
        target = f"TERMSRV/{ip}:{port}"

    # Full username: domain\username or just username
    full_user = f"{domain}\\{username}" if domain and domain.strip() else username

    try:
        cmd = ["cmdkey", f"/generic:{target}", f"/user:{full_user}", f"/pass:{password}"]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            logger.info(f"Credentials stored via cmdkey for {target} (user: {full_user})")
            return True
        else:
            logger.warning(f"cmdkey failed: {result.stderr.strip()}")
            return False
    except Exception as e:
        logger.error(f"Failed to store credentials: {e}")
        return False


def delete_credentials(ip: str, port: int = 3389):
    """Remove stored credentials after session ends."""
    target = f"TERMSRV/{ip}"
    if port != 3389:
        target = f"TERMSRV/{ip}:{port}"
    try:
        subprocess.run(["cmdkey", f"/delete:{target}"], capture_output=True, timeout=5)
        logger.info(f"Credentials removed for {target}")
    except Exception as e:
        logger.debug(f"cmdkey delete: {e}")


def trust_server_in_registry(ip: str):
    """Mark server as trusted in HKCU to suppress untrusted publisher caution dialogs."""
    try:
        import winreg
        # 1. LocalDevices: allows redirection of clipboard, webauth, etc. without prompting
        key_path = r"Software\Microsoft\Terminal Server Client\LocalDevices"
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                winreg.SetValueEx(key, ip, 0, winreg.REG_DWORD, 255)
                logger.info(f"Marked {ip} as trusted in LocalDevices registry")
        except Exception:
            pass

        # 2. Servers: marks server identity as accepted
        srv_path = rf"Software\Microsoft\Terminal Server Client\Servers\{ip}"
        try:
            with winreg.CreateKey(winreg.HKEY_CURRENT_USER, srv_path) as key:
                winreg.SetValueEx(key, "CertHash", 0, winreg.REG_BINARY, b"")
        except Exception:
            pass
    except Exception as e:
        logger.debug(f"trust_server_in_registry: {e}")


def launch_mstsc(
    ip: str,
    port: int = 3389,
    username: str = "",
    password: str = "",
    domain: str = "",
    width: int = 1920,
    height: int = 1080,
    color_depth: int = 32,
    use_h264: bool = True,
    network_type: int = 6,
    smart_sizing: bool = True,
    enable_nla: bool = True,
    compress: bool = True,
    fullscreen: bool = False,
    audio_mode: int = 1,
) -> subprocess.Popen | None:
    """
    Launch mstsc.exe with a generated .rdp file.
    Stores credentials via cmdkey if password is provided.
    Returns the Popen process handle so caller can track when it exits.
    """
    if not os.path.isfile(MSTSC_PATH):
        logger.error(f"mstsc.exe not found at {MSTSC_PATH}")
        return None

    # Step 0: Suppress caution/untrusted connection prompt in registry
    trust_server_in_registry(ip)

    # Step 1: Store credentials so mstsc doesn't prompt
    creds_stored = False
    if username and password:
        creds_stored = store_credentials(ip, port, username, password, domain)

    # Step 2: Build .rdp file
    rdp_file = build_rdp_file(
        ip=ip, port=port, username=username, domain=domain,
        width=width, height=height, color_depth=color_depth,
        use_h264=use_h264, network_type=network_type,
        smart_sizing=smart_sizing, enable_nla=enable_nla,
        compress=compress, fullscreen=fullscreen,
        audio_mode=audio_mode,
    )

    # Step 3: Launch mstsc.exe
    mstsc_exe = _find_mstsc()
    cmd = [mstsc_exe, rdp_file]
    if fullscreen:
        cmd.append("/f")

    try:
        proc = subprocess.Popen(cmd)
        logger.info(f"Launched mstsc.exe (PID={proc.pid}) for {ip}:{port}")
        return proc
    except Exception as e:
        logger.error(f"Failed to launch mstsc.exe: {e}")
        if creds_stored:
            delete_credentials(ip, port)
        return None


def test_port_reachable(ip: str, port: int = 3389, timeout: float = 3.0) -> bool:
    """Quick TCP test to see if RDP port is reachable before launching mstsc."""
    import socket
    try:
        with socket.create_connection((ip, port), timeout=timeout):
            return True
    except (socket.timeout, ConnectionRefusedError, OSError):
        return False
