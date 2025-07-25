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
# CSS – compact, professional, boxed sections
# ----------------------------------
st.markdown("""
<style>
/* ====== Font ====== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
/* ====== Page shell ====== */
.block-container { padding-top: 0.5rem !important; }
.container-narrow { max-width: 1000px; margin: 0 auto; }
/* ====== Header (smaller) ====== */
.header-container{
  background: linear-gradient(135deg,#1f4e79 0%,#4a90e2 100%);
  padding: 1.1rem 0 1.3rem 0;   /* smaller */
  margin: -1rem -1rem 1.5rem -1rem;
  border-radius: 0 0 18px 18px;
  text-align:center; color:#fff;
}
.header-title{ font-size:2.2rem; font-weight:700; margin:0 0 .25rem 0; }
.header-subtitle{ font-size:0.95rem; font-weight:300; opacity:.9; margin:0; }
/* ====== Section titles ====== */
.section-title{
  font-size:1.35rem; font-weight:600; margin:0.75rem 0 0.5rem 0;
  display:flex; align-items:center; gap:.4rem;
}
/* ====== Upload box (smaller) ====== */
.upload-section{
  background:#fff; border-radius:12px;
  padding:1rem 1.2rem !important;   /* tighter */
  box-shadow:0 2px 10px rgba(0,0,0,.04);
  border:1px dashed #d0d7de; margin:1rem auto 1.25rem auto !important;
  transition:.25s; max-width:820px;
}
.upload-section:hover{ border-color:#4a90e2; box-shadow:0 6px 18px rgba(74,144,226,.08); }
/* Streamlit native uploader sizing */
[data-testid="stFileUploader"] section{ padding:0 !important; }
[data-testid="stFileUploaderDropzone"]{
  min-height:90px !important;      /* was 120px */
  padding:.75rem !important;
  border:1px dashed #d0d7de !important;
  background:#fafbfc !important; border-radius:8px !important;
}
[data-testid="stFileUploaderDropzone"] div{ gap:.35rem !important; }
[data-testid="stFileUploader"] svg{ width:18px !important; height:18px !important; }
/* hide under-hint */
[data-testid="stFileUploader"] > div > div:nth-child(2){ display:none !important; }
/* ====== Cards ====== */
.card{
  background:#fff; border-radius:12px;
  padding:1.1rem 1.3rem;
  box-shadow:0 2px 12px rgba(0,0,0,.05);
  margin:1rem auto; max-width:980px;
}
.card--accent-blue{ border-left:4px solid #4a90e2; }
.card--accent-green{ border-left:4px solid #20c997; }
.card h3{ margin-top:0; }
/* ====== Buttons ====== */
.stButton > button{
  background:linear-gradient(135deg,#28a745 0%,#20c997 100%);
  color:#fff; border:none; border-radius:8px !important;
  padding:.55rem 1.15rem !important; font-weight:600;
  font-size:.95rem !important; transition:.2s;
}
.stButton > button:hover{ transform:translateY(-1px); box-shadow:0 4px 12px rgba(40,167,69,.25); }
/* Progress bar */
[data-testid="stProgress"] div[role="progressbar"]{
  height:6px !important; border-radius:999px !important;
}
/* Messages */
.success-message, .error-message{
  max-width:880px; padding:.85rem 1rem; border-radius:8px; margin:1rem auto .5rem auto;
  font-size:.9rem; line-height:1.4;
}
.success-message{
  background:#d4edda; color:#155724; border-left:4px solid #28a745;
}
.error-message{
  background:#f8d7da; color:#721c24; border-left:4px solid #dc3545;
}
/* Footer */
.footer{
  text-align:center; padding:1.25rem 0; color:#6c757d;
  border-top:1px solid #e9ecef; margin-top:2rem !important; font-size:.82rem;
}
/* Hide Streamlit chrome */
#MainMenu, header, footer{ visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ----------------------------------
# Small helpers
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
# App
# ----------------------------------
def main():
    # ---- Header (now compact) ----
    st.markdown("""
    <div class="header-container">
        <div class="header-title">🚀 InsightPilot</div>
        <div class="header-subtitle">Your AI PowerBI Report Assistant</div>
    </div>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="container-narrow">', unsafe_allow_html=True)

        # ---- Session state ----
        for k, v in {
            'analysis_complete': False,
            'analysis_result': None,
            'pdf_path': None,
            'file_type': None,
            'uploaded_file_name': None
        }.items():
            st.session_state.setdefault(k, v)

        # ---- Select type ----
        st.markdown('<div class="section-title">📁 Select Analysis Type</div>', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        with col1:
            csv_selected = st.button("📊 CSV Dataset Analysis", use_container_width=True)
        with col2:
            pdf_selected = st.button("📋 PDF Report Analysis", use_container_width=True)

        if csv_selected:
            st.session_state.file_type = "csv"
        if pdf_selected:
            st.session_state.file_type = "pdf"

        # ---- Upload box (small) ----
        if st.session_state.file_type:
            st.markdown(f"""
            <div class="upload-section">
                <h3 style="text-align:center;color:#1f4e79;margin:0 0 .6rem 0;">
                    Upload your {st.session_state.file_type.upper()} file
                </h3>
            </div>
            """, unsafe_allow_html=True)

            if st.session_state.file_type == "csv":
                uploaded_file = st.file_uploader(
                    "Choose a CSV file",
                    type=['csv'],
                    help="Upload your file for AI analysis.",
                    label_visibility="collapsed",
                    key="csv_uploader"
                )
            else:
                uploaded_file = st.file_uploader(
                    "Choose a PDF file",
                    type=['pdf'],
                    help="Upload your file for AI analysis.",
                    label_visibility="collapsed",
                    key="pdf_uploader"
                )

            if uploaded_file is not None:
                st.session_state.uploaded_file_name = uploaded_file.name
                size_mb = len(uploaded_file.getvalue()) / 1024 / 1024
                st.markdown(f"""
                <div class="success-message">
                    ✅ <strong>File uploaded successfully!</strong><br>
                    📄 <strong>Name:</strong> {uploaded_file.name}<br>
                    📏 <strong>Size:</strong> {size_mb:.2f} MB<br>
                    🗂️ <strong>Type:</strong> {st.session_state.file_type.upper()} Analysis
                </div>
                """, unsafe_allow_html=True)

                # ---- CSV preview - inside a card ----
                if st.session_state.file_type == "csv":
                    try:
                        df = pd.read_csv(uploaded_file, encoding='latin-1')
                        st.markdown('<div class="card card--accent-blue">', unsafe_allow_html=True)
                        st.markdown("### 👀 Dataset Preview")
                        st.write(f"**Shape:** {df.shape[0]} rows × {df.shape[1]} columns")
                        st.dataframe(df.head(), use_container_width=True)
                        st.markdown('</div>', unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Error reading CSV file: {str(e)}")

                # ---- Start analysis button ----
                if st.button("🔍 Start AI Analysis", use_container_width=True):  
                    with st.spinner("🔧 Initializing AI systems and analyzing your data..."):
                        try:
                            
                            query_engine = build_index()

                            
                            

                            if st.session_state.file_type == "csv":
                                file_content = io.BytesIO(uploaded_file.getvalue())
                            else:
                                pdf_text = extract_pdf_text(uploaded_file)
                                if pdf_text is None:
                                    st.error("Failed to extract text from PDF. Please try again.")
                                    st.stop()
                                   
                                file_content = pdf_text

                       

                            result, pdf_path = chat_with_agents(
                                file_type=st.session_state.file_type,
                                file_content=file_content,
                                query_engine=query_engine
                            )

                        
                            st.session_state.analysis_result = result
                            st.session_state.pdf_path = pdf_path
                            st.session_state.analysis_complete = True
                            st.success("✅ Analysis complete!")

                       
                        

                        except Exception as e:
                            st.markdown(f"""
                            <div class="error-message">
                               ❌ <strong>Analysis failed:</strong> {str(e)}
                            </div>
                            """, unsafe_allow_html=True)

        # ---- Results (inside cards) ----
        if st.session_state.analysis_complete and st.session_state.analysis_result:
            st.markdown("---")
            st.markdown('<div class="card card--accent-green">', unsafe_allow_html=True)
            st.markdown("## 📊 Analysis Results")
            st.markdown("### 🎯 AI-Generated Insights")
            st.markdown(st.session_state.analysis_result)
            st.markdown('</div>', unsafe_allow_html=True)

            st.markdown('<div class="card">', unsafe_allow_html=True)
            st.markdown("### 📋 Generated Report Preview")

            lines = str(st.session_state.analysis_result).split('\n')
            preview_lines = [l for l in lines if l.strip() and not l.startswith('        ')][:5]
            preview_text = '\n'.join(preview_lines)

            st.markdown(f"""
            **Report Summary:**  
            {preview_text}
            **Generated:** {datetime.now().strftime('%B %d, %Y at %I:%M %p')}  
            **File Analyzed:** {st.session_state.uploaded_file_name}  
            **Analysis Type:** {st.session_state.file_type.upper()}
            """)
            st.markdown('</div>', unsafe_allow_html=True)

            col1, col2, col3 = st.columns([1,2,1])
            with col2:
                if st.session_state.pdf_path:
                    with open(st.session_state.pdf_path, "rb") as pdf_file:
                        st.download_button(
                            label="📥 Download Full Report (PDF)",
                            data=pdf_file,
                            file_name=f"insightpilot_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )

            st.markdown("---")
            col1, col2, col3 = st.columns([1,1,1])
            with col2:
                if st.button("🔄 Start New Analysis", use_container_width=True):
                    for key in [
                        'analysis_complete', 'analysis_result', 'pdf_path',
                        'file_type', 'uploaded_file_name'
                    ]:
                        if key in st.session_state:
                            del st.session_state[key]
                    st.rerun()

        # footer
        st.markdown("""
        <div class="footer">
            🚀 <strong>InsightPilot</strong> • Powered by CrewAI & OpenAI
        </div>
        """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)  # end container-narrow


if __name__ == "__main__":
    main()
