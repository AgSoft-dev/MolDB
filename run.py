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

    from ui.app import app  # direct import instead of string reference

    uvicorn.run(
        app,            # pass object, not string
        host=HOST,
        port=PORT,
        log_level="warning",
        reload=False,   # must be False when passing app object anyway
    )


if __name__ == "__main__":
    main()
