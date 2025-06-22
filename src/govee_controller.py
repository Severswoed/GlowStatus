import requests
from logger import get_logger

logger = get_logger()

class GoveeController:
    BASE_URL = "https://developer-api.govee.com/v1/devices/control"

    def __init__(self, api_key, device_id, device_model=None):
        self.api_key = api_key
        self.device_id = device_id
        self.device_model = device_model or "H6001"
        if not self.api_key or not self.device_id:
            logger.error("Govee API key or Device ID not set.")

    def set_color(self, r, g, b):
        """Set the Govee device color using RGB values."""
        payload = {
            "device": self.device_id,
            "model": self.device_model,
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
            logger.info(f"Govee color set to RGB({r}, {g}, {b}) for model {self.device_model}")
        except Exception as e:
            logger.error(f"Failed to set Govee color: {e}")

    def set_brightness(self, brightness):
        """Set the Govee device brightness."""
        payload = {
            "device": self.device_id,
            "model": self.device_model,
            "cmd": {
                "name": "brightness",
                "value": brightness
            }
        }
        headers = {
            "Govee-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.put(self.BASE_URL, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"Govee brightness set to {brightness} for model {self.device_model}")
        except Exception as e:
            logger.error(f"Failed to set Govee brightness: {e}")

    def is_on(self):
        """
        Check if the Govee device is currently on.
        Note: This uses an undocumented endpoint and may not work for all users/devices.
        """
        url = f"https://developer-api.govee.com/v1/devices/status?device={self.device_id}"
        headers = {
            "Govee-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            status = response.json().get("data", {}).get("status", {})
            power_state = status.get("powerState", "off")
            logger.info(f"Govee device power state: {power_state}")
            return power_state == "on"
        except Exception as e:
            logger.error(f"Failed to check Govee power state: {e}")
            return False
    
    def set_power(self, power_state):
        """Turn the Govee device on or off."""
        payload = {
            "device": self.device_id,
            "model": self.device_model,
            "cmd": {
                "name": "turn",
                "value": power_state
            }
        }
        headers = {
            "Govee-API-Key": self.api_key,
            "Content-Type": "application/json"
        }
        try:
            response = requests.put(self.BASE_URL, json=payload, headers=headers, timeout=10)
            response.raise_for_status()
            logger.info(f"Govee power state set to {power_state} for model {self.device_model}")
        except Exception as e:
            logger.error(f"Failed to set Govee power state: {e}")
            
    