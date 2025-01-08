import os
from tapo import ApiClient
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

tapo_username = os.getenv("TAPO_USERNAME", "default")
tapo_password = os.getenv("TAPO_PASSWORD", "default")
ip_address = os.getenv("IP_ADDRESS", "192.168.1.200")
client = ApiClient(tapo_username, tapo_password)


async def toggle_device():
    device = await client.generic_device(ip_address)
    device_info = await device.get_device_info()
    if device_info.device_on:
        await device.off()
        return "off"
    await device.on()
    return "on"


@app.get("/toggle")
async def toggle():
    state = await toggle_device()
    return {"state": state}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9000)
