# 🚀 Complete Deployment Guide - AI Virtual Photographer

## Table of Contents
1. [Project Structure Overview](#project-structure-overview)
2. [Pre-Deployment Checklist](#pre-deployment-checklist)
3. [Step-by-Step Deployment](#step-by-step-deployment)
4. [Environment Variables Reference](#environment-variables-reference)
5. [Troubleshooting](#troubleshooting)
6. [Sharing for Testing](#sharing-for-testing)

---

## Project Structure Overview

```
d:\image_gen\
│
├── 📁 app/                          # Web Application
│   ├── __init__.py
│   └── streamlit_app.py            # Main Streamlit UI
│
├── 📁 agents/                       # AI Agents (Business Logic)
│   ├── __init__.py
│   ├── garment_understanding_agent.py  # Analyzes garment images
│   ├── prompt_builder_agent.py         # Builds generation prompts
│   ├── tryon_generation_agent.py       # Orchestrates try-on pipeline
│   └── quality_checker_agent.py        # Validates generated images
│
├── 📁 config/                       # Configuration
│   ├── __init__.py
│   └── settings.py                 # All env-based settings
│
├── 📁 schemas/                      # Data Models (Pydantic)
│   ├── __init__.py
│   ├── garment_schema.py           # Garment description schema
│   └── generation_request.py       # Request/response models
│
├── 📁 services/                     # External API Wrappers
│   ├── __init__.py
│   └── gemini_client.py            # Google Gemini API client
│
├── 📁 utils/                        # Utility Functions
│   ├── __init__.py
│   ├── logging_utils.py            # Logging configuration
│   └── image_utils.py              # Image processing
│
├── 📁 .streamlit/                   # Streamlit Configuration
│   ├── config.toml                 # Theme settings (included)
│   └── secrets.toml.example        # Secrets template (NOT included)
│
├── 📁 docs/                         # Documentation
│   ├── CODE_DOCUMENTATION.md       # Full code explanation
│   └── IMPROVEMENT_PLAN.md         # Future improvements
│
├── 📄 .env.example                  # Environment template (included)
├── 📄 .env                          # Your secrets (NOT included)
├── 📄 .gitignore                    # Git ignore rules
├── 📄 requirements.txt              # Python dependencies
├── 📄 README.md                     # Project documentation
└── 📄 DEPLOYMENT_GUIDE.md           # This file
```

---

## Pre-Deployment Checklist

Before deploying, verify:

- [ ] `.gitignore` excludes `.env` and `venv/`
- [ ] `requirements.txt` has all dependencies
- [ ] No hardcoded API keys in any file
- [ ] `.streamlit/config.toml` exists for theme
- [ ] All Python files have no syntax errors

**Test locally first:**
```bash
cd d:\image_gen
venv\Scripts\activate
streamlit run app/streamlit_app.py
```

---

## Step-by-Step Deployment

### Step 1: Prepare Git Repository

```powershell
# Navigate to project folder
cd d:\image_gen

# Initialize Git (if not done)
git init

# Check what will be committed (should NOT include .env or venv)
git status

# Add all tracked files
git add .

# Verify .env is NOT staged
git status
# You should NOT see .env in the list

# Commit
git commit -m "AI Virtual Photographer - Initial Release"
```

### Step 2: Create GitHub Repository

1. Go to **[github.com/new](https://github.com/new)**
2. Create repository:
   - **Name:** `ai-virtual-photographer`
   - **Visibility:** Public (required for free Streamlit)
   - **DO NOT** add README or .gitignore (you have them)
3. Click **Create repository**

### Step 3: Push to GitHub

```powershell
# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/ai-virtual-photographer.git

# Push code
git branch -M main
git push -u origin main
```

### Step 4: Deploy to Streamlit Cloud

1. Go to **[share.streamlit.io](https://share.streamlit.io)**
2. Sign in with GitHub
3. Click **"New app"**
4. Configure:
   ```
   Repository:  YOUR_USERNAME/ai-virtual-photographer
   Branch:      main
   Main file:   app/streamlit_app.py
   ```
5. Click **"Deploy!"**

### Step 5: Add API Key (CRITICAL!)

1. Wait for app to deploy (will show error without API key)
2. Click **"Manage app"** (⋮ menu) → **"Settings"**
3. Click **"Secrets"** tab
4. Paste this (with YOUR key):

```toml
# Required
GEMINI_API_KEY = "YOUR_ACTUAL_API_KEY_HERE"

# Optional - Model Configuration
GEMINI_TEXT_VISION_MODEL_ID = "gemini-2.0-flash-exp"
GEMINI_IMAGE_MODEL_ID = "imagen-3.0-generate-002"
GEMINI_NATIVE_IMAGE_MODEL_ID = "gemini-2.0-flash-preview-image-generation"

# Optional - Quality Settings
IMAGE_ASPECT_RATIO = "3:4"
ENABLE_PROMPT_ENHANCEMENT = "true"
AUTO_QUALITY_KEYWORDS = "true"
```

5. Click **"Save"**
6. Click **"Reboot app"** from the ⋮ menu

### Step 6: Verify Deployment

1. Wait 1-2 minutes for reboot
2. Open your app URL
3. Upload a test garment image
4. Click **"Generate Try-On"**
5. Verify image generation works ✅

---

## Environment Variables Reference

All settings are configurable via Streamlit Secrets or `.env` file:

### Required

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Your Google AI API key |

### Model Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `GEMINI_TEXT_VISION_MODEL_ID` | `gemini-2.0-flash-exp` | Vision/analysis model |
| `GEMINI_IMAGE_MODEL_ID` | `imagen-3.0-generate-002` | Primary image model |
| `GEMINI_NATIVE_IMAGE_MODEL_ID` | `gemini-2.0-flash-preview-image-generation` | Fallback model |

### Quality Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `IMAGE_ASPECT_RATIO` | `3:4` | Output aspect ratio |
| `IMAGE_COUNT` | `1` | Images per generation |
| `ENABLE_PROMPT_ENHANCEMENT` | `true` | AI prompt optimization |
| `AUTO_QUALITY_KEYWORDS` | `true` | Add quality terms |
| `QUALITY_KEYWORDS` | `high-quality, 4K...` | Quality terms to add |
| `SAFETY_FILTER_LEVEL` | `block_only_high` | Content filter level |

### Generation Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `ANALYSIS_TEMPERATURE` | `0.2` | Lower = more consistent |
| `GENERATION_TEMPERATURE` | `0.9` | Higher = more creative |
| `MAX_RETRIES` | `3` | API retry attempts |
| `RETRY_DELAY_SECONDS` | `1.0` | Delay between retries |

---

## Files Included vs Excluded

### ✅ Included in Git (will be deployed)

```
app/                     # All Python files
agents/                  # All Python files
config/                  # settings.py
schemas/                 # All Python files
services/                # gemini_client.py
utils/                   # All Python files
docs/                    # Documentation
.streamlit/config.toml   # Theme only
.env.example             # Template
requirements.txt         # Dependencies
README.md                # Documentation
DEPLOYMENT_GUIDE.md      # This guide
```

### ❌ Excluded from Git (.gitignore)

```
.env                     # Your API key (SECRET!)
.streamlit/secrets.toml  # Local secrets
venv/                    # Virtual environment (large)
__pycache__/             # Python cache
*.pyc, *.pyo             # Compiled files
test.py                  # Test file
.vscode/, .idea/         # IDE settings
*.log                    # Log files
```

---

## Troubleshooting

### "API Key not configured" Error
```
Solution:
1. Go to Streamlit Cloud → App Settings → Secrets
2. Add: GEMINI_API_KEY = "your_key"
3. Click Save, then Reboot app
```

### "ModuleNotFoundError" 
```
Solution:
1. Check requirements.txt has all packages
2. Ensure package names are correct:
   - google-genai (NOT google-generativeai)
   - streamlit
   - pydantic
   - python-dotenv
   - Pillow
```

### "Image Generation Failed"
```
Possible causes:
1. API key lacks Imagen 3 access → Fallback should work
2. Rate limit exceeded → Wait and retry
3. Content policy violation → Try different image
```

### App stuck on "Loading"
```
Solution:
1. Check Streamlit Cloud logs (Manage app → Logs)
2. Look for Python errors
3. Verify all files are pushed to GitHub
```

---

## Sharing for Testing

Your deployed app URL format:
```
https://YOUR_USERNAME-ai-virtual-photographer-app-streamlit-XXXXX.streamlit.app
```

### Message Template for Consumer:

```
Hi! Here's our AI Virtual Photographer demo:

🔗 Link: [YOUR_APP_URL]

📌 How to Test:
1. Click the link above
2. Upload a photo of Indian ethnic wear (kurta, lehenga, etc.)
3. Configure preferences (gender, pose, background)
4. Click "Generate Try-On"
5. Wait ~30-60 seconds for AI magic!

💡 Best Photos to Upload:
- Clear, well-lit garment photos
- Flat-lay or mannequin shots work best
- Kurtas, sherwanis, lehengas, sarees

📝 Please Share:
- Did the try-on look realistic?
- Were colors/patterns preserved?
- Any issues or suggestions?

Thank you for testing! 🙏
```

---

## Cost Information

| Service | Cost |
|---------|------|
| **Streamlit Cloud** | FREE for public apps |
| **Gemini API** | Free tier: ~60 requests/min |
| **Imagen 3** | Free tier: Limited usage |

Check your usage: https://aistudio.google.com

---

## Quick Reference Commands

```powershell
# Local development
cd d:\image_gen
venv\Scripts\activate
streamlit run app/streamlit_app.py

# Git commands
git add .
git commit -m "Update message"
git push

# View logs
streamlit logs  # Local only
```

---

## Next Steps After Testing

1. ✅ Deploy to Streamlit Cloud
2. ✅ Share link with test consumer
3. 📝 Collect feedback
4. 🔄 Iterate based on feedback
5. 🚀 Plan advanced features (see IMPROVEMENT_PLAN.md)
