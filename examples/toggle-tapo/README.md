# toggle tapo example

This example shows how to toggle a TP-Link Tapo device on and off with a simple http to tapo bridge. 

This server must be running on the same network as the Tapo device, and the `pushbutt` device must be able to send http requests to this server.


```bash
uv run main.py
# INFO:     Started server process [82590]
# INFO:     Waiting for application startup.
# INFO:     Application startup complete.
# INFO:     Uvicorn running on http://0.0.0.0:9000 (Press CTRL+C to quit)
```

then simply send a http request to the server to toggle the tapo device

```bash
curl http://localhost:9000/toggle
# {"state": "off"}
```
