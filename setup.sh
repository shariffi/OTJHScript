#!/bin/bash

echo ""
echo "🛠️  Setting up your OTJ Hours Automation environment..."
echo ""

read -p "💬 Enter your Chrome version (e.g., 115, 116, 137). Leave empty to auto-detect: " CHROME_VERSION

# Detect version if not provided
if [ -z "$CHROME_VERSION" ]; then
    if command -v /Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome >/dev/null 2>&1; then
        FULL_VERSION=$(/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome --version | grep -oE '[0-9.]+' | head -n1)
    elif command -v google-chrome >/dev/null 2>&1; then
        FULL_VERSION=$(google-chrome --version | grep -oE '[0-9.]+' | head -n1)
    else
        echo "❌ Could not auto-detect Chrome version. Please enter it manually."
        exit 1
    fi
    CHROME_VERSION=$(echo "$FULL_VERSION" | cut -d '.' -f1)
    echo "📦 Detected Chrome version: $CHROME_VERSION"
fi

PLATFORM="mac-arm64"
BASE_URL="https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing"
LATEST_JSON="https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json"

echo "🌐 Fetching ChromeDriver info from Google..."
DOWNLOAD_URL=$(curl -s "$LATEST_JSON" | grep -A5 "\"$CHROME_VERSION\"" | grep "chromedriver-$PLATFORM.zip" | cut -d '"' -f4 | head -n1)

if [ -z "$DOWNLOAD_URL" ]; then
    echo "❌ Could not find a matching ChromeDriver for version $CHROME_VERSION"
    exit 1
fi

echo "⬇️ Downloading ChromeDriver for Chrome v$CHROME_VERSION..."
curl -L -o chromedriver.zip "$DOWNLOAD_URL"

echo "📂 Extracting..."
unzip -o chromedriver.zip -d chromedriver

echo "🧹 Cleaning up..."
rm chromedriver.zip

echo "✅ ChromeDriver setup complete. ChromeDriver extracted to ./chromedriver"

# Step 1: Create virtual environment
python3 -m venv venv

# Step 2: Install dependencies using venv's pip
echo ""
echo "📦 Installing Python packages..."
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt

# Step 3: Run the script using venv's python
echo ""
echo "🚀 Starting the automation script..."
./venv/bin/python OTJHScript.py