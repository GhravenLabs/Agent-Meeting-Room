# Desktop Shell Builds

Agent Meeting Room ships with a reliable PyInstaller executable first. The repo also includes two desktop-shell experiments for people who want a more native app window.

## Tauri Backend-Owned Shell

This is the more complete desktop app path. It builds the Flask app as a PyInstaller backend sidecar, bundles that sidecar into a Tauri app, starts the backend when the desktop app launches, waits for it, and opens the local UI inside the native WebView window.

Build it with:

```powershell
npm run desktop:tauri
```

Generated installers are written under:

```text
desktop/src-tauri/target/x86_64-pc-windows-msvc/release/bundle/
```

The desktop shell stores writable user files in the app data directory instead of next to the embedded backend executable. That keeps `.env`, saved meeting notes, and `agent_profiles.json` user-local.

## Pake URL Wrapper

Pake turns a web app into a lightweight desktop app using Tauri. For Agent Meeting Room, the Pake wrapper points at the local Flask server. That means the backend must already be running, or the build script must start it only for packaging.

## Prerequisites

- Python 3.11+
- Node.js and npm
- Rust/Cargo from https://rustup.rs/
- Visual Studio C++ Build Tools on Windows
- Ollama installed and at least one model pulled

Install Python dependencies first:

```powershell
pip install -r requirements.txt
```

Install Node dependencies:

```powershell
npm install
```

## Build Pake Wrapper

Build the Windows MSI desktop shell:

```powershell
npm run desktop:pake:msi
```

The script starts the Flask backend on `http://127.0.0.1:5000`, waits for it to respond, runs Pake, and then stops the backend.

Use another port if needed:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-pake-desktop.ps1 -Port 5050 -Targets msi
```

If you already started Agent Meeting Room yourself:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/build-pake-desktop.ps1 -SkipServer
```

## Current Limitation

The Pake wrapper is a desktop shell around the local web app, not a replacement for the PyInstaller release.

The Tauri backend-owned shell is the serious desktop-app path because it starts the backend automatically at runtime.
