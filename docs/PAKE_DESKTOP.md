# Pake Desktop Shell

Agent Meeting Room ships with a reliable PyInstaller executable first. This Pake path is an optional desktop-shell build for people who want a more native app window around the existing Flask UI.

Pake turns a web app into a lightweight desktop app using Tauri. For Agent Meeting Room, the shell points at the local Flask server, so the backend still needs Python, Ollama, and the normal app dependencies.

## Prerequisites

- Python 3.11+
- Node.js and npm
- Rust/Cargo from https://rustup.rs/
- Ollama installed and at least one model pulled

Install Python dependencies first:

```powershell
pip install -r requirements.txt
```

Install Node dependencies:

```powershell
npm install
```

## Build

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

This is a desktop shell around the local web app, not a replacement for the PyInstaller release. The standard `AgentMeetingRoom.exe` remains the simplest release asset because it starts the backend and opens the UI by itself.

The next step, if this shell feels good, is to make the desktop wrapper start the backend automatically at runtime too.
