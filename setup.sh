#!/bin/bash

echo ""
echo "🛠️  Setting up your OTJ Hours Automation environment..."
echo ""

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