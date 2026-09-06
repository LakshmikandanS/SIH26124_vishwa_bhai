"""
Lightweight Pure-Python MQTT Broker (amqtt)
===========================================
Runs on port 1883 with anonymous auth enabled.
Eliminates Docker/Mosquitto binary requirement on Windows.
"""

import asyncio
import logging
import signal
from amqtt.broker import Broker

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] [MQTT-Broker] %(message)s")
logger = logging.getLogger("MQTTBroker")

config = {
    "listeners": {
        "default": {
            "type": "tcp",
            "bind": "127.0.0.1:1883",
            "max_connections": 100,
        }
    },
    "sys_interval": 30,
    "auth": {
        "allow-anonymous": True,
    },
}


async def start_broker():
    broker = Broker(config)
    await broker.start()
    logger.info("=" * 60)
    logger.info("  🚀 Pure-Python MQTT Broker Listening on 127.0.0.1:1883")
    logger.info("=" * 60)
    try:
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, asyncio.CancelledError):
        await broker.shutdown()
        logger.info("Broker stopped.")


if __name__ == "__main__":
    try:
        asyncio.run(start_broker())
    except KeyboardInterrupt:
        pass
