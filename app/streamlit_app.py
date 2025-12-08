"""
AI Virtual Photographer - Streamlit Web Application

A stunning web interface for virtual try-on of Indian ethnic wear.
Optimized for Streamlit Cloud deployment.
"""

import io
import sys
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st
from PIL import Image

# Import with error handling for deployment
try:
    from config.settings import settings
    from schemas.garment_schema import GarmentDescription
    from schemas.generation_request import Gender, PoseStyle, BackgroundStyle, ModelPreferences
    from agents.garment_understanding_agent import analyze_garment
    from agents.prompt_builder_agent import build_image_prompt
    from agents.tryon_generation_agent import generate_tryon_image
    from agents.quality_checker_agent import check_consistency
    from services.gemini_client import GeminiClientError
    from utils.image_utils import validate_image
except ImportError as e:
    st.error(f"Import error: {e}")
    st.stop()


# ==============================================
# Page Configuration
# ==============================================
st.set_page_config(
    page_title="AI Virtual Photographer | Indian Ethnic Wear",
    page_icon="📸",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# AI Virtual Photographer\nTransform garment images into virtual try-on photos."
    }
)

# ==============================================
# Custom CSS for Premium UI
# ==============================================
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        --success-color: #10B981;
        --warning-color: #F59E0B;
        --error-color: #EF4444;
    }
    
    /* Header styling */
    .main-header {
        font-size: 2.8rem;
        font-weight: 800;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        padding: 1rem 0;
    }
    
    .sub-header {
        font-size: 1.2rem;
        color: #6B7280;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    /* Card styling */
    .feature-card {
        background: linear-gradient(145deg, #ffffff, #f3f4f6);
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
        margin-bottom: 1rem;
    }
    
    /* Status badges */
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 9999px;
        font-size: 0.875rem;
        font-weight: 500;
    }
    
    .status-success {
        background-color: #D1FAE5;
        color: #065F46;
    }
    
    .status-warning {
        background-color: #FEF3C7;
        color: #92400E;
    }
    
    .status-error {
        background-color: #FEE2E2;
        color: #991B1B;
    }
    
    /* Button styling */
    .stButton>button {
        width: 100%;
        border-radius: 12px;
        padding: 0.75rem 1.5rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* File uploader */
    .stFileUploader {
        border: 2px dashed #667eea;
        border-radius: 16px;
        padding: 2rem;
        background: linear-gradient(145deg, #f8fafc, #ffffff);
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        font-weight: 600;
        color: #374151;
    }
    
    /* Footer */
    .footer {
        text-align: center;
        padding: 2rem;
        color: #9CA3AF;
        border-top: 1px solid #E5E7EB;
        margin-top: 3rem;
    }
    
    /* Hide Streamlit branding for cleaner look */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Responsive adjustments */
    @media (max-width: 768px) {
        .main-header {
            font-size: 2rem;
        }
    }
</style>
""", unsafe_allow_html=True)


# ==============================================
# Session State Initialization
# ==============================================
if "garment_description" not in st.session_state:
    st.session_state.garment_description = None
if "uploaded_image_bytes" not in st.session_state:
    st.session_state.uploaded_image_bytes = None
if "generated_image_bytes" not in st.session_state:
    st.session_state.generated_image_bytes = None
if "prompt_used" not in st.session_state:
    st.session_state.prompt_used = None
if "generation_count" not in st.session_state:
    st.session_state.generation_count = 0


# ==============================================
# Helper Functions
# ==============================================
def display_garment_description(desc: GarmentDescription):
    """Display garment description in a beautiful format."""
    
    # Summary card
    st.markdown(f"""
    <div class="feature-card">
        <h4>📋 Garment Summary</h4>
        <p style="font-size: 1.1rem; color: #374151;">{desc.get_summary()}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Details in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏷️ Basic Info")
        if desc.garment_type:
            st.write(f"**Type:** {desc.garment_type}")
        if desc.gender_usage:
            st.write(f"**For:** {', '.join(desc.gender_usage)}")
        if desc.occasion:
            st.write(f"**Occasion:** {', '.join(desc.occasion)}")
        if desc.region_inspiration:
            st.write(f"**Style:** {', '.join(desc.region_inspiration)}")
        
        st.markdown("#### 🎨 Colors")
        if desc.colors:
            if desc.colors.primary:
                st.markdown(f"🔵 **Primary:** {desc.colors.primary}")
            if desc.colors.secondary:
                st.markdown(f"🟣 **Secondary:** {', '.join(desc.colors.secondary)}")
    
    with col2:
        st.markdown("#### 📐 Silhouette")
        if desc.silhouette:
            if desc.silhouette.length:
                st.write(f"**Length:** {desc.silhouette.length}")
            if desc.silhouette.fit:
                st.write(f"**Fit:** {desc.silhouette.fit}")
            if desc.silhouette.sleeve:
                st.write(f"**Sleeve:** {desc.silhouette.sleeve}")
            if desc.silhouette.neckline:
                st.write(f"**Neckline:** {desc.silhouette.neckline}")
        
        st.markdown("#### 🧵 Fabric")
        if desc.fabrics:
            for fab in desc.fabrics[:3]:  # Limit to 3
                if fab.name:
                    st.write(f"• {fab.name}")
    
    # Embroidery section
    if desc.embroidery:
        st.markdown("#### ✨ Embroidery Details")
        for emb in desc.embroidery[:2]:  # Limit to 2
            parts = []
            if emb.style:
                parts.append(f"**{emb.style}**")
            if emb.motifs:
                parts.append(f"motifs: {', '.join(emb.motifs[:3])}")
            if emb.density:
                parts.append(f"({emb.density} density)")
            if parts:
                st.write(" | ".join(parts))


def show_demo_instructions():
    """Show demo mode instructions."""
    with st.expander("ℹ️ How to Use This Demo", expanded=False):
        st.markdown("""
        ### Quick Start Guide
        
        1. **Upload a Garment Image** 📤
           - Use a clear photo of Indian ethnic wear
           - Flat-lay, mannequin, or catalog shots work best
           
        2. **Analyze the Garment** 🔍
           - Click "Analyze Garment" to see AI-detected details
           - Review colors, patterns, embroidery info
           
        3. **Configure Preferences** ⚙️
           - Choose gender, pose, and background
           - Add any special styling notes
           
        4. **Generate Try-On Image** ✨
           - Click "Generate" and wait ~30 seconds
           - Download your virtual try-on result!
        
        ---
        
        **🇮🇳 Best Results With:**
        - Kurtas, Sherwanis, Lehengas
        - Sarees, Anarkalis, Indo-western
        - Clear embroidery/pattern visibility
        """)


# ==============================================
# Main Application
# ==============================================
def main():
    # Header
    st.markdown('<h1 class="main-header">📸 AI Virtual Photographer</h1>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Transform your Indian ethnic wear into stunning virtual try-on photos</p>',
        unsafe_allow_html=True
    )
    
    # Check API configuration
    if not settings.validate():
        st.error("⚠️ API Key not configured!")
        st.info("""
        **For Demo Access:**
        This demo requires a Gemini API key. Please contact the administrator 
        or set up your own instance with your API key.
        
        Get your API key at: https://aistudio.google.com/apikey
        """)
        st.stop()
    
    # Demo instructions
    show_demo_instructions()
    
    # Sidebar configuration
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")
        
        st.markdown("### 👤 Model Preferences")
        
        gender = st.selectbox(
            "Target Gender",
            options=["Auto-detect from garment", "Female", "Male"],
            help="Select the gender for the virtual model"
        )
        
        pose = st.selectbox(
            "Pose Style",
            options=[ps.value for ps in PoseStyle],
            index=0,
            help="How should the model pose?"
        )
        
        background = st.selectbox(
            "Background",
            options=[bs.value for bs in BackgroundStyle],
            index=0,
            help="Choose the backdrop"
        )
        
        st.markdown("### 🎨 Styling")
        
        age_range = st.selectbox(
            "Age Range",
            options=["young adult (20-30)", "adult (30-40)", "mature (40+)"],
            index=0
        )
        
        additional_styling = st.text_area(
            "Additional Notes",
            placeholder="e.g., Add traditional jewelry, minimal makeup...",
            help="Any extra styling preferences"
        )
        
        st.divider()
        
        # Stats
        st.markdown("### 📊 Session Stats")
        st.metric("Images Generated", st.session_state.generation_count)
        
        st.divider()
        
        # About
        st.markdown("### ℹ️ About")
        st.caption(f"""
        **Models Used:**
        - Vision: {settings.TEXT_VISION_MODEL_ID}
        - Generation: {settings.IMAGE_MODEL_ID}
        
        **Powered by Google Gemini AI**
        """)
    
    # Main content - Two columns
    col_input, col_output = st.columns([1, 1], gap="large")
    
    # Left column - Input
    with col_input:
        st.markdown("### 📤 Upload Garment")
        
        uploaded_file = st.file_uploader(
            "Drop your garment image here",
            type=["jpg", "jpeg", "png", "webp"],
            help="Supported: JPEG, PNG, WebP (max 10MB)"
        )
        
        if uploaded_file:
            image_bytes = uploaded_file.read()
            st.session_state.uploaded_image_bytes = image_bytes
            
            # Validate
            is_valid, message = validate_image(image_bytes)
            
            if is_valid:
                st.image(image_bytes, caption="Your Garment", use_container_width=True)
                st.success(f"✅ {message}")
                
                # Action buttons
                st.markdown("---")
                
                col_btn1, col_btn2 = st.columns(2)
                
                with col_btn1:
                    analyze_btn = st.button(
                        "🔍 Analyze Garment",
                        type="secondary",
                        use_container_width=True,
                        help="Extract garment details with AI"
                    )
                
                with col_btn2:
                    generate_btn = st.button(
                        "✨ Generate Try-On",
                        type="primary",
                        use_container_width=True,
                        help="Create virtual try-on image"
                    )
                
                # Handle Analyze
                if analyze_btn:
                    with st.spinner("🧠 Analyzing garment with AI..."):
                        try:
                            description = analyze_garment(image_bytes)
                            st.session_state.garment_description = description
                            st.success("Analysis complete! See results on the right →")
                            st.rerun()
                        except Exception as e:
                            st.error(f"❌ Analysis failed: {str(e)}")
                
                # Handle Generate
                if generate_btn:
                    with st.spinner("🎨 Generating virtual try-on... (This takes ~30 seconds)"):
                        try:
                            # Build preferences
                            gender_value = None
                            if gender == "Female":
                                gender_value = Gender.FEMALE
                            elif gender == "Male":
                                gender_value = Gender.MALE
                            
                            preferences = ModelPreferences(
                                gender=gender_value,
                                pose=PoseStyle(pose),
                                background=BackgroundStyle(background),
                                age_range=age_range.split(" ")[0],
                                additional_styling=additional_styling if additional_styling else None
                            )
                            
                            # Generate
                            generated_bytes, description, prompt = generate_tryon_image(
                                image_bytes,
                                preferences=preferences,
                                cached_description=st.session_state.garment_description
                            )
                            
                            st.session_state.generated_image_bytes = generated_bytes
                            st.session_state.garment_description = description
                            st.session_state.prompt_used = prompt
                            st.session_state.generation_count += 1
                            
                            st.success("✅ Try-on image generated!")
                            st.rerun()
                            
                        except GeminiClientError as e:
                            st.error(f"❌ Generation failed: {str(e)}")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
            else:
                st.error(f"❌ {message}")
                st.session_state.uploaded_image_bytes = None
        else:
            # Placeholder when no image
            st.markdown("""
            <div style="background: linear-gradient(145deg, #f8fafc, #e2e8f0); 
                        border-radius: 16px; padding: 3rem; text-align: center;
                        border: 2px dashed #94a3b8;">
                <h3 style="color: #475569;">📤 Upload a Garment Image</h3>
                <p style="color: #64748b;">
                    Drag and drop or click to browse<br>
                    <small>Supports: JPEG, PNG, WebP</small>
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Right column - Output
    with col_output:
        st.markdown("### 🎨 Results")
        
        # Tabs for different outputs
        tab1, tab2, tab3 = st.tabs(["🖼️ Try-On Image", "📋 Analysis", "🔧 Details"])
        
        with tab1:
            if st.session_state.generated_image_bytes:
                st.image(
                    st.session_state.generated_image_bytes,
                    caption="AI-Generated Virtual Try-On",
                    use_container_width=True
                )
                
                # Download button
                col_dl1, col_dl2 = st.columns(2)
                with col_dl1:
                    st.download_button(
                        label="📥 Download Image",
                        data=st.session_state.generated_image_bytes,
                        file_name=f"tryon_{st.session_state.generation_count}.png",
                        mime="image/png",
                        use_container_width=True
                    )
                with col_dl2:
                    if st.button("🔄 Regenerate", use_container_width=True):
                        st.session_state.generated_image_bytes = None
                        st.rerun()
            else:
                st.markdown("""
                <div style="background: linear-gradient(145deg, #faf5ff, #ede9fe); 
                            border-radius: 16px; padding: 3rem; text-align: center;">
                    <h3 style="color: #7c3aed;">✨ Your Try-On Image</h3>
                    <p style="color: #8b5cf6;">
                        Upload a garment and click "Generate Try-On"<br>
                        to see the magic happen!
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        with tab2:
            if st.session_state.garment_description:
                display_garment_description(st.session_state.garment_description)
            else:
                st.info("Click 'Analyze Garment' to see AI-detected details")
        
        with tab3:
            if st.session_state.prompt_used:
                st.markdown("#### 📝 Generation Prompt")
                with st.expander("View Full Prompt", expanded=False):
                    st.code(st.session_state.prompt_used, language=None)
            
            if st.session_state.garment_description:
                st.markdown("#### 📄 Raw JSON Data")
                with st.expander("View JSON", expanded=False):
                    st.json(st.session_state.garment_description.model_dump(exclude_none=True))
    
    # Footer
    st.markdown("""
    <div class="footer">
        <p>
            <strong>AI Virtual Photographer</strong> | 
            Powered by Google Gemini AI | 
            Made for Indian Ethnic Wear Brands
        </p>
        <p style="font-size: 0.8rem;">
            🇮🇳 Celebrating the Beauty of Indian Fashion
        </p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
