# 📸 AI Virtual Photographer for Indian Ethnic Wear

An agentic AI service that transforms garment images into realistic virtual try-on photos. Upload a product image of a kurta, sherwani, lehenga, or any Indian ethnic wear, and get a photorealistic image of a model wearing that exact garment.

![Architecture](https://img.shields.io/badge/Architecture-Agentic_AI-purple)
![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Gemini](https://img.shields.io/badge/Powered_by-Google_Gemini-orange)

## 🎯 What This Does

- **Input**: A garment image (flat-lay, mannequin, or catalog shot)
- **Output**: A photorealistic image of a human model wearing that garment

The system preserves:
- ✅ Embroidery patterns and placement
- ✅ Color accuracy (primary and secondary)
- ✅ Fabric texture and drape
- ✅ Pattern integrity (geometric, floral, etc.)
- ✅ Cultural styling elements

## 🏗️ Architecture

The system uses an **agentic architecture** with specialized agents:

```
┌─────────────────────────────────────────────────────────────────┐
│                    AI Virtual Photographer                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │   Garment        │    │   Prompt         │                   │
│  │   Understanding  │───>│   Builder        │                   │
│  │   Agent          │    │   Agent          │                   │
│  └──────────────────┘    └──────────────────┘                   │
│         │                        │                               │
│         │ GarmentDescription     │ Rich Text Prompt             │
│         │ (JSON)                 │                               │
│         v                        v                               │
│  ┌──────────────────────────────────────────┐                   │
│  │         Try-On Generation Agent          │                   │
│  │         (Orchestrator)                   │                   │
│  └──────────────────────────────────────────┘                   │
│                        │                                         │
│                        v                                         │
│  ┌──────────────────┐    ┌──────────────────┐                   │
│  │   Quality        │<───│   Generated      │                   │
│  │   Checker Agent  │    │   Try-On Image   │                   │
│  └──────────────────┘    └──────────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Gemini Models Used:
- Gemini 2.0 Flash (Text+Vision) → Garment Understanding & Quality Check
- Imagen 3 (Image Generation) → Try-On Rendering
```

### Agent Roles

| Agent | Role | Gemini Model |
|-------|------|--------------|
| **Garment Understanding** | Analyzes garment images to extract structured details | Gemini 2.0 Flash |
| **Prompt Builder** | Converts JSON to rich generation prompt | N/A (logic only) |
| **Try-On Generation** | Orchestrates pipeline and generates images | Imagen 3 |
| **Quality Checker** | Validates generated images match originals | Gemini 2.0 Flash |

## 📁 Project Structure

```
image_gen/
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment template
│
├── config/
│   └── settings.py                    # API keys, model configs
│
├── schemas/
│   ├── garment_schema.py              # Pydantic models for garments
│   └── generation_request.py          # Request/response schemas
│
├── services/
│   └── gemini_client.py               # Unified Gemini API wrapper
│
├── agents/
│   ├── garment_understanding_agent.py # Vision analysis agent
│   ├── prompt_builder_agent.py        # Prompt construction
│   ├── tryon_generation_agent.py      # Image generation orchestrator
│   └── quality_checker_agent.py       # Quality validation
│
├── utils/
│   ├── logging_utils.py               # Logging configuration
│   └── image_utils.py                 # Image processing utilities
│
└── app/
    └── streamlit_app.py               # Web UI
```

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.10 or higher
- Google AI API Key with access to Gemini models

### 2. Setup

```bash
# Clone or navigate to the project
cd d:\image_gen

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure API Key

```bash
# Copy the example env file
copy .env.example .env

# Edit .env and add your API key
# GEMINI_API_KEY=your_api_key_here
```

Get your API key from: https://aistudio.google.com/apikey

### 4. Run the App

```bash
streamlit run app/streamlit_app.py
```

The app will open in your browser at `http://localhost:8501`

## 📖 How to Use

1. **Upload a Garment Image**
   - Use a clear product photo (flat-lay, mannequin, or model shot)
   - Supported formats: JPEG, PNG, WebP

2. **Analyze Garment** (Optional)
   - Click "Analyze Garment" to see the extracted details
   - Review the JSON to understand what the AI detected

3. **Configure Preferences**
   - Select target gender (or auto-detect)
   - Choose pose style
   - Select background
   - Add any additional styling notes

4. **Generate Try-On Image**
   - Click "Generate Try-On Image"
   - Wait for the AI to create the virtual try-on
   - Download the result

5. **Quality Check** (Optional)
   - Run quality check to compare original vs generated
   - Review any detected issues

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Your Google AI API key | Required |
| `GEMINI_TEXT_VISION_MODEL_ID` | Vision model ID | `gemini-2.0-flash-exp` |
| `GEMINI_IMAGE_MODEL_ID` | Image generation model | `imagen-3.0-generate-002` |
| `IMAGE_WIDTH` | Generated image width | `1024` |
| `IMAGE_HEIGHT` | Generated image height | `1024` |

### Garment Schema

The system uses a flexible JSON schema to represent garments:

```json
{
  "garment_type": "sherwani",
  "gender_usage": ["male"],
  "occasion": ["wedding", "festive"],
  "colors": {
    "primary": "ivory white",
    "secondary": ["gold"],
    "pattern_colors": ["gold thread"]
  },
  "embroidery": [{
    "style": "zardozi",
    "motifs": ["paisley", "floral"],
    "density": "heavy",
    "placement": ["front panel", "collar"]
  }],
  "silhouette": {
    "length": "knee-length",
    "fit": "fitted",
    "neckline": "bandhgala"
  }
}
```

## ⚠️ Limitations

1. **Pattern Preservation**: Complex patterns may not be perfectly preserved
2. **Embroidery Details**: Very fine embroidery details may be simplified
3. **Draping**: Complex draping (like saree pleats) is challenging
4. **Consistency**: Results may vary between generations

## 🔮 Future Improvements

- [ ] Fine-tune models on Indian ethnic wear dataset
- [ ] Add multiple angle generation
- [ ] Implement reference image conditioning
- [ ] Add batch processing for catalogs
- [ ] Build API endpoint for integration
- [ ] Add more pose and background options

## 🤝 Contributing

This is a learning project. Feel free to:
- Report issues
- Suggest improvements
- Add new features

## 📄 License

MIT License - feel free to use and modify for your projects.

---

**Built with ❤️ for Indian Ethnic Wear Brands**
