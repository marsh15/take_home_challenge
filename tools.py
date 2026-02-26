import os
import pypdf
from dotenv import load_dotenv
from crewai_tools import SerperDevTool
from crewai.tools import tool

load_dotenv()

## Creating search tool
search_tool = SerperDevTool()

@tool("Read Financial Document")
def read_data_tool(path: str) -> str:
    """Tool to read text from a pdf file.

    Args:
        path (str): Path to the pdf file.

    Returns:
        str: Extracted text from the Financial Document
    """
    try:
        reader = pypdf.PdfReader(path)
        full_report = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                # Remove extra whitespaces and format properly
                while "\n\n" in content:
                    content = content.replace("\n\n", "\n")
                full_report += content + "\n"
        return full_report
    except Exception as e:
        return f"Failed to read pdf: {str(e)}"

@tool("Analyze Investment Data")
def analyze_investment_tool(financial_document_data: str) -> str:
    """Analyze the selected financial document data.
    
    Args:
        financial_document_data (str): Text data to analyze.
        
    Returns:
        str: Basic investment analysis response.
    """
    return "Investment analysis based on the formatted document data."

@tool("Assess Document Risk")
def create_risk_assessment_tool(financial_document_data: str) -> str:
    """Create a risk assessment for the document data.
    
    Args:
        financial_document_data (str): Text data to assess.
        
    Returns:
        str: Basic risk assessment response.
    """
    return "Risk assessment based on the formatted document data."