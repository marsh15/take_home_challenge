import os
from dotenv import load_dotenv
from crewai import Agent
from tools import search_tool, read_data_tool

load_dotenv()


def _get_model():
    """Read the model name fresh every time (not cached at import)."""
    return os.getenv("OPENAI_MODEL_NAME", "gemini/gemini-2.5-flash")


def get_verifier():
    return Agent(
        role="Financial Document Verifier",
        goal="Verify the structural integrity and extract basic formatting info from the document at {file_path}",
        verbose=True,
        memory=True,
        backstory=(
            "You are a meticulous compliance and verification officer. Your job is to ensure "
            "that uploaded documents are properly parsed and valid financial reports before analysis."
        ),
        tools=[read_data_tool],
        allow_delegation=False,
        llm=_get_model()
    )

def get_financial_analyst():
    return Agent(
        role="Senior Financial Analyst",
        goal="Conduct a thorough, objective analysis of the financial document at {file_path} addressing the query: {query}",
        verbose=True,
        memory=True,
        backstory=(
            "You are a highly experienced financial analyst with a keen eye for detail. "
            "You analyze company financials, market trends, and economic indicators "
            "to provide objective, data-driven insights. You rely on actual data."
        ),
        tools=[read_data_tool],
        allow_delegation=True,
        llm=_get_model()
    )

def get_investment_advisor():
    return Agent(
        role="Investment Advisor",
        goal="Provide objective, well-reasoned investment strategies addressing this query: {query}",
        verbose=True,
        backstory=(
            "You are a certified financial planner and investment advisor with decades of experience. "
            "You build data-backed, well-diversified portfolios and provide realistic, pragmatic investment advice. "
        ),
        allow_delegation=False,
        llm=_get_model()
    )

def get_risk_assessor():
    return Agent(
        role="Risk Assessment Expert",
        goal="Evaluate concrete market risks and mitigations rationally for the user query: {query}",
        verbose=True,
        backstory=(
            "You are a cautious and analytical Risk Assessment Expert. "
            "You specialize in identifying credit risks, market volatility, and operational hazards. "
            "You provide actionable risk mitigation strategies."
        ),
        allow_delegation=False,
        llm=_get_model()
    )
