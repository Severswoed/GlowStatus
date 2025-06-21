import requests
from logger import get_logger

logger = get_logger()

class GoveeController:
    BASE_URL = "https://developer-api.govee.com/v1/devices/control"

    def __init__(self, api_key, device_id):
        self.api_key = api_key
        self.device_id = device_id
        if not self.api_key or not self.device_id:
            logger.error("Govee API key or Device ID not set.")

    def set_color(self, r, g, b):
        """Set the Govee device color using RGB values."""
        payload = {
            "device": self.device_id,
            "model": "H6001",  # You may want to make this configurable
            "cmd": {
                "name": "color",
                "value": {"r": r, "g": g, "b": b}
            }
        }
        headers = {
            "Govee-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.put(self.BASE_URL, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"Govee color set to RGB({r}, {g}, {b})")
        except Exception as e:
            logger.error(f"Failed to set Govee color: {e}")