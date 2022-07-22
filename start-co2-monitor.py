#!/home/tudor/co2meter-env/.env/bin/python3
import logging
import json
import netrc
import time

import click

import co2meter as co2
import paho.mqtt.client as mqtt

netrc_entries = netrc.netrc()

MQTT_SERVER = "YOUR_SERVER_HERE"
MQTT_USER = netrc.netrc().authenticators(MQTT_SERVER)[0]
MQTT_PASSWORD = netrc.netrc().authenticators(MQTT_SERVER)[2]
MQTT_TOPIC = "sensors/raspi-co2-monitor-001"

logging.basicConfig(format="%(asctime)s %(levelname)-5.5s [%(name)s] %(message)s")
logger = logging.getLogger("CO2Monitor")
logger.setLevel(logging.INFO)


@click.command()
@click.option("--interval", default=30, help="Interval to report to MQTT")
def main(interval):
    logger.info("CO2 monitor initializing")
    mon = co2.CO2monitor(bypass_decrypt=True)
    logger.info("Initialized CO2 monitor %s", mon.info)

    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_publish = on_publish
    client.username_pw_set(MQTT_USER, MQTT_PASSWORD)

    while True:
        logger.info("Reading data")
        timestamp, co2_ppm, temperature = mon.read_data()
        logger.info("Read Data: CO2 PPM %s, Temperature: %d.02", co2_ppm, temperature)
        if not client.is_connected():
            logger.info("Client is not connected, connecting to server %s", MQTT_SERVER)
            client.connect(MQTT_SERVER, 1883, 60)
        logger.info()
        client.publish(
            MQTT_TOPIC,
            json.dumps(
                {
                    "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
                    "temperature": round(temperature, 2),
                    "co2ppm": co2_ppm,
                }
            ),
        )
        time.sleep(interval)


def on_connect(client, userdata, flags, rc):
    logger.info("MQTT Connected with result code " + str(rc))


def on_publish(client, userdata, result):
    logger.info("MQTT data published: %s", result)


if __name__ == "__main__":
    main()
