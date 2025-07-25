"""
Backend Integration Module for InsightPilot
(Strictly Streamlit-compatible – no Gradio)
"""

from crewai import Agent, Task, Crew
from textwrap import dedent
from openai import OpenAI
import pandas as pd
from fpdf import FPDF
from datetime import datetime
import re
from pathlib import Path
from llama_index.core import SimpleDirectoryReader, VectorStoreIndex
from llama_index.embeddings.openai import OpenAIEmbedding
from dotenv import load_dotenv
import os
import fitz  # PyMuPDF

# ---------------------------
# INIT
# ---------------------------
load_dotenv(dotenv_path=Path('.') / '.env')
print("✅ OpenAI Key Loaded:", bool(os.getenv("OPENAI_API_KEY")))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY is not set")

client = OpenAI(api_key=OPENAI_API_KEY)

# Global RAG objects
_index = None
_query_engine = None


def build_index():
    """Build the RAG index from PDFs in ./data"""
    global _index, _query_engine

    print("📂 Loading documents from ./data ...")
    Path("data").mkdir(exist_ok=True)
    documents = SimpleDirectoryReader("data").load_data()
    print(f"✅ Loaded {len(documents)} documents. Creating vector index...")

    _index = VectorStoreIndex.from_documents(
        documents,
        embed_model=OpenAIEmbedding()
    )
    _query_engine = _index.as_query_engine()
    print("✅ RAG index is ready!")
    return _query_engine


# ---------------------------
# Agents (labels only – real work is in functions)
# ---------------------------
dataset_analyzer = Agent(
    role="Dataset Analyzer",
    goal="Understand and summarize any CSV dataset using GPT",
    backstory="You clean and explain raw datasets in simple English.",
    verbose=True
)

report_planner = Agent(
    role="Dashboard Planner",
    goal="Generate Power BI dashboard layout using real documentation",
    backstory="You suggest layout, KPIs, DAX formulas using RAG.",
    verbose=True
)

pdf_insight_agent = Agent(
    role="PDF Insight Agent",
    goal="Explain uploaded Power BI PDF dashboards",
    backstory="You analyze charts and summarize insights clearly.",
    verbose=True
)


# ---------------------------
# Utilities
# ---------------------------
def extract_pdf_text(file_bytes: bytes) -> str:
    """Extract text from PDF bytes"""
    doc = fitz.open("pdf", file_bytes)
    return "\n".join([page.get_text() for page in doc])


def clean_and_summarize(df: pd.DataFrame):
    """Clean and prepare dataset for analysis and track what was done"""
    original_shape = df.shape
    cleaning_report = []

    # Drop completely empty columns
    empty_cols = df.columns[df.isna().all()].tolist()
    if empty_cols:
        cleaning_report.append(f"Removed empty columns: {empty_cols}")
    df.dropna(axis=1, how='all', inplace=True)

    # Remove unnamed columns
    unnamed_cols = df.columns[df.columns.str.contains('^Unnamed')].tolist()
    if unnamed_cols:
        cleaning_report.append(f"Removed unnamed columns: {unnamed_cols}")
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]

    # Drop duplicates
    before_dedup = len(df)
    df.drop_duplicates(inplace=True)
    after_dedup = len(df)
    if before_dedup != after_dedup:
        cleaning_report.append(f"Removed {before_dedup - after_dedup} duplicate rows")

    # Strip column names
    df.columns = df.columns.str.strip()

    if df.isnull().sum().sum() > 0:
        cleaning_report.append("Missing values detected in some columns.")

    cleaning_report.append(f"Final dataset shape after cleaning: {df.shape} (original was {original_shape})")
    cleaning_report.append("Columns after cleaning: " + ", ".join(df.columns[:8]) + ("..." if len(df.columns) > 8 else ""))
    return df, "\n".join(cleaning_report)


def describe_dataset(df: pd.DataFrame, cleaning_info: str) -> str:
    """Generate dataset description using GPT"""
    schema = df.dtypes.astype(str).to_dict()
    sample_rows = df.head(3).to_dict(orient="records")

    prompt = f"""
You are an intelligent assistant. A user uploaded a CSV file. Here is its info:

🧹 Cleaning done:
{cleaning_info}

📄 Column types:
{schema}

📊 Sample rows:
{sample_rows}

Answer in plain business language:
1. What is this dataset about (without guessing fields that don't exist)?
2. Who might use this dataset?
3. What kind of questions could this data help answer?
4. What types of dashboards can be created from this?
5. Give 2–3 lines summarizing the key business value of this data.

Be concise, non-technical, and avoid assumptions beyond the visible columns.
"""
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a helpful data understanding assistant."},
            {"role": "user", "content": prompt}
        ]
    )
    return response.choices[0].message.content


class ReportGeneratorAgent:
    def __init__(self, query_engine):
        self.query_engine = query_engine

    def generate_report_plan(self, dataset_summary: str, cleaning_info: str):
        prompt = f"""Additional Context:

- Assume the user is working in Power BI Desktop
- Provide guidance on building a clean star schema
- Recommend adding a Date Table for time intelligence
- Mention use of DAX measures (not calculated columns)
- Suggest slicers/bookmarks/interactivity options

================ CLEANING LOG ================
{cleaning_info}

================ DATASET SUMMARY ================
{dataset_summary}

TASK:
Using ONLY the uploaded Power BI guidance documents, design a Power BI dashboard:

1. Start with a **very short recap of the important cleaning steps** and how they affect metric definitions (if relevant).
2. KPIs to track (with exact metric names).
3. Chart types with example titles.
4. Layout suggestions (what goes top, left, right).
5. DAX formulas (write the measure names and sample DAX).
6. Visual theme / color guidance.
7. Mistakes to avoid.
8. Step-by-step build instructions in Power BI.

Be concrete and structured.
"""
        rag_response = str(self.query_engine.query(prompt))

        design_best_practices = """
📌 **Design Best Practices (from Visual Guide):**

- Use high contrast between text and background
- Avoid 3D visuals and excessive effects
- Start Y-axis at 0 when appropriate
- Keep colors consistent across visuals
- Limit relationships per visual
- Group related visuals with whitespace
- Use sans-serif fonts (no italics/all-caps)
- Test report comprehension with peers
"""

        return rag_response + "\n\n" + design_best_practices




class InsightAgent:
    def __init__(self, model="gpt-4o"):
        self.model = model

    def generate_insights(self, raw_text: str) -> str:
        prompt = f"""
You are a professional AI insight assistant for business intelligence dashboards.

Below is the extracted text from a Power BI report:
-------------------
{raw_text}
-------------------

Provide a **detailed, section-wise summary** with this structure:

🔹 Revenue / Finance Trends  
🔹 Customer Contributions  
🔹 Product / Service Performance  
🔹 Transaction or Operational Issues  
🔹 City / Channel / Department Level Observations  
🔹 Business Recommendations (2–3 actionable points)  
🔹 Confidence Rating (High / Medium / Low, and say why)

Be clear, concise, and avoid repeating table headers.
"""
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a helpful data analyst."},
                {"role": "user", "content": prompt}
            ]
        )
        return response.choices[0].message.content


class ExportAgent:
    def __init__(self, output_filename="insight_report.pdf"):
        self.output_filename = output_filename

    def save_as_pdf(self, insights_text: str):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.set_title("InsightPilot Analysis Report")

        # Title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, "InsightPilot Analysis Report", ln=True, align='C')

        # Date
        pdf.set_font("Arial", '', 12)
        today = datetime.today().strftime('%B %d, %Y')
        pdf.cell(0, 10, f"Generated: {today}", ln=True, align='C')
        pdf.ln(10)

        # Remove problematic characters
        cleaned_insights_text = re.sub(r'[^\x00-\x7F]+', '', insights_text)

        # Body
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 8, cleaned_insights_text)

        pdf.output(self.output_filename)
        return self.output_filename


# ---------------------------
# Public entry point (used by Streamlit)
# ---------------------------
def chat_with_agents(file_type, file_content, query_engine=None):
    """
    file_type: "csv" or "pdf"
    file_content:
        - csv: BytesIO or bytes
        - pdf: bytes (raw file bytes)
    query_engine: result of build_index()
    """
    if query_engine is None:
        raise ValueError("query_engine is None. Call build_index() first in your Streamlit app.")

    if file_type == "csv":
        # 1) Clean
        df = pd.read_csv(file_content, encoding='latin-1')
        df_clean, cleaning_info = clean_and_summarize(df)

        # 2) Describe
        dataset_summary = describe_dataset(df_clean, cleaning_info)

        # 3) Plan dashboard (RAG)
        planner = ReportGeneratorAgent(query_engine)
        dashboard_plan = planner.generate_report_plan(dataset_summary,cleaning_info)

        # 4) Combine
        final_text = (
            "========================\n"
            "🧹 DATA CLEANING LOG\n"
            "========================\n"
            f"{cleaning_info}\n\n"
            "========================\n"
            "📊 DATASET UNDERSTANDING\n"
            "========================\n"
            f"{dataset_summary}\n\n"
            "========================\n"
            "📈 POWER BI DASHBOARD PLAN (RAG-GROUNDED)\n"
            "========================\n"
            f"{dashboard_plan}"
        )

        exporter = ExportAgent(output_filename="dashboard_output.pdf")
        pdf_path = exporter.save_as_pdf(final_text)
        return final_text, pdf_path

    elif file_type == "pdf":
        # 1) Extract text
        if isinstance(file_content, (bytes, bytearray)):
            pdf_text = extract_pdf_text(file_content)
        else:
            # If the caller already extracted text (not recommended), accept it
            pdf_text = str(file_content)

        # 2) Analyze
        insight_agent = InsightAgent(model="gpt-4o")
        insights = insight_agent.generate_insights(pdf_text)

        # 3) Export
        exporter = ExportAgent(output_filename="pdf_insight_summary.pdf")
        pdf_path = exporter.save_as_pdf(insights)

        return insights, pdf_path

    else:
        raise ValueError("file_type must be either 'csv' or 'pdf'")


def initialize_system():
    """Initialize the RAG system and return query engine"""
    return build_index()
