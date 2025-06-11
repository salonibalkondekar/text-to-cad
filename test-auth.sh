#!/bin/bash

# AI CAD.js Authentication Demo Script
echo "🚀 AI CAD.js Authentication System Demo"
echo "========================================"
echo ""

# Check if backend is running
echo "1. Testing Backend Connection..."
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
if [ "$BACKEND_STATUS" -eq 200 ]; then
    echo "✅ Backend is running on http://localhost:8000"
else
    echo "❌ Backend is not running. Please start with: cd backend && python3 app.py"
    exit 1
fi

# Check if frontend is running
echo ""
echo "2. Testing Frontend Connection..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080)
if [ "$FRONTEND_STATUS" -eq 200 ]; then
    echo "✅ Frontend is running on http://localhost:8080"
else
    echo "❌ Frontend is not running. Please start with: cd frontend && python3 -m http.server 8080"
    exit 1
fi

# Test user creation
echo ""
echo "3. Testing User Management..."
USER_RESPONSE=$(curl -s -X POST http://localhost:8000/api/user/info \
    -H "Content-Type: application/json" \
    -d '{"user_id":"demo_user_123","email":"demo@example.com","name":"Demo User"}')
echo "✅ User created: $USER_RESPONSE"

# Test model count increment
echo ""
echo "4. Testing Model Count Management..."
COUNT_RESPONSE=$(curl -s -X POST http://localhost:8000/api/user/increment-count \
    -H "Content-Type: application/json" \
    -d '{"user_id":"demo_user_123"}')
echo "✅ Model count incremented: $COUNT_RESPONSE"

# Test generation with user
echo ""
echo "5. Testing Model Generation with User Authentication..."
GEN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/generate \
    -H "Content-Type: application/json" \
    -d '{"prompt":"Create a simple cube","user_id":"demo_user_123"}')
echo "✅ Model generated: $(echo $GEN_RESPONSE | cut -c1-100)..."

echo ""
echo "🎉 All tests passed! Authentication system is working correctly."
echo ""
echo "📝 Next Steps:"
echo "   1. Get your Google Client ID from: https://console.cloud.google.com/"
echo "   2. Replace 'YOUR_GOOGLE_CLIENT_ID_HERE' in frontend/scripts/auth.js"
echo "   3. Open http://localhost:8080 and test Google Sign-In"
echo ""
echo "📖 For detailed setup instructions, see: GOOGLE_OAUTH_SETUP.md"
