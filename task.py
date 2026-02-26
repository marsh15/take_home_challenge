from crewai import Task
from tools import read_data_tool

def get_verification_task(verifier):
    return Task(
        description="Extract text from the financial document located at {file_path} and verify it contains readable financial data. "
                    "Ensure the contents are properly read so downstream agents can utilize it.",
        expected_output="A brief summary confirming the document has been successfully read and verified, including basic document metadata or structure.",
        agent=verifier,
        tools=[read_data_tool],
        async_execution=False
    )

def get_analyze_document_task(financial_analyst):
    return Task(
        description="Read the financial document at {file_path} if necessary, and analyze it to address the user query: {query}. "
                    "Provide a detailed, objective breakdown of the financial metrics, health, and notable data points found in the document.",
        expected_output="A detailed financial analysis report in Markdown format, covering key metrics, financial health, and addressing the specific query.",
        agent=financial_analyst,
        tools=[read_data_tool],
        async_execution=False
    )

def get_investment_analysis_task(investment_advisor):
    return Task(
        description="Based on the financial analysis previously conducted, provide professional investment advice regarding the user query: {query}. "
                    "Recommend practical, data-backed strategies suitable for a balanced portfolio.",
        expected_output="A structured investment strategy guide in Markdown format, recommending specific approaches based on the analysis.",
        agent=investment_advisor,
        async_execution=False
    )

def get_risk_assessment_task(risk_assessor):
    return Task(
        description="Identify and formulate a risk assessment based on the financial document and the user query: {query}. "
                    "Highlight key potential risks (market, operational, liquidity) and suggest practical mitigation strategies.",
        expected_output="A comprehensive risk assessment report in Markdown format, identifying core risks and outlining mitigation steps.",
        agent=risk_assessor,
        async_execution=False
    )