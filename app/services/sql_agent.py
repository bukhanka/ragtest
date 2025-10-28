"""SQL Agent for natural language to SQL conversion."""
import logging
import json
import re
from typing import List, Dict, Any
import aiosqlite
from app.services.llm import LLMService
from app.config import settings

logger = logging.getLogger(__name__)


class SQLAgent:
    """Agent for converting natural language queries to SQL."""
    
    def __init__(self, llm_service: LLMService):
        """Initialize SQL agent."""
        self.llm_service = llm_service
        self.db_path = "./data/assistant.db"
        self.schema_info = None
    
    async def initialize(self):
        """Initialize database and load schema."""
        try:
            # Ensure data directory exists
            import os
            os.makedirs("./data", exist_ok=True)
            
            # Create database and tables
            async with aiosqlite.connect(self.db_path) as db:
                # Create team_members table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS team_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        role TEXT NOT NULL,
                        department TEXT,
                        email TEXT,
                        join_date TEXT,
                        skills TEXT
                    )
                """)
                
                # Create projects table
                await db.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        description TEXT,
                        status TEXT,
                        start_date TEXT,
                        end_date TEXT
                    )
                """)
                
                # Insert sample data if tables are empty
                cursor = await db.execute("SELECT COUNT(*) FROM team_members")
                count = (await cursor.fetchone())[0]
                
                if count == 0:
                    # Insert sample team members
                    team_data = [
                        ('Александр Иванов', 'Senior ML Engineer', 'Machine Learning', 'a.ivanov@company.com', '2020-03-15', 'Python,TensorFlow,PyTorch,NLP'),
                        ('Мария Петрова', 'Data Scientist', 'Machine Learning', 'm.petrova@company.com', '2021-06-01', 'Python,Scikit-learn,SQL,Statistics'),
                        ('Дмитрий Смирнов', 'ML Engineer', 'Machine Learning', 'd.smirnov@company.com', '2022-01-10', 'Python,Docker,MLOps,FastAPI'),
                        ('Елена Васильева', 'NLP Specialist', 'Machine Learning', 'e.vasilieva@company.com', '2021-09-20', 'Python,NLP,LangChain,Transformers'),
                        ('Иван Кузнецов', 'Backend Developer', 'Engineering', 'i.kuznetsov@company.com', '2020-11-05', 'Python,FastAPI,PostgreSQL,Redis'),
                        ('Анна Соколова', 'DevOps Engineer', 'Engineering', 'a.sokolova@company.com', '2019-08-12', 'Docker,Kubernetes,CI/CD,Linux'),
                        ('Павел Морозов', 'Team Lead', 'Machine Learning', 'p.morozov@company.com', '2018-05-20', 'Python,Management,ML,Architecture'),
                        ('Ольга Новикова', 'QA Engineer', 'Quality Assurance', 'o.novikova@company.com', '2021-03-15', 'Python,Testing,Selenium,API Testing'),
                    ]
                    
                    await db.executemany(
                        "INSERT INTO team_members (name, role, department, email, join_date, skills) VALUES (?, ?, ?, ?, ?, ?)",
                        team_data
                    )
                    
                    # Insert sample projects
                    projects_data = [
                        ('LLM Assistant', 'Разработка многофункционального LLM-ассистента', 'active', '2024-01-15', None),
                        ('RAG System', 'Система поиска по документации с использованием RAG', 'active', '2024-02-01', None),
                        ('SQL Agent', 'Агент для работы с SQL базами данных', 'completed', '2023-10-01', '2024-01-30'),
                    ]
                    
                    await db.executemany(
                        "INSERT INTO projects (name, description, status, start_date, end_date) VALUES (?, ?, ?, ?, ?)",
                        projects_data
                    )
                    
                    await db.commit()
                    logger.info("Sample data inserted into database")
            
            # Load schema information
            await self._load_schema()
            logger.info("SQL agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing SQL agent: {e}", exc_info=True)
            raise
    
    async def _load_schema(self):
        """Load database schema information."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # Get table names
                cursor = await db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'"
                )
                tables = await cursor.fetchall()
                
                schema = {}
                for (table_name,) in tables:
                    # Get column info for each table
                    cursor = await db.execute(f"PRAGMA table_info({table_name})")
                    columns = await cursor.fetchall()
                    schema[table_name] = [
                        {"name": col[1], "type": col[2], "notnull": bool(col[3])}
                        for col in columns
                    ]
                
                self.schema_info = schema
                logger.info(f"Loaded schema for tables: {list(schema.keys())}")
                
        except Exception as e:
            logger.error(f"Error loading schema: {e}", exc_info=True)
            raise
    
    def _get_schema_description(self) -> str:
        """Get human-readable schema description."""
        if not self.schema_info:
            return "No schema available"
        
        description = "Database Schema:\n\n"
        for table_name, columns in self.schema_info.items():
            description += f"Table: {table_name}\n"
            description += "Columns:\n"
            for col in columns:
                required = " (required)" if col["notnull"] else ""
                description += f"  - {col['name']}: {col['type']}{required}\n"
            description += "\n"
        
        return description
    
    async def query(self, natural_language_query: str) -> Dict[str, Any]:
        """
        Convert natural language query to SQL and execute it.
        
        Args:
            natural_language_query: Natural language question
            
        Returns:
            Dictionary with query results and metadata
        """
        try:
            # Generate SQL from natural language
            sql_query = await self._generate_sql(natural_language_query)
            
            # Validate SQL (basic safety check)
            if not self._is_safe_query(sql_query):
                raise ValueError("Unsafe SQL query detected")
            
            # Execute query
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(sql_query)
                rows = await cursor.fetchall()
                
                # Convert to list of dicts
                results = [dict(row) for row in rows]
            
            logger.info(f"SQL query executed successfully: {sql_query}")
            
            return {
                "success": True,
                "sql_query": sql_query,
                "results": results,
                "row_count": len(results)
            }
            
        except Exception as e:
            logger.error(f"Error executing SQL query: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "sql_query": None,
                "results": []
            }
    
    async def _generate_sql(self, natural_language_query: str) -> str:
        """Generate SQL query from natural language."""
        schema_desc = self._get_schema_description()
        
        prompt = f"""You are a SQL expert. Convert the following natural language query into a valid SQLite query.

{schema_desc}

Rules:
1. Only generate SELECT queries (no INSERT, UPDATE, DELETE, DROP)
2. Use proper SQLite syntax
3. Return ONLY the SQL query, no explanations
4. If skills column is queried, note it contains comma-separated values

Natural language query: {natural_language_query}

SQL Query:"""
        
        messages = [
            {"role": "system", "content": "You are a SQL expert that converts natural language to SQL queries."},
            {"role": "user", "content": prompt}
        ]
        
        response = await self.llm_service.chat_completion(
            messages=messages,
            temperature=0.0,
            max_tokens=500
        )
        
        # Extract SQL query from response
        sql_query = self._extract_sql(response)
        return sql_query
    
    def _extract_sql(self, text: str) -> str:
        """Extract SQL query from LLM response."""
        # Remove markdown code blocks if present
        text = re.sub(r'```sql\n?', '', text)
        text = re.sub(r'```\n?', '', text)
        
        # Remove common prefixes
        text = re.sub(r'^(SQL Query:|Query:)\s*', '', text, flags=re.IGNORECASE)
        
        # Take first non-empty line that looks like SQL
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        for line in lines:
            if line.upper().startswith('SELECT'):
                return line
        
        # If no SELECT found, return first line
        return lines[0] if lines else text.strip()
    
    def _is_safe_query(self, sql_query: str) -> bool:
        """Check if SQL query is safe to execute."""
        sql_upper = sql_query.upper()
        
        # Block dangerous operations
        dangerous_keywords = [
            'DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER',
            'CREATE', 'TRUNCATE', 'REPLACE', 'PRAGMA'
        ]
        
        for keyword in dangerous_keywords:
            if keyword in sql_upper:
                return False
        
        # Only allow SELECT queries
        if not sql_upper.strip().startswith('SELECT'):
            return False
        
        return True

