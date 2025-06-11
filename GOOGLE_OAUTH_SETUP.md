# Google OAuth Setup Guide

To enable Google Sign-In authentication for the AI CAD application, follow these steps:

## 1. Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API for your project

## 2. Configure OAuth Consent Screen

1. In the Google Cloud Console, go to **APIs & Services** > **OAuth consent screen**
2. Choose **External** user type (unless you're creating an internal app)
3. Fill in the required fields:
   - App name: `AI CAD.js`
   - User support email: Your email
   - Developer contact information: Your email
4. Add scopes (optional for basic profile info)
5. Add test users if needed

## 3. Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **Create Credentials** > **OAuth client ID**
3. Choose **Web application** as the application type
4. Add authorized origins:
   - `http://localhost:8080` (for development)
   - `http://localhost:8000` (alternative dev port)
   - Your production domain (when deployed)
5. Add authorized redirect URIs:
   - `http://localhost:8080` (for development)
   - `http://localhost:8000` (alternative dev port)
   - Your production domain (when deployed)

## 4. Update the Client ID

1. Copy the **Client ID** from the credentials you just created
2. Open `frontend/scripts/auth.js`
3. Replace `YOUR_GOOGLE_CLIENT_ID_HERE` with your actual client ID:

```javascript
client_id: 'your-actual-client-id-here.apps.googleusercontent.com'
```

## 5. Test the Setup

1. Start the application:
   ```bash
   cd frontend
   npm start
   ```
2. Open your browser and navigate to the application
3. You should see a "Sign in with Google" button in the header
4. Click it to test the authentication flow

## Security Notes

- Never commit your actual Client ID to version control if it's a private repository
- Consider using environment variables for production deployments
- The Client ID is safe to expose in frontend code (it's designed to be public)
- Make sure to configure the authorized origins correctly to prevent unauthorized use

## Troubleshooting

### Common Issues:

1. **"Error: popup_closed_by_user"**
   - User closed the popup before completing sign-in
   - This is normal user behavior

2. **"Error: redirect_uri_mismatch"**
   - The redirect URI in your OAuth settings doesn't match your development URL
   - Add your exact development URL to the authorized redirect URIs

3. **"Error: origin_mismatch"**
   - The origin in your OAuth settings doesn't match your development URL
   - Add your exact development URL to the authorized origins

4. **Google API not loading**
   - Check your internet connection
   - Ensure the Google APIs script is loaded before your auth script

For more detailed information, visit the [Google Identity documentation](https://developers.google.com/identity/gsi/web).


