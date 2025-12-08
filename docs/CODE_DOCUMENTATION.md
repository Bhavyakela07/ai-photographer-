# AI Virtual Photographer - Complete Code Documentation

## Project Overview

This is an **agentic AI system** that transforms garment product images into virtual try-on photographs. The system analyzes Indian ethnic wear (kurtas, sherwanis, lehengas, etc.) and generates realistic images of models wearing those garments.

---

## Table of Contents

1. [Project Structure](#project-structure)
2. [Configuration Files](#configuration-files)
3. [Utility Modules](#utility-modules)
4. [Schema Definitions](#schema-definitions)
5. [Gemini Service Layer](#gemini-service-layer)
6. [Agent Layer](#agent-layer)
7. [Web Application](#web-application)
8. [Data Flow Diagram](#data-flow-diagram)

---

## Project Structure

```
d:\image_gen\
│
├── .env                    # Your API keys (not in git)
├── .env.example            # Template for environment variables
├── requirements.txt        # Python dependencies
├── README.md               # Project documentation
│
├── config/                 # Configuration management
│   ├── __init__.py
│   └── settings.py         # Loads environment variables
│
├── utils/                  # Utility functions
│   ├── __init__.py
│   ├── logging_utils.py    # Logging configuration
│   └── image_utils.py      # Image processing helpers
│
├── schemas/                # Data models (Pydantic)
│   ├── __init__.py
│   ├── garment_schema.py   # Garment description models
│   └── generation_request.py # API request/response models
│
├── services/               # External API wrappers
│   ├── __init__.py
│   └── gemini_client.py    # Google Gemini API client
│
├── agents/                 # AI agents (business logic)
│   ├── __init__.py
│   ├── garment_understanding_agent.py
│   ├── prompt_builder_agent.py
│   ├── tryon_generation_agent.py
│   └── quality_checker_agent.py
│
└── app/                    # Web application
    ├── __init__.py
    └── streamlit_app.py    # Streamlit UI
```

---

## Configuration Files

### File: `config/settings.py`

This file is the **central configuration hub**. It loads all settings from environment variables.

```python
# Line 1-6: Module docstring explaining purpose
"""
Configuration settings for AI Virtual Photographer.
This module loads environment variables and provides
centralized configuration for all agents and services.
"""

# Line 8-10: Import required modules
import os                    # For reading environment variables
from pathlib import Path     # For file path handling
from dotenv import load_dotenv  # For loading .env file

# Line 12-14: Load the .env file
env_path = Path(__file__).parent.parent / ".env"  # Go up one level, find .env
load_dotenv(env_path)  # Parse .env and load into os.environ
```

**Key Settings Explained:**

| Setting | Purpose | Default Value |
|---------|---------|---------------|
| `GEMINI_API_KEY` | Your Google AI API key | Required |
| `TEXT_VISION_MODEL_ID` | Model for analyzing images | `gemini-2.0-flash-exp` |
| `IMAGE_MODEL_ID` | Model for generating images | `imagen-3.0-generate-002` |
| `NATIVE_IMAGE_MODEL_ID` | Fallback image model | `gemini-2.0-flash-preview-image-generation` |
| `IMAGE_ASPECT_RATIO` | Output image dimensions | `3:4` (portrait) |
| `AUTO_QUALITY_KEYWORDS` | Add quality terms to prompts | `true` |

---

## Utility Modules

### File: `utils/logging_utils.py`

Provides consistent logging across all modules.

```python
def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Creates a logger with formatted output.
    
    Example output:
    2025-12-08 21:30:00 | INFO     | agent.GarmentUnderstanding | Starting analysis...
    """
    logger = logging.getLogger(name)
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger
```

**Usage in other files:**
```python
from utils.logging_utils import get_agent_logger
logger = get_agent_logger("GarmentUnderstanding")
logger.info("Processing garment image...")
```

---

### File: `utils/image_utils.py`

Handles image validation and processing.

**Key Functions:**

| Function | Purpose |
|----------|---------|
| `validate_image(bytes)` | Checks if bytes are valid JPEG/PNG/WEBP |
| `resize_if_needed(bytes)` | Shrinks images larger than 4096px |
| `image_to_base64(bytes)` | Converts to base64 for API calls |
| `get_mime_type(bytes)` | Detects image/jpeg, image/png, etc. |

```python
def validate_image(image_bytes: bytes) -> Tuple[bool, str]:
    """
    Returns (True, "Valid JPEG image (800x1200)") if valid
    Returns (False, "Invalid image: ...") if invalid
    """
    try:
        image = Image.open(io.BytesIO(image_bytes))
        image.verify()  # PIL's built-in validation
        return True, f"Valid {image.format} image ({image.size[0]}x{image.size[1]})"
    except Exception as e:
        return False, f"Invalid image: {str(e)}"
```

---

## Schema Definitions

### File: `schemas/garment_schema.py`

Defines the **structured representation** of a garment using Pydantic models.

**Why Pydantic?**
- Automatic validation of data types
- JSON serialization/deserialization
- Clear documentation via type hints

**Main Classes:**

```python
class Silhouette(BaseModel):
    """Shape and construction of the garment"""
    length: Optional[str] = None      # "knee-length", "ankle-length"
    fit: Optional[str] = None         # "straight", "A-line", "flared"
    sleeve: Optional[str] = None      # "full-sleeve", "half-sleeve"
    neckline: Optional[str] = None    # "bandhgala", "V-neck"

class Embroidery(BaseModel):
    """Embroidery details - crucial for Indian ethnic wear"""
    style: Optional[str] = None       # "zari", "zardozi", "chikankari"
    motifs: List[str] = []            # ["paisley", "floral", "peacock"]
    density: Optional[str] = None     # "heavy", "medium", "sparse"
    placement: List[str] = []         # ["front panel", "cuffs", "collar"]

class GarmentDescription(BaseModel):
    """Complete garment description - the main schema"""
    garment_type: Optional[str] = None       # "kurta", "sherwani", "lehenga"
    gender_usage: List[str] = []             # ["male"], ["female"]
    colors: Optional[Colors] = None          # Primary, secondary colors
    embroidery: List[Embroidery] = []        # All embroidery details
    patterns: List[Pattern] = []             # Printed/woven patterns
    silhouette: Optional[Silhouette] = None  # Shape details
    free_text_description: Optional[str] = None  # Rich description
```

**Why all fields are Optional:**
- The AI may not be able to detect every detail
- Some garments don't have embroidery, patterns, etc.
- Prevents errors when data is incomplete

---

### File: `schemas/generation_request.py`

Defines user preferences for image generation.

```python
class Gender(str, Enum):
    """Target gender for the generated model"""
    MALE = "male"
    FEMALE = "female"
    UNISEX = "unisex"

class PoseStyle(str, Enum):
    """Pose options for the generated image"""
    STANDING_FRONT = "standing front pose"
    STANDING_SIDE = "standing side pose with slight turn"
    WALKING = "elegant walking pose"
    TRADITIONAL = "traditional Indian pose with hands folded"

class ModelPreferences(BaseModel):
    """User's preferences for the generated image"""
    gender: Optional[Gender] = None
    pose: PoseStyle = PoseStyle.STANDING_FRONT
    background: BackgroundStyle = BackgroundStyle.STUDIO_WHITE
    age_range: Optional[str] = "young adult"
```

---

## Gemini Service Layer

### File: `services/gemini_client.py`

This is the **core integration** with Google's Gemini AI. All API calls go through this file.

**Class: `GeminiClient`**

```python
class GeminiClient:
    def __init__(self):
        # Initialize with API key from settings
        self._client = genai.Client(api_key=settings.GEMINI_API_KEY)
```

**Key Methods:**

#### 1. `analyze_image()` - Vision Analysis

```python
def analyze_image(self, image_bytes, system_prompt, user_prompt) -> str:
    """
    Sends image + prompts to Gemini Vision model.
    Returns: JSON string describing the garment.
    
    Flow:
    1. Convert image bytes to Part object
    2. Send to Gemini with prompts
    3. Return text response (JSON)
    """
    image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    
    response = self._client.models.generate_content(
        model=settings.TEXT_VISION_MODEL_ID,  # e.g., "gemini-2.0-flash-exp"
        contents=[full_prompt, image_part],
        config=types.GenerateContentConfig(
            temperature=0.2,  # Low = consistent output
        )
    )
    return response.text
```

#### 2. `generate_image()` - Image Generation

```python
def generate_image(self, prompt, reference_image_bytes=None) -> bytes:
    """
    Generates an image from text prompt.
    Returns: PNG image as bytes.
    
    Flow:
    1. Enhance prompt with quality keywords
    2. Try Imagen 3 first (best quality)
    3. Fall back to native Gemini generation if Imagen fails
    """
    enhanced_prompt = self._enhance_prompt_for_quality(prompt)
    
    if "imagen" in settings.IMAGE_MODEL_ID.lower():
        return self._generate_with_imagen(enhanced_prompt)
    else:
        return self._generate_with_native(enhanced_prompt)
```

#### 3. `_generate_with_imagen()` - Imagen 3 API

```python
def _generate_with_imagen(self, prompt) -> bytes:
    """Uses Google's Imagen 3 model for highest quality."""
    response = self._client.models.generate_images(
        model=settings.IMAGE_MODEL_ID,  # "imagen-3.0-generate-002"
        prompt=prompt,
        config=types.GenerateImagesConfig(
            number_of_images=1,
            aspect_ratio=settings.IMAGE_ASPECT_RATIO,  # "3:4"
            safety_filter_level=settings.SAFETY_FILTER_LEVEL,
        )
    )
    return response.generated_images[0].image.image_bytes
```

#### 4. `_enhance_prompt_for_quality()` - Quality Optimization

```python
def _enhance_prompt_for_quality(self, prompt) -> str:
    """Adds quality keywords to improve image output."""
    if not settings.AUTO_QUALITY_KEYWORDS:
        return prompt
    
    return f"""Create a high-quality, 4K, ultra-detailed image.
    
{prompt}

Technical requirements:
- Ultra high resolution and sharp details
- Professional studio lighting
- Photorealistic quality"""
```

---

## Agent Layer

The agents contain the **business logic**. Each agent has a specific responsibility.

### File: `agents/garment_understanding_agent.py`

**Purpose:** Analyze garment images and extract structured data.

```python
# System prompt - tells AI how to behave
SYSTEM_PROMPT = """You are an expert in Indian ethnic fashion.
You analyze garments and extract detailed information about:
- garment type (kurta, sherwani, lehenga, etc.)
- embroidery techniques (zari, zardozi, chikankari, etc.)
- patterns, colors, fabrics, silhouette
Return ONLY valid JSON following the schema."""

def analyze_garment(image_bytes: bytes) -> GarmentDescription:
    """
    Main function - analyzes a garment image.
    
    Steps:
    1. Validate the image (is it a real image?)
    2. Resize if too large (>4096px)
    3. Call Gemini API with vision prompt
    4. Parse JSON response into GarmentDescription
    5. Return structured data
    """
    # Step 1: Validate
    is_valid, message = validate_image(image_bytes)
    if not is_valid:
        raise ValueError(message)
    
    # Step 2: Resize
    image_bytes = resize_if_needed(image_bytes)
    
    # Step 3: Call API
    client = get_gemini_client()
    response_text = client.analyze_image(
        image_bytes=image_bytes,
        system_prompt=SYSTEM_PROMPT,
        user_prompt=_get_user_prompt()
    )
    
    # Step 4: Parse JSON
    garment_json = _extract_json_from_response(response_text)
    
    # Step 5: Return
    return GarmentDescription.model_validate(garment_json)
```

---

### File: `agents/prompt_builder_agent.py`

**Purpose:** Convert structured garment data into a rich text prompt for image generation.

```python
def build_image_prompt(garment: GarmentDescription, preferences: ModelPreferences) -> str:
    """
    Converts GarmentDescription JSON into natural language prompt.
    
    Example output:
    "Generate a high-quality studio photo of a female Indian model wearing:
    
    GARMENT: Lehenga
    Occasion: Suitable for wedding, festive
    
    COLORS (MUST be accurate):
    • Primary color: deep maroon
    • Secondary colors: gold, silver
    
    EMBROIDERY (preserve exactly):
    • Style: zardozi | Motifs: paisley, floral | Placement: front panel, border
    
    CRITICAL CONSTRAINTS:
    • The garment design MUST closely match the description
    • Do NOT change embroidery patterns or colors"
    """
    sections = [
        _build_intro_section(gender, preferences),   # Model description
        _build_garment_section(garment),             # Garment type
        _build_color_section(garment),               # Colors
        _build_embroidery_section(garment),          # Embroidery
        _build_pattern_section(garment),             # Patterns
        _build_silhouette_section(garment),          # Shape
        _build_technical_section(preferences),       # Background, lighting
        _build_constraints_section(),                # DON'T change rules
    ]
    return "\n\n".join(sections)
```

---

### File: `agents/tryon_generation_agent.py`

**Purpose:** Orchestrate the full pipeline from image input to generated output.

```python
def generate_tryon_image(
    garment_image_bytes: bytes,
    preferences: ModelPreferences = None,
    cached_description: GarmentDescription = None
) -> Tuple[bytes, GarmentDescription, str]:
    """
    Main orchestration function.
    
    Flow:
    1. Validate input image
    2. Analyze garment (or use cached)
    3. Build generation prompt
    4. Generate try-on image
    5. Return (image_bytes, description, prompt_used)
    """
    # Step 1: Validate
    is_valid, message = validate_image(garment_image_bytes)
    if not is_valid:
        raise ValueError(message)
    
    # Step 2: Analyze (or use cache)
    if cached_description:
        description = cached_description
    else:
        description = analyze_garment(garment_image_bytes)
    
    # Step 3: Build prompt
    prompt = build_image_prompt(description, preferences)
    
    # Step 4: Generate
    client = get_gemini_client()
    generated_bytes = client.generate_image(prompt=prompt)
    
    # Step 5: Return
    return generated_bytes, description, prompt
```

---

### File: `agents/quality_checker_agent.py`

**Purpose:** Validate that generated images match the original garment.

```python
def check_consistency(
    original_image_bytes: bytes,
    generated_image_bytes: bytes,
    garment: GarmentDescription
) -> QualityReport:
    """
    Compares original garment with generated try-on image.
    
    Returns QualityReport with:
    - color_match: bool
    - embroidery_match: bool
    - pattern_match: bool
    - silhouette_match: bool
    - overall_score: float (0.0-1.0)
    - issues: List[str]
    - recommendations: List[str]
    """
    client = get_gemini_client()
    
    # Send both images to Gemini for comparison
    response = client.compare_images(
        original_image_bytes,
        generated_image_bytes,
        COMPARISON_PROMPT
    )
    
    # Parse response into QualityReport
    return _parse_quality_response(response)
```

---

## Web Application

### File: `app/streamlit_app.py`

**Purpose:** Provide a web interface for users.

**Key Components:**

```python
# Page configuration
st.set_page_config(
    page_title="AI Virtual Photographer",
    page_icon="📸",
    layout="wide",
)

# Session state - persists data between interactions
if "garment_description" not in st.session_state:
    st.session_state.garment_description = None
if "generated_image_bytes" not in st.session_state:
    st.session_state.generated_image_bytes = None

# File uploader
uploaded_file = st.file_uploader(
    "Choose a garment image",
    type=["jpg", "jpeg", "png", "webp"],
)

# Analyze button
if st.button("🔍 Analyze Garment"):
    description = analyze_garment(image_bytes)
    st.session_state.garment_description = description
    display_garment_description(description)

# Generate button
if st.button("✨ Generate Try-On Image"):
    generated_bytes, description, prompt = generate_tryon_image(
        image_bytes,
        preferences=ModelPreferences(...),
    )
    st.session_state.generated_image_bytes = generated_bytes
    st.image(generated_bytes)
```

---

## Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           USER INTERFACE                                 │
│                        (streamlit_app.py)                               │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      TRY-ON GENERATION AGENT                            │
│                   (tryon_generation_agent.py)                           │
│                                                                         │
│  1. Receives garment image from UI                                      │
│  2. Calls Garment Understanding Agent                                   │
│  3. Calls Prompt Builder Agent                                          │
│  4. Calls Gemini Client for image generation                           │
│  5. Returns generated image to UI                                       │
└─────────────────────────────────────────────────────────────────────────┘
                    │                           │
                    ▼                           ▼
┌───────────────────────────────┐   ┌───────────────────────────────────┐
│  GARMENT UNDERSTANDING AGENT  │   │     PROMPT BUILDER AGENT          │
│ (garment_understanding_agent) │   │   (prompt_builder_agent.py)       │
│                               │   │                                   │
│ Input: Image bytes            │   │ Input: GarmentDescription         │
│ Output: GarmentDescription    │   │ Output: Rich text prompt          │
│                               │   │                                   │
│ Uses: Gemini Vision API       │   │ Uses: Pure Python logic           │
└───────────────────────────────┘   └───────────────────────────────────┘
                    │                           │
                    └─────────────┬─────────────┘
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         GEMINI CLIENT                                    │
│                      (gemini_client.py)                                 │
│                                                                         │
│  Methods:                                                               │
│  - analyze_image() → Calls Gemini 2.0 Flash (vision)                   │
│  - generate_image() → Calls Imagen 3 or native Gemini                  │
│  - compare_images() → Calls Gemini for quality check                   │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        GOOGLE GEMINI API                                │
│                     (External Cloud Service)                            │
│                                                                         │
│  Models Used:                                                           │
│  - gemini-2.0-flash-exp (Text + Vision)                                │
│  - imagen-3.0-generate-002 (Image Generation)                          │
│  - gemini-2.0-flash-preview-image-generation (Fallback)                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `GEMINI_API_KEY` | ✅ Yes | - | Your Google AI API key |
| `GEMINI_TEXT_VISION_MODEL_ID` | No | `gemini-2.0-flash-exp` | Vision analysis model |
| `GEMINI_IMAGE_MODEL_ID` | No | `imagen-3.0-generate-002` | Image generation model |
| `GEMINI_NATIVE_IMAGE_MODEL_ID` | No | `gemini-2.0-flash-preview-image-generation` | Fallback model |
| `IMAGE_ASPECT_RATIO` | No | `3:4` | Output image ratio |
| `IMAGE_COUNT` | No | `1` | Number of images to generate |
| `ENABLE_PROMPT_ENHANCEMENT` | No | `true` | AI prompt optimization |
| `AUTO_QUALITY_KEYWORDS` | No | `true` | Add quality terms |
| `ANALYSIS_TEMPERATURE` | No | `0.2` | Consistency vs creativity |
| `GENERATION_TEMPERATURE` | No | `0.9` | Image creativity |
| `SAFETY_FILTER_LEVEL` | No | `block_only_high` | Content filtering |

---

## Running the Application

```bash
# 1. Navigate to project
cd d:\image_gen

# 2. Activate virtual environment
venv\Scripts\activate

# 3. Set API key in .env file
# GEMINI_API_KEY=your_key_here

# 4. Run Streamlit
streamlit run app/streamlit_app.py
```

The app opens at `http://localhost:8501`

---

## Summary

| Component | File | Responsibility |
|-----------|------|----------------|
| Configuration | `config/settings.py` | Load environment variables |
| Logging | `utils/logging_utils.py` | Consistent log formatting |
| Image Utils | `utils/image_utils.py` | Validate, resize, convert images |
| Garment Schema | `schemas/garment_schema.py` | Define garment data structure |
| Request Schema | `schemas/generation_request.py` | Define user preferences |
| Gemini Client | `services/gemini_client.py` | API communication |
| Understanding Agent | `agents/garment_understanding_agent.py` | Analyze garment images |
| Prompt Builder | `agents/prompt_builder_agent.py` | Create generation prompts |
| Generation Agent | `agents/tryon_generation_agent.py` | Orchestrate pipeline |
| Quality Agent | `agents/quality_checker_agent.py` | Validate results |
| Web UI | `app/streamlit_app.py` | User interface |
