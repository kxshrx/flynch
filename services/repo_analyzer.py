import os
import json
import tempfile
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime, timezone
from sqlalchemy.orm import Session

# LangChain imports
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

from models.project_analysis import ProjectAnalysis
from models.repository import Repository

class ProjectDetails(BaseModel):
    title: str = Field(description="Professional project title (max 80 chars)")
    summary: str = Field(description="Detailed project summary (200-400 words)")
    tech_stack: List[str] = Field(description="Technologies, frameworks, and tools used")
    skills: List[str] = Field(description="Transferable skills demonstrated")
    domain: str = Field(description="Primary domain/industry category")
    impact: str = Field(description="Quantifiable impact or results (100-200 words)")
    problem_solved: str = Field(description="Explicit problem the project addresses")
    project_type: str = Field(description="Project category (Web App, API, etc.)")
    responsibilities: List[str] = Field(description="Developer's specific responsibilities")
    key_features: List[str] = Field(description="Key features and capabilities")
    used_llm_or_vector: bool = Field(description="Uses LLM or vector database technology")
    
class RepositoryAnalyzer:
    def __init__(self, groq_api_key: str):
        self.groq_api_key = groq_api_key
        self.file_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.md', '.txt', '.yml', '.yaml', '.json'}
        self.exclude_dirs = {'node_modules', '__pycache__', '.git', 'venv', 'env', '.env', 'dist', 'build'}
        
        # Enhanced API key validation
        if not groq_api_key:
            raise ValueError("Groq API key is required")
        
        if not groq_api_key.startswith('gsk_'):
            raise ValueError("Invalid Groq API key format. Key should start with 'gsk_'")
        
        try:
            # Initialize LangChain GroqChat with proper error handling
            self.llm = ChatGroq(
                model="llama-3.3-70b-versatile",  # Updated to working model
                temperature=0.1,
                max_tokens=1000,
                groq_api_key=groq_api_key
            )
            
            # Setup JSON output parser
            self.parser = JsonOutputParser(pydantic_object=ProjectDetails)
            
            # Create prompt template
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert technical analyst specializing in software project evaluation for professional resumes.

                Analyze the provided repository information and extract structured data that highlights technical achievements, skills, and business impact.

                {format_instructions}

                Focus on:
                - Technical complexity and innovation
                - Problem-solving approach
                - Technologies and frameworks used
                - Measurable outcomes or impact
                - Professional skills demonstrated
                - Specific responsibilities and features
                - Whether the project uses LLM/AI/vector database technology

                Provide accurate, professional descriptions suitable for a software engineer's resume."""),
                    ("human", """Repository: {repo_name}
                Description: {description}
                README Content: {readme_content}
                Code Structure: {code_content}

                Analyze this project and provide structured information including:
                - What problem it solves
                - Project type/category
                - Developer's specific responsibilities
                - Key features and capabilities
                - Whether it uses LLM or vector database technology

                Return a complete JSON object with all required fields.""")
            ])

            
            # Create the analysis chain
            self.analysis_chain = self.prompt | self.llm | self.parser
            
            print("RepositoryAnalyzer initialized successfully")
            
        except Exception as e:
            print(f"Failed to initialize RepositoryAnalyzer: {e}")
            raise ValueError(f"Failed to initialize LangChain components: {e}")

    async def analyze_repositories(self, repo_names: List[str], username: str, db: Session) -> Dict:
        results = {
            'success': [],
            'failed': [],
            'total': len(repo_names)
        }
        
        for repo_name in repo_names:
            try:
                repo = db.query(Repository).filter_by(
                    repo_name=repo_name,
                    owner_username=username
                ).first()
                
                if not repo:
                    results['failed'].append({
                        'repo_name': repo_name,
                        'error': 'Repository not found in database'
                    })
                    continue
                
                # Check if already analyzed
                existing_analysis = db.query(ProjectAnalysis).filter_by(
                    repo_id=repo.repo_id,
                    user_github_username=username
                ).first()
                
                if existing_analysis:
                    results['success'].append({
                        'repo_name': repo_name,
                        'status': 'already_analyzed'
                    })
                    continue
                
                # Create pending analysis record
                analysis = ProjectAnalysis(
                    repo_id=repo.repo_id,
                    repo_name=repo_name,
                    title="",
                    summary="",
                    tech_stack="[]",
                    skills="[]",
                    domain="",
                    impact="",
                    user_github_username=username,
                    analysis_status="pending"
                )
                db.add(analysis)
                db.commit()
                
                # Analyze repository using LangChain
                analysis_result = await self.analyze_single_repository(repo, analysis.id, db)
                
                if analysis_result['success']:
                    results['success'].append({
                        'repo_name': repo_name,
                        'status': 'completed'
                    })
                else:
                    results['failed'].append({
                        'repo_name': repo_name,
                        'error': analysis_result['error']
                    })
                    
            except Exception as e:
                results['failed'].append({
                    'repo_name': repo_name,
                    'error': str(e)
                })
        
        return results
    
    async def analyze_single_repository(self, repo: Repository, analysis_id: str, db: Session) -> Dict:
        temp_dir = None
        try:
            # Clone repository with enhanced error handling
            temp_dir = tempfile.mkdtemp()
            clone_path = os.path.join(temp_dir, repo.repo_name)
            
            print(f"Cloning repository: {repo.repo_name}")
            clone_result = subprocess.run([
                'git', 'clone', '--depth', '1', repo.repo_url, clone_path
            ], capture_output=True, text=True, timeout=300)
            
            if clone_result.returncode != 0:
                raise Exception(f"Git clone failed: {clone_result.stderr}")
            
            # Aggregate files
            aggregated_content = self.aggregate_repository_files(clone_path)
            
            # Use LangChain chain for analysis with enhanced error handling
            try:
                analysis_result = self.analysis_chain.invoke({
                    "repo_name": repo.repo_name,
                    "description": repo.description or "No description available",
                    "readme_content": (repo.readme_content or "No README available")[:3000],
                    "code_content": aggregated_content[:8000],
                    "format_instructions": self.parser.get_format_instructions()
                })
            except Exception as llm_error:
                raise Exception(f"LLM analysis failed: {str(llm_error)}")
            
            # Validate analysis result
            if not isinstance(analysis_result, dict):
                raise Exception("LLM returned invalid response format")
            
            required_fields = ['title', 'summary', 'tech_stack', 'skills', 'domain', 'impact']
            for field in required_fields:
                if field not in analysis_result:
                    raise Exception(f"Missing required field in LLM response: {field}")
            
            # Update analysis record
            analysis = db.query(ProjectAnalysis).filter_by(id=analysis_id).first()
# Update analysis record with new fields
            analysis.title = analysis_result['title'][:255]
            analysis.summary = analysis_result['summary']
            analysis.tech_stack = json.dumps(analysis_result['tech_stack'])
            analysis.skills = json.dumps(analysis_result['skills'])
            analysis.domain = analysis_result['domain'][:255]
            analysis.impact = analysis_result['impact']
            analysis.problem_solved = analysis_result.get('problem_solved', '')
            analysis.project_type = analysis_result.get('project_type', '')[:100]
            analysis.responsibilities = json.dumps(analysis_result.get('responsibilities', []))
            analysis.key_features = json.dumps(analysis_result.get('key_features', []))
            analysis.used_llm_or_vector = analysis_result.get('used_llm_or_vector', False)
            analysis.analysis_status = "completed"
            analysis.updated_at = datetime.now(timezone.utc)

                        
            db.commit()
            
            print(f"Successfully analyzed: {repo.repo_name}")
            return {'success': True}
            
        except Exception as e:
            # Update analysis record with error
            try:
                analysis = db.query(ProjectAnalysis).filter_by(id=analysis_id).first()
                if analysis:
                    analysis.analysis_status = "failed"
                    analysis.error_message = str(e)[:500]  # Limit error message length
                    analysis.updated_at = datetime.now(timezone.utc)
                    db.commit()
            except Exception as db_error:
                print(f"Failed to update analysis record: {db_error}")
            
            print(f"Failed to analyze {repo.repo_name}: {str(e)}")
            return {'success': False, 'error': str(e)}
            
        finally:
            # Cleanup
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                except Exception as cleanup_error:
                    print(f"Failed to cleanup temp directory: {cleanup_error}")
    
    def aggregate_repository_files(self, repo_path: str) -> str:
        content_parts = []
        repo_path = Path(repo_path)
        
        for file_path in repo_path.rglob('*'):
            if file_path.is_file() and file_path.suffix in self.file_extensions:
                # Skip excluded directories
                if any(excluded in file_path.parts for excluded in self.exclude_dirs):
                    continue
                
                try:
                    relative_path = file_path.relative_to(repo_path)
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_content = f.read()
                    
                    content_parts.append(f"=== {relative_path} ===\n{file_content}\n")
                    
                    # Limit total content size
                    if len('\n'.join(content_parts)) > 50000:  # 50KB limit
                        break
                        
                except Exception:
                    continue
        
        return '\n'.join(content_parts)
