# 🔍 How to Find Your Govee Device ID

To integrate your Govee lights with **GlowStatus**, you’ll need your **Device ID**.

---

## 🛠️ Step-by-Step Instructions

### 1. Use the Govee Developer API

Run the following command in your terminal, replacing the API key if needed:

```bash
curl -X GET "https://developer-api.govee.com/v1/devices" \
  -H "Govee-API-Key: your-govee-api-key"
```

---

### 2. Sample Response

```json
{
  "data": {
    "devices": [
      {
        "device": "00:11:22:33:AA:BB:CC",
        "model": "H61AB",
        "deviceName": "GlowStatus Lights",
        "controllable": true,
        "retrievable": true,
        "supportCmds": ["turn", "brightness", "color"]
      }
    ]
  }
}
```

> ✅ The **`device`** value (e.g., `00:11:22:33:AA:BB:CC`) is your Govee Device ID.

---

## 🔐 Add to `.env`

Once you have the Device ID, add it to your `.env`:

```env
GOVEE_DEVICE_ID=00:11:22:33:AA:BB:CC
```

---

## 🧪 Optional: Python Script

Use this Python snippet to list devices:

```python
import requests

API_KEY = "your_govee_api_key"
headers = {"Govee-API-Key": API_KEY}
response = requests.get("https://developer-api.govee.com/v1/devices", headers=headers)
print(response.json())
```

---

Let your lights know your status – automatically.
