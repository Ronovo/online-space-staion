"""Run Space Station Explorer Online with Flask's built-in server. Settings are listed in README.md."""

import os

from space_online.webapp import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        threaded=True,
    )
