import streamlit as st
import pandas as pd
import io
import base64
import time
import tempfile
from datetime import datetime

from backend1_integration import chat_with_agents, build_index  # (logic unchanged)

# ----------------------------------
# Page configuration
# ----------------------------------
st.set_page_config(
    page_title="InsightPilot - AI PowerBI Report Assistant",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ----------------------------------
# Enhanced CSS – Professional SaaS Design
# ----------------------------------
st.markdown("""
<style>
/* ====== Font & Base Styles ====== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
html, body, [class*="css"] { 
    font-family: 'Inter', sans-serif; 
    background-color: #f8fafc;
}

/* ====== Page Layout ====== */
.block-container { 
    padding-top: 0rem !important; 
    padding-bottom: 2rem !important;
    max-width: 1200px !important;
}

/* ====== Header Section ====== */
.header-container {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    padding: 2.5rem 0;
    margin: -1rem -1rem 2rem -1rem;
    border-radius: 0 0 24px 24px;
    text-align: center;
    color: white;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
    position: relative;
    overflow: hidden;
}

.header-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: url('data:image/svg+xml,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><defs><pattern id="grain" width="100" height="100" patternUnits="userSpaceOnUse"><circle cx="50" cy="50" r="1" fill="white" opacity="0.1"/></pattern></defs><rect width="100" height="100" fill="url(%23grain)"/></svg>');
    opacity: 0.3;
}

.header-title { 
    font-size: 3rem; 
    font-weight: 800; 
    margin: 0 0 0.5rem 0; 
    position: relative;
    z-index: 1;
    text-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.header-subtitle { 
    font-size: 1.1rem; 
    font-weight: 400; 
    opacity: 0.9; 
    margin: 0;
    position: relative;
    z-index: 1;
}

/* ====== Section Headers ====== */
.section-header {
    background: white;
    border-radius: 16px;
    padding: 1.5rem 2rem;
    margin: 2rem 0 1.5rem 0;
    box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    border: 1px solid #e2e8f0;
}

.section-title {
    font-size: 1.5rem; 
    font-weight: 700; 
    margin: 0;
    color: #1e293b;
    display: flex; 
    align-items: center; 
    gap: 0.75rem;
}

.section-subtitle {
    font-size: 0.95rem;
    color: #64748b;
    margin: 0.5rem 0 0 0;
    font-weight: 400;
}

/* ====== Upload Area ====== */
.upload-container {
    background: white;
    border-radius: 20px;
    padding: 2.5rem;
    margin: 1.5rem 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
    border: 2px dashed #cbd5e1;
    transition: all 0.3s ease;
    position: relative;
    overflow: hidden;
}

.upload-container:hover {
    border-color: #667eea;
    box-shadow: 0 12px 40px rgba(102, 126, 234, 0.15);
    transform: translateY(-2px);
}

.upload-container::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.02) 0%, rgba(118, 75, 162, 0.02) 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
}

.upload-container:hover::before {
    opacity: 1;
}

.upload-title {
    text-align: center;
    color: #1e293b;
    margin: 0 0 1rem 0;
    font-size: 1.25rem;
    font-weight: 600;
    position: relative;
    z-index: 1;
}

/* Streamlit File Uploader Styling */
[data-testid="stFileUploader"] {
    position: relative;
    z-index: 1;
}

[data-testid="stFileUploader"] section {
    padding: 0 !important;
    border: none !important;
}

[data-testid="stFileUploaderDropzone"] {
    min-height: 120px !important;
    padding: 2rem !important;
    border: 2px dashed #cbd5e1 !important;
    background: #f8fafc !important;
    border-radius: 16px !important;
    transition: all 0.3s ease !important;
}

[data-testid="stFileUploaderDropzone"]:hover {
    border-color: #667eea !important;
    background: #f1f5f9 !important;
}

[data-testid="stFileUploader"] svg {
    width: 24px !important;
    height: 24px !important;
    color: #667eea !important;
}

/* Hide file uploader help text */
[data-testid="stFileUploader"] > div > div:nth-child(2) {
    display: none !important;
}

/* ====== Analysis Type Buttons ====== */
.analysis-buttons {
    display: flex;
    gap: 1rem;
    margin: 1.5rem 0;
}

.analysis-button {
    flex: 1;
    background: white;
    border: 2px solid #e2e8f0;
    border-radius: 16px;
    padding: 1.5rem;
    text-align: center;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.04);
}

.analysis-button:hover {
    border-color: #667eea;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.15);
    transform: translateY(-2px);
}

.analysis-button.selected {
    border-color: #667eea;
    background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
}

/* ====== Cards & Content Areas ====== */
.content-card {
    background: white;
    border-radius: 20px;
    padding: 2rem 2.5rem;
    margin: 1.5rem 0;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.06);
    border: 1px solid #e2e8f0;
    position: relative;
    overflow: hidden;
}

.content-card::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 4px;
    height: 100%;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.content-card--success::before {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.content-card--preview::before {
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.card-title {
    font-size: 1.4rem;
    font-weight: 700;
    margin: 0 0 1rem 0;
    color: #1e293b;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.card-subtitle {
    font-size: 1.1rem;
    font-weight: 600;
    margin: 1.5rem 0 0.75rem 0;
    color: #374151;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* ====== Status Messages ====== */
.status-message {
    padding: 1.25rem 1.5rem;
    border-radius: 12px;
    margin: 1rem 0;
    font-size: 0.95rem;
    line-height: 1.5;
    border-left: 4px solid;
}

.status-message--success {
    background: #ecfdf5;
    color: #065f46;
    border-left-color: #10b981;
}

.status-message--error {
    background: #fef2f2;
    color: #991b1b;
    border-left-color: #ef4444;
}

.status-message--info {
    background: #eff6ff;
    color: #1e40af;
    border-left-color: #3b82f6;
}

/* ====== Buttons ====== */
.stButton > button {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3) !important;
    text-transform: none !important;
}

.stButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.4) !important;
}

.stButton > button:active {
    transform: translateY(0) !important;
}

/* Secondary Button Style */
.secondary-button > button {
    background: white !important;
    color: #667eea !important;
    border: 2px solid #667eea !important;
    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.1) !important;
}

.secondary-button > button:hover {
    background: #667eea !important;
    color: white !important;
}

/* ====== Download Button ====== */
.stDownloadButton > button {
    background: linear-gradient(135deg, #10b981 0%, #059669 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.75rem 2rem !important;
    font-weight: 600 !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 16px rgba(16, 185, 129, 0.3) !important;
}

.stDownloadButton > button:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 8px 32px rgba(16, 185, 129, 0.4) !important;
}

/* ====== Progress Bar ====== */
[data-testid="stProgress"] div[role="progressbar"] {
    height: 8px !important;
    border-radius: 999px !important;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}

/* ====== Data Preview ====== */
.dataframe-container {
    background: #f8fafc;
    border-radius: 12px;
    padding: 1rem;
    margin: 1rem 0;
    border: 1px solid #e2e8f0;
}

/* ====== Footer ====== */
.footer {
    text-align: center;
    padding: 2rem 0;
    color: #64748b;
    border-top: 1px solid #e2e8f0;
    margin-top: 3rem;
    font-size: 0.9rem;
    background: white;
    border-radius: 16px 16px 0 0;
}

.footer-brand {
    font-weight: 600;
    color: #667eea;
}

/* ====== Responsive Design ====== */
@media (max-width: 768px) {
    .header-title {
        font-size: 2.2rem;
    }
    
    .content-card {
        padding: 1.5rem;
        margin: 1rem 0;
    }
    
    .upload-container {
        padding: 1.5rem;
    }
    
    .analysis-buttons {
        flex-direction: column;
    }
}

/* ====== Hide Streamlit Elements ====== */
#MainMenu, header, footer {
    visibility: hidden;
}

.stDeployButton {
    display: none;
}

/* ====== Animations ====== */
@keyframes fadeInUp {
    from {
        opacity: 0;
        transform: translateY(20px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.fade-in-up {
    animation: fadeInUp 0.6s ease-out;
}

/* ====== Loading Spinner ====== */
.stSpinner > div {
    border-color: #667eea !important;
}
</style>
""", unsafe_allow_html=True)

# ----------------------------------
# Helper Functions (unchanged)
# ----------------------------------
def create_download_link(file_path, file_name):
    try:
        with open(file_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        return f'<a href="data:application/pdf;base64,{b64}" download="{file_name}">📥 Download Report PDF</a>'
    except FileNotFoundError:
        return "❌ File not found. Please try generating the report again."

def extract_pdf_text(pdf_file):
    try:
        import fitz  # PyMuPDF
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(pdf_file.read())
            path = tmp.name
        doc = fitz.open(path)
        return "\n".join([p.get_text() for p in doc])
    except Exception as e:
        st.error(f"Error reading PDF: {str(e)}")
        return None

# ----------------------------------
# Main Application
# ----------------------------------
def main():
    # ---- Enhanced Header ----
    st.markdown("""
    <div class="header-container fade-in-up">
        <div class="header-title">🚀 InsightPilot</div>
        <div class="header-subtitle">Your AI PowerBI Report Assistant</div>
    </div>
    """, unsafe_allow_html=True)

    # ---- Session State Initialization ----
    for k, v in {
        'analysis_complete': False,
        'analysis_result': None,
        'pdf_path': None,
        'file_type': None,
        'uploaded_file_name': None
    }.items():
        st.session_state.setdefault(k, v)

    # ---- Analysis Type Selection ----
    st.markdown("""
    <div class="section-header fade-in-up">
        <div class="section-title">📁 Select Analysis Type</div>
        <div class="section-subtitle">Choose the type of file you want to analyze with AI</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="medium")
    
    with col1:
        csv_selected = st.button(
            "📊 CSV Dataset Analysis", 
            use_container_width=True,
            help="Upload CSV files for comprehensive data analysis and insights"
        )
    
    with col2:
        pdf_selected = st.button(
            "📋 PDF Report Analysis", 
            use_container_width=True,
            help="Upload Power BI PDF reports for detailed section-wise analysis"
        )

    if csv_selected:
        st.session_state.file_type = "csv"
    if pdf_selected:
        st.session_state.file_type = "pdf"

    # ---- File Upload Section ----
    if st.session_state.file_type:
        file_type_display = st.session_state.file_type.upper()
        
        st.markdown(f"""
        <div class="upload-container fade-in-up">
            <div class="upload-title">📤 Upload your {file_type_display} file</div>
        </div>
        """, unsafe_allow_html=True)

        if st.session_state.file_type == "csv":
            uploaded_file = st.file_uploader(
                "Choose a CSV file",
                type=['csv'],
                help="Upload your CSV file for AI-powered analysis and insights",
                label_visibility="collapsed",
                key="csv_uploader"
            )
        else:
            uploaded_file = st.file_uploader(
                "Choose a PDF file",
                type=['pdf'],
                help="Upload your Power BI PDF report for detailed analysis",
                label_visibility="collapsed",
                key="pdf_uploader"
            )

        # ---- File Upload Success ----
        if uploaded_file is not None:
            st.session_state.uploaded_file_name = uploaded_file.name
            size_mb = len(uploaded_file.getvalue()) / 1024 / 1024
            
            st.markdown(f"""
            <div class="status-message status-message--success fade-in-up">
                <strong>✅ File uploaded successfully!</strong><br>
                📄 <strong>Name:</strong> {uploaded_file.name}<br>
                📏 <strong>Size:</strong> {size_mb:.2f} MB<br>
                🗂️ <strong>Type:</strong> {st.session_state.file_type.upper()} Analysis
            </div>
            """, unsafe_allow_html=True)

            # ---- CSV Preview ----
            if st.session_state.file_type == "csv":
                try:
                    df = pd.read_csv(uploaded_file, encoding='latin-1')
                    
                    st.markdown("""
                    <div class="content-card fade-in-up">
                        <div class="card-title">👀 Dataset Preview</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("📊 Total Rows", f"{df.shape[0]:,}")
                    with col2:
                        st.metric("📋 Total Columns", f"{df.shape[1]:,}")
                    with col3:
                        st.metric("💾 Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024:.1f} KB")
                    
                    st.markdown('<div class="dataframe-container">', unsafe_allow_html=True)
                    st.dataframe(df.head(10), use_container_width=True)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                except Exception as e:
                    st.markdown(f"""
                    <div class="status-message status-message--error">
                        ❌ <strong>Error reading CSV file:</strong> {str(e)}
                    </div>
                    """, unsafe_allow_html=True)

            # ---- Analysis Button ----
            st.markdown("<br>", unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔍 Start AI Analysis", use_container_width=True, type="primary"):
                    
                    # Progress indicator
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    try:
                        # Step 1: Initialize
                        status_text.markdown("🔧 **Initializing AI systems...**")
                        progress_bar.progress(20)
                        time.sleep(0.5)
                        
                        query_engine = build_index()
                        
                        # Step 2: Process file
                        status_text.markdown("📄 **Processing your file...**")
                        progress_bar.progress(40)
                        time.sleep(0.5)
                        
                        if st.session_state.file_type == "csv":
                            file_content = io.BytesIO(uploaded_file.getvalue())
                        else:
                            pdf_text = extract_pdf_text(uploaded_file)
                            if pdf_text is None:
                                st.error("Failed to extract text from PDF. Please try again.")
                                st.stop()
                            file_content = pdf_text

                        # Step 3: AI Analysis
                        status_text.markdown("🤖 **AI agents are analyzing your data...**")
                        progress_bar.progress(60)
                        time.sleep(0.5)

                        result, pdf_path = chat_with_agents(
                            file_type=st.session_state.file_type,
                            file_content=file_content,
                            query_engine=query_engine
                        )

                        # Step 4: Finalize
                        status_text.markdown("📊 **Generating insights and reports...**")
                        progress_bar.progress(90)
                        time.sleep(0.5)
                        
                        st.session_state.analysis_result = result
                        st.session_state.pdf_path = pdf_path
                        st.session_state.analysis_complete = True
                        
                        progress_bar.progress(100)
                        status_text.markdown("✅ **Analysis complete!**")
                        time.sleep(1)
                        
                        # Clear progress indicators
                        progress_bar.empty()
                        status_text.empty()
                        
                        st.rerun()

                    except Exception as e:
                        progress_bar.empty()
                        status_text.empty()
                        
                        st.markdown(f"""
                        <div class="status-message status-message--error">
                            ❌ <strong>Analysis failed:</strong> {str(e)}
                        </div>
                        """, unsafe_allow_html=True)

    # ---- Results Section ----
    if st.session_state.analysis_complete and st.session_state.analysis_result:
        
        # Analysis Results
        st.markdown("""
        <div class="content-card content-card--success fade-in-up">
            <div class="card-title">📊 Analysis Results</div>
            <div class="card-subtitle">🎯 AI-Generated Insights</div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown(st.session_state.analysis_result)

        # Report Preview
        st.markdown("""
        <div class="content-card content-card--preview fade-in-up">
            <div class="card-title">📋 Generated Report Preview</div>
        </div>
        """, unsafe_allow_html=True)

        lines = str(st.session_state.analysis_result).split('\n')
        preview_lines = [l for l in lines if l.strip() and not l.startswith('        ')][:5]
        preview_text = '\n'.join(preview_lines)

        col1, col2 = st.columns([2, 1])
        with col1:
            st.markdown(f"""
            **Report Summary:**  
            {preview_text}...
            
            **Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}  
            **File Analyzed:** {st.session_state.uploaded_file_name}  
            **Analysis Type:** {st.session_state.file_type.upper()}
            """)
        
        with col2:
            if st.session_state.pdf_path:
                with open(st.session_state.pdf_path, "rb") as pdf_file:
                    st.download_button(
                        label="📥 Download Full Report (PDF)",
                        data=pdf_file,
                        file_name=f"insightpilot_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                        type="primary"
                    )

        # New Analysis Button
        st.markdown("<br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("🔄 Start New Analysis", use_container_width=True, key="new_analysis"):
                for key in [
                    'analysis_complete', 'analysis_result', 'pdf_path',
                    'file_type', 'uploaded_file_name'
                ]:
                    if key in st.session_state:
                        del st.session_state[key]
                st.rerun()

    # ---- Footer ----
    st.markdown("""
    <div class="footer">
        🚀 <span class="footer-brand">InsightPilot</span> • Powered by CrewAI & OpenAI
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
