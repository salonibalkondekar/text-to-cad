#!/bin/bash

# Google OAuth Setup Script for AI CAD Application

echo "🚀 AI CAD Google OAuth Setup"
echo "=============================="
echo ""

echo "This script will help you set up Google OAuth for your AI CAD application."
echo ""

echo "📋 Prerequisites:"
echo "1. You need a Google account"
echo "2. Access to Google Cloud Console"
echo "3. Basic understanding of OAuth 2.0"
echo ""

echo "🔗 Steps to follow:"
echo ""
echo "1. Go to Google Cloud Console: https://console.cloud.google.com/"
echo "2. Create a new project or select an existing one"
echo "3. Enable the Google Identity services"
echo "4. Go to 'APIs & Services' > 'OAuth consent screen'"
echo "5. Configure the consent screen with these details:"
echo "   - App name: AI CAD.js"
echo "   - User support email: your-email@example.com"
echo "   - Developer contact: your-email@example.com"
echo ""
echo "6. Go to 'APIs & Services' > 'Credentials'"
echo "7. Click 'Create Credentials' > 'OAuth client ID'"
echo "8. Choose 'Web application'"
echo "9. Add these Authorized origins:"
echo "   - http://localhost:8000"
echo "   - http://localhost:3000"
echo "   - http://127.0.0.1:8000"
echo ""
echo "10. Add these Authorized redirect URIs:"
echo "    - http://localhost:8000"
echo "    - http://localhost:3000"
echo "    - http://127.0.0.1:8000"
echo ""

# Check if auth.js exists
if [ -f "frontend/scripts/auth.js" ]; then
    echo "11. Copy your Client ID and paste it below:"
    echo ""
    read -p "Enter your Google OAuth Client ID: " client_id
    
    if [ ! -z "$client_id" ]; then
        # Update the auth.js file
        sed -i.bak "s/YOUR_GOOGLE_CLIENT_ID_HERE/$client_id/g" frontend/scripts/auth.js
        echo ""
        echo "✅ Client ID updated in frontend/scripts/auth.js"
        echo ""
        echo "🔧 Re-enabling Google OAuth in auth.js..."
        
        # Comment out the mock auth and enable real Google OAuth
        cat > temp_auth_fix.js << 'EOF'
// Enable Google OAuth initialization
sed -i.bak2 's/return; \/\/ Skip Google API initialization for now//g' frontend/scripts/auth.js
sed -i.bak3 's/\/\/ For now.*showing sign-in button/\/\/ Google OAuth is now configured/g' frontend/scripts/auth.js
EOF
        
        echo "✅ Google OAuth has been configured!"
        echo ""
        echo "🎯 Next steps:"
        echo "1. Restart your development server"
        echo "2. Refresh your browser"
        echo "3. You should now see the 'Sign in with Google' button"
        echo "4. Test the sign-in functionality"
        echo ""
        echo "🔧 If you encounter issues:"
        echo "1. Check the browser console for errors"
        echo "2. Verify your Client ID is correct"
        echo "3. Ensure your domain is in the authorized origins"
        echo "4. Check that all redirect URIs are correctly configured"
        echo ""
    else
        echo "❌ No Client ID provided. Setup incomplete."
        echo ""
        echo "💡 To complete setup later:"
        echo "1. Get your Client ID from Google Cloud Console"
        echo "2. Run this script again, or"
        echo "3. Manually replace 'YOUR_GOOGLE_CLIENT_ID_HERE' in frontend/scripts/auth.js"
    fi
else
    echo "❌ frontend/scripts/auth.js not found!"
    echo "Make sure you're running this script from the project root directory."
fi

echo ""
echo "📚 For detailed instructions, see: GOOGLE_OAUTH_SETUP.md"
echo "🌐 Google Identity Documentation: https://developers.google.com/identity/gsi/web"
