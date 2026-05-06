"""
Entry point for both development and packaged .exe
"""
import sys, os, threading, time, webbrowser
import uvicorn

HOST = "127.0.0.1"
PORT = int(os.environ.get("MOLDB_PORT", "8000"))


def open_browser():
    time.sleep(1.5)
    webbrowser.open(f"http://{HOST}:{PORT}")


def main():
    threading.Thread(target=open_browser, daemon=True).start()
    uvicorn.run(
        "ui.app:app",
        host=HOST,
        port=PORT,
        log_level="warning",
        # Needed for PyInstaller one-file build
        reload=False,
    )


if __name__ == "__main__":
    main()
