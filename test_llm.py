#!/usr/bin/env python3

"""
Test script to verify Groq LLM integration works correctly
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import List

# Load environment variables
load_dotenv()

class ProjectDetails(BaseModel):
    """Pydantic model for structured project analysis output"""
    title: str = Field(description="Professional project title (max 80 chars)")
    summary: str = Field(description="Detailed project summary highlighting achievements (200-400 words)")
    tech_stack: List[str] = Field(description="List of technologies, frameworks, and tools used")
    skills: List[str] = Field(description="Transferable skills demonstrated in this project")
    domain: str = Field(description="Primary domain/industry category")
    impact: str = Field(description="Quantifiable impact or results achieved (100-200 words)")

def test_groq_llm():
    """Test the Groq LLM integration"""
    
    # Get API key
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key:
        print("❌ GROQ_API_KEY not found")
        return False
    
    print(f"✅ Using Groq API key (length: {len(groq_api_key)})")
    
    try:
        # Initialize LLM
        llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=1000,
            groq_api_key=groq_api_key
        )
        
        # Setup JSON output parser
        parser = JsonOutputParser(pydantic_object=ProjectDetails)
        
        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert technical analyst specializing in software project evaluation for professional resumes.

Analyze the provided repository information and extract structured data that highlights the technical achievements, skills, and business impact.

{format_instructions}

Focus on:
- Technical complexity and innovation
- Problem-solving approach
- Technologies and frameworks used
- Measurable outcomes or impact
- Professional skills demonstrated

Provide accurate, professional descriptions suitable for a software engineer's resume."""),
            ("human", """Repository: {repo_name}
Description: {description}
README Content: {readme_content}
Code Structure: {code_content}

Analyze this project and provide structured information for a professional resume.""")
        ])
        
        # Create the analysis chain
        analysis_chain = prompt | llm | parser
        
        # Test with sample data
        test_data = {
            "repo_name": "test-repository",
            "description": "A sample Python web application using Flask and PostgreSQL",
            "readme_content": "# Test Repository\n\nThis is a test web application built with Flask.",
            "code_content": "main.py:\nfrom flask import Flask\napp = Flask(__name__)\n\n@app.route('/')\ndef hello():\n    return 'Hello World!'",
            "format_instructions": parser.get_format_instructions()
        }
        
        print("🔄 Testing LLM analysis...")
        result = analysis_chain.invoke(test_data)
        
        print("✅ LLM analysis completed successfully!")
        print("Result type:", type(result))
        print("Result keys:", list(result.keys()) if isinstance(result, dict) else "Not a dict")
        
        if isinstance(result, dict):
            print("Sample result:")
            for key, value in result.items():
                print(f"  {key}: {value}")
        
        return True
        
    except Exception as e:
        print(f"❌ LLM test failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Groq LLM integration...")
    success = test_groq_llm()
    if success:
        print("🎉 All tests passed!")
    else:
        print("💥 Tests failed!")
