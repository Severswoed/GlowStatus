# How to Find Your Govee Device ID

To use GlowStatus with your Govee smart light, you need your device's unique Device ID. Here’s how to find it:

---

## 📱 Using the Govee App

1. **Open the Govee App** on your phone.
2. **Select your device** from the device list.
3. Tap the **gear/settings icon** (usually in the top right).
4. Scroll down to **"Device Info"** or **"About"**.
5. Look for the **Device ID** (often starts with "AA:BB:CC:...").

---

## 🖥️ Using the Govee API

1. **Get your Govee API Key** from the [Govee Developer Portal](https://developer.govee.com/).
2. Use the following command to list your devices:

   ```bash
   curl -X GET "https://developer-api.govee.com/v1/devices" \
     -H "Govee-API-Key: YOUR_API_KEY"
   ```

3. The response will include your devices and their IDs, e.g.:

   ```json
   {
     "data": {
       "devices": [
         {
           "device": "AA:BB:CC:DD:EE:FF",
           "model": "H6159",
           "deviceName": "Desk Lamp"
         }
       ]
     }
   }
   ```

---

## 📝 Tips

- The Device ID is **case-sensitive** and usually formatted like a MAC address.
- Copy it exactly as shown in the app or API response.

---

## ❓ Need Help?

If you have trouble finding your Device ID, check the [Govee API docs](https://developer.govee.com/docs) or ask in the