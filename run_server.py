"""Run Space Station Explorer Online with Flask's built-in server.

Environment variables:
    HOST                     interface to bind (default 127.0.0.1; use 0.0.0.0 to allow other machines)
    PORT                     port to listen on (default 5000)
    SPACE_ONLINE_SECRET_KEY  session signing key (default: generated once into instance/secret_key)
"""

import os

from space_online.webapp import create_app

app = create_app()

if __name__ == "__main__":
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=int(os.environ.get("PORT", "5000")),
        threaded=True,
    )
