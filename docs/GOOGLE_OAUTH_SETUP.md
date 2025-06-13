# Google OAuth Setup Guide

This guide helps you set up Google OAuth authentication for Text-to-CAD to enable user authentication and usage tracking (10 models per user).

## Prerequisites

- Google Cloud Platform account
- Project with enabled APIs

## Setup Steps

### 1. Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable the **Google+ API** or **People API**

### 2. Configure OAuth Consent Screen

1. Navigate to **APIs & Services** → **OAuth consent screen**
2. Choose **External** user type
3. Fill required fields:
   - **App name**: Text-to-CAD
   - **User support email**: Your email
   - **Developer contact**: Your email
4. Add authorized domains if needed
5. Save and continue through remaining steps

### 3. Create OAuth Credentials

1. Go to **APIs & Services** → **Credentials**
2. Click **Create Credentials** → **OAuth client ID**
3. Select **Web application**
4. Configure:
   - **Name**: Text-to-CAD Client
   - **Authorized JavaScript origins**: 
     - `http://localhost:8080`
     - `http://127.0.0.1:8080`
     - Add your production domain
   - **Authorized redirect URIs**: Same as origins
5. Copy the **Client ID**

### 4. Update Frontend Configuration

1. Open `frontend/scripts/auth.js`
2. Replace the placeholder with your Client ID:
   ```javascript
   const CLIENT_ID = 'your-actual-client-id.googleusercontent.com';
   ```
3. Save the file

### 5. Test Authentication

1. Start the application (Docker or manual setup)
2. Open the frontend in your browser
3. Click the **Sign In** button
4. Complete Google OAuth flow
5. Verify user info appears in header

## Security Notes

- Keep your Client ID public-facing only (no Client Secret needed for frontend)
- Never commit sensitive credentials to version control
- Use environment variables for production deployments
- Regularly review authorized domains and redirect URIs

## Troubleshooting

**"Origin not allowed"**: Add your domain to authorized JavaScript origins
**"Redirect URI mismatch"**: Ensure redirect URIs match exactly
**"Access blocked"**: Complete OAuth consent screen configuration

For more details, see [Google OAuth 2.0 documentation](https://developers.google.com/identity/oauth2/web/guides/overview).
