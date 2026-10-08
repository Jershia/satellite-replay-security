import json

import rclpy
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from std_msgs.msg import String

from satellite_comm.security import verify_mac


rclpy.init()

ros_node = rclpy.create_node('fastapi_bridge')
ros_publisher = ros_node.create_publisher(
    String,
    'telecommand',
    10
)

app = FastAPI()


class Telecommand(BaseModel):
    command: str
    timestamp: int
    nonce: str
    mac: str


@app.get("/")
def home():
    return {"status": "FastAPI server is running"}


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/telecommand")
def receive_telecommand(data: Telecommand):

    if not verify_mac(
        data.command,
        data.timestamp,
        data.nonce,
        data.mac
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid MAC"
        )

    message = {
        "command": data.command,
        "timestamp": data.timestamp,
        "nonce": data.nonce,
        "mac": data.mac
    }

    msg = String()
    msg.data = json.dumps(message)

    ros_publisher.publish(msg)

    return {
        "status": "accepted",
        "forwarded": True,
        "command": data.command
    }
