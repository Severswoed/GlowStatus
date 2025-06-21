# 📅 How to Get a Google Calendar API Key

To integrate with Google Calendar, you need an API key and OAuth credentials from the Google Cloud Console. Follow these steps to obtain them.

---

## 📋 Step-by-Step Instructions

### 1. Go to the Google Cloud Console  
Visit the Google Cloud Console at:  
👉 [https://console.cloud.google.com/](https://console.cloud.google.com/)

---

### 2. Create a New Project  
- Click on the **Project dropdown** at the top of the page.  
- Click **New Project**, give it a name, and click **Create**.

---

### 3. Enable the Google Calendar API  
- In the left sidebar, go to **APIs & Services > Library**.  
- Search for **Google Calendar API**.  
- Click **Enable**.

---

### 4. Create Credentials  
Go to **APIs & Services > Credentials**, then:

- Click **Create Credentials** > **OAuth 2.0 Client IDs** or **API key**, depending on your use case.

> ⚠️ **For read/write access to calendar events, use OAuth 2.0.**  
> API Keys are usually used for read-only public calendar access.

---

### 5. Set Up OAuth Consent Screen  
- Go to **OAuth consent screen** in the left sidebar.  
- Choose **External** or **Internal** based on your user audience.  
- Fill in app name, support email, and required fields.  
- Add the **Scopes** your app needs (e.g., `.../auth/calendar.readonly` or `.../auth/calendar`).

---

### 6. Configure OAuth Client ID  
- Choose **Web application**, give it a name.  
- Add your **authorized redirect URIs** if needed (e.g., for local testing or production).

---

### 7. Save and Copy Credentials  
- Once created, you’ll be shown your **Client ID** and **Client Secret**.  
- Save these securely — they are required for authenticating API requests.

---

## 🧪 Test the API  
Use the [Google OAuth Playground](https://developers.google.com/oauthplayground/) or your preferred API client to test Google Calendar operations.

---

## 📘 Documentation  
Full Google Calendar API docs here:  
👉 [https://developers.google.com/calendar](https://developers.google.com/calendar)

---

## 🆘 Support  
For help, visit:  
📨 [https://support.google.com/cloud](https://support.google.com/cloud)

---

## ✅ You’re Ready to Integrate  
You now have the credentials to begin authenticating and using the Google Calendar API. Be sure to securely store your secrets and comply with Google’s usage and consent policies.