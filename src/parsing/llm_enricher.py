"""
LLM Enricher Module
Uses LLM to enrich and refine requirements with descriptions, summaries, and refinements.
"""

import logging
import json
from typing import Dict, List, Optional
from dataclasses import asdict

from src.parsing.requirements_structurer import RequirementsDocument, Question, TableInfo, SQLQuery

logger = logging.getLogger(__name__)


class LLMEnricher:
    """
    Enriches requirements document using LLM.
    Adds descriptions, summaries, and refines content.
    """
    
    def __init__(self, llm_client):
        """
        Initialize LLM enricher.
        
        Args:
            llm_client: LLM client (DatabricksFoundationModelClient)
        """
        self.llm_client = llm_client
    
    def enrich_document(self, doc: RequirementsDocument) -> RequirementsDocument:
        """
        Enrich requirements document with LLM-generated content.
        
        Args:
            doc: RequirementsDocument to enrich
            
        Returns:
            Enriched RequirementsDocument
        """
        logger.info("Enriching requirements document with LLM")
        
        # Enrich tables (add descriptions if missing)
        self._enrich_tables(doc.all_tables)
        
        # Enrich queries (add descriptions if missing)
        self._enrich_queries(doc.all_queries)
        
        # Generate business scenarios
        doc.metadata["business_scenarios"] = self._generate_scenarios(doc)
        
        # Generate document summary
        doc.metadata["summary"] = self._generate_summary(doc)
        
        logger.info("Document enrichment complete")
        
        return doc
    
    def _enrich_tables(self, tables: List[TableInfo]) -> None:
        """Enrich table descriptions using LLM"""
        logger.info(f"Enriching {len(tables)} tables")
        
        for table in tables:
            if not table.description or table.description == "Unknown":
                try:
                    description = self._generate_table_description(table)
                    table.description = description
                    logger.debug(f"Generated description for {table.full_name}")
                except Exception as e:
                    logger.error(f"Error enriching table {table.full_name}: {e}")
    
    def _enrich_queries(self, queries: List[SQLQuery]) -> None:
        """Enrich query descriptions using LLM"""
        logger.info(f"Enriching {len(queries)} queries")
        
        for query in queries:
            if not query.description or query.description.startswith("Query for"):
                try:
                    description = self._generate_query_description(query)
                    query.description = description
                    logger.debug(f"Generated description for query {query.question_id}")
                except Exception as e:
                    logger.error(f"Error enriching query {query.question_id}: {e}")
    
    def _generate_table_description(self, table: TableInfo) -> str:
        """Generate description for a table using LLM"""
        prompt = f"""Generate a concise 1-2 sentence description for this database table:

Table: {table.full_name}
Columns: {', '.join([col.name for col in table.columns])}
Related KPI: {table.related_kpi or 'None'}

Description should explain:
1. What data this table contains
2. What business purpose it serves

Respond with ONLY the description, no additional text."""
        
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=200
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Error generating table description: {e}")
            return table.description or "Database table"
    
    def _generate_query_description(self, query: SQLQuery) -> str:
        """Generate description for a SQL query using LLM"""
        # Truncate query if too long
        query_text = query.query[:1000] + "..." if len(query.query) > 1000 else query.query
        
        prompt = f"""Generate a concise 1-2 sentence description for this SQL query:

Query:
{query_text}

Description should explain:
1. What business question this query answers
2. Key metrics or data it returns

Respond with ONLY the description, no additional text."""
        
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=200
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Error generating query description: {e}")
            return query.description or "SQL query"
    
    def _generate_scenarios(self, doc: RequirementsDocument) -> List[Dict]:
        """Generate business scenario examples using LLM"""
        logger.info("Generating business scenarios")
        
        # Select top 3-5 questions from different categories
        sample_questions = []
        seen_categories = set()
        
        for question in doc.all_questions:
            if question.category not in seen_categories and len(sample_questions) < 5:
                sample_questions.append(question)
                seen_categories.add(question.category)
        
        if not sample_questions:
            return []
        
        questions_text = "\n".join([f"{i+1}. {q.text}" for i, q in enumerate(sample_questions)])
        
        prompt = f"""Based on these business questions, generate 3-5 realistic business scenarios where these questions would be asked:

Questions:
{questions_text}

For each scenario, provide:
1. Title (brief, 3-5 words)
2. Description (1-2 sentences)
3. Related questions (by number)

Return as JSON array:
[
  {{
    "title": "...",
    "description": "...",
    "related_questions": [1, 2]
  }}
]

Respond with ONLY valid JSON, no additional text."""
        
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.3,
                max_tokens=1000
            )
            
            # Parse JSON response
            response_clean = response.strip()
            if response_clean.startswith("```json"):
                response_clean = response_clean[7:]
            elif response_clean.startswith("```"):
                response_clean = response_clean[3:]
            if response_clean.endswith("```"):
                response_clean = response_clean[:-3]
            
            scenarios = json.loads(response_clean.strip())
            return scenarios
        except Exception as e:
            logger.error(f"Error generating scenarios: {e}")
            return []
    
    def _generate_summary(self, doc: RequirementsDocument) -> str:
        """Generate summary of requirements document using LLM"""
        logger.info("Generating document summary")
        
        # Prepare statistics
        stats = {
            "num_questions": len(doc.all_questions),
            "num_tables": len(doc.all_tables),
            "num_queries": len(doc.all_queries),
            "categories": list(set([q.category for q in doc.all_questions])),
            "domains": doc.metadata.get("domains", [])
        }
        
        # Sample questions (first 10)
        sample_questions = [q.text for q in doc.all_questions[:10]]
        
        prompt = f"""Generate a concise 2-3 paragraph summary of this requirements document:

Statistics:
- Questions: {stats['num_questions']}
- Tables: {stats['num_tables']}
- SQL Queries: {stats['num_queries']}
- Categories: {', '.join(stats['categories'])}
- Domains: {', '.join(stats['domains'])}

Sample Questions:
{chr(10).join([f'- {q}' for q in sample_questions])}

Summary should cover:
1. Overall purpose and scope
2. Key question categories
3. Main data sources

Write in clear, professional language."""
        
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.2,
                max_tokens=500
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Requirements document with {stats['num_questions']} questions across {stats['num_tables']} tables."
    
    def refine_questions(self, questions: List[Question]) -> List[Question]:
        """
        Refine question phrasing for clarity using LLM.
        
        Args:
            questions: List of questions to refine
            
        Returns:
            List of refined questions
        """
        logger.info(f"Refining {len(questions)} questions")
        
        for question in questions:
            try:
                refined_text = self._refine_question_text(question.text)
                if refined_text and refined_text != question.text:
                    question.text = refined_text
                    logger.debug(f"Refined question {question.id}")
            except Exception as e:
                logger.error(f"Error refining question {question.id}: {e}")
        
        return questions
    
    def _refine_question_text(self, question_text: str) -> str:
        """Refine a single question text using LLM"""
        prompt = f"""Refine this business question for clarity while preserving its meaning and language (Korean/English):

Original: {question_text}

Guidelines:
- Keep the same language (if Korean, respond in Korean)
- Make it more precise and professional
- Preserve all key information
- Keep it concise

Respond with ONLY the refined question, no additional text."""
        
        try:
            response = self.llm_client.generate(
                prompt=prompt,
                temperature=0.1,
                max_tokens=150
            )
            return response.strip()
        except Exception as e:
            logger.error(f"Error refining question: {e}")
            return question_text


def enrich_requirements(doc: RequirementsDocument, llm_client) -> RequirementsDocument:
    """
    Convenience function to enrich requirements document.
    
    Args:
        doc: RequirementsDocument to enrich
        llm_client: LLM client for enrichment
        
    Returns:
        Enriched RequirementsDocument
    """
    enricher = LLMEnricher(llm_client)
    return enricher.enrich_document(doc)
