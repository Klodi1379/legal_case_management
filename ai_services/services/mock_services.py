# ai_services/services/mock_services.py

import logging
import time
import random
from datetime import datetime

logger = logging.getLogger(__name__)

class MockLLMService:
    """Mock LLM service for development and testing."""
    
    def __init__(self, name="Mock LLM", model_type="mock", response_time=1.0, max_tokens=4096):
        self.name = name
        self.model_type = model_type
        self.response_time = response_time
        self.max_tokens = max_tokens
        logger.info(f"Initialized {self.name} service")
    
    def generate_text(self, prompt, max_tokens=None, temperature=0.7):
        """
        Generate text from a prompt.
        
        Args:
            prompt: Prompt string
            max_tokens: Maximum tokens to generate
            temperature: Temperature for generation
            
        Returns:
            Dictionary with generated text and metadata
        """
        if max_tokens is None:
            max_tokens = self.max_tokens
        
        # Log the request
        logger.info(f"Generating text with {self.name} (max_tokens={max_tokens}, temperature={temperature})")
        
        # Simulate processing time
        start_time = time.time()
        time.sleep(self.response_time)
        
        # Generate mock response based on prompt
        response = self._generate_mock_response(prompt)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        return {
            'text': response,
            'processing_time': processing_time,
            'model': self.name,
            'timestamp': datetime.now().isoformat(),
        }
    
    def _generate_mock_response(self, prompt):
        """
        Generate a mock response based on the prompt.
        
        Args:
            prompt: Prompt string
            
        Returns:
            Generated text
        """
        # Extract keywords from prompt to make response seem relevant
        prompt_lower = prompt.lower()
        
        if 'summary' in prompt_lower:
            return self._generate_summary_response()
        elif 'key points' in prompt_lower or 'extract' in prompt_lower:
            return self._generate_key_points_response()
        elif 'legal analysis' in prompt_lower:
            return self._generate_legal_analysis_response()
        elif 'precedent' in prompt_lower:
            return self._generate_precedent_response()
        elif 'research' in prompt_lower:
            return self._generate_research_response()
        else:
            return self._generate_generic_response()
    
    def _generate_summary_response(self):
        """Generate a mock summary response."""
        return """# Document Summary

This document appears to be a legal agreement between two parties, outlining the terms and conditions of their business relationship. The document is structured into several sections covering definitions, obligations, payment terms, confidentiality, termination, and dispute resolution.

## Key Components:
- The agreement establishes a contractual relationship between Party A and Party B
- It defines the scope of services to be provided
- Payment terms indicate a 30-day net payment schedule
- Confidentiality provisions protect both parties' proprietary information
- Termination can occur with 30 days written notice from either party
- Disputes are to be resolved through arbitration in New York

The document is dated January 15, 2025, and appears to be valid for a period of one year with automatic renewal provisions unless terminated by either party."""
    
    def _generate_key_points_response(self):
        """Generate mock key points."""
        return """1. Agreement dated January 15, 2025 between Party A and Party B.

2. Services to be provided include legal consultation and representation.

3. Payment terms: 30-day net with 1.5% monthly interest on late payments.

4. Confidentiality provisions apply to all proprietary information.

5. Term of agreement is one year with automatic renewal.

6. Either party may terminate with 30 days written notice.

7. Governing law is the State of New York.

8. Disputes to be resolved through binding arbitration.

9. Force majeure clause included for unforeseeable circumstances.

10. Amendments must be in writing and signed by both parties."""
    
    def _generate_legal_analysis_response(self):
        """Generate a mock legal analysis response."""
        return """# Legal Analysis

## Strengths
- The agreement clearly defines the rights and obligations of both parties
- Confidentiality provisions are comprehensive and protect both parties
- Termination clauses provide flexibility while ensuring reasonable notice
- Dispute resolution mechanism is clearly defined
- Force majeure provisions account for unforeseen circumstances

## Potential Issues
- The indemnification clause may be overly broad and could expose Party A to significant liability
- The limitation of liability section caps damages at a relatively low amount
- The non-compete provision may face enforceability challenges in certain jurisdictions
- Assignment provisions allow transfer without consent under certain conditions, which could be problematic
- The automatic renewal provision lacks a notification requirement before renewal

## Recommendations
1. Consider narrowing the scope of the indemnification clause
2. Review the limitation of liability cap to ensure it's appropriate for the transaction value
3. Modify the non-compete provision to ensure enforceability in relevant jurisdictions
4. Add a requirement for notification before automatic renewal
5. Include more specific performance metrics and remedies for non-performance

This analysis is based on general legal principles and should be reviewed by counsel familiar with the specific jurisdiction and business context."""
    
    def _generate_precedent_response(self):
        """Generate a mock precedent search response."""
        return """# Relevant Legal Precedents

Based on the document content, the following legal precedents may be applicable:

## Contract Interpretation
1. **Smith v. Jones (2022)** - Supreme Court case establishing that ambiguous terms in contracts should be interpreted against the drafter.

2. **ABC Corp v. XYZ Inc. (2021)** - Established that industry standards can be used to interpret technical terms in agreements.

## Non-Compete Provisions
3. **Johnson Enterprises v. Former Employee (2023)** - Limited the enforceability of non-compete agreements to reasonable geographic scope and duration.

4. **Tech Innovations v. Developer (2020)** - Found that overly broad non-compete provisions may be unenforceable in their entirety.

## Confidentiality
5. **Data Corp v. Ex-Manager (2022)** - Defined the scope of "confidential information" in the absence of specific definitions.

6. **Secure Systems v. Consultant (2021)** - Established that general knowledge and skills cannot be considered confidential information.

## Termination
7. **Service Provider v. Client (2023)** - Clarified requirements for proper notice of termination under similar contract provisions.

8. **Vendor v. Purchaser (2022)** - Established that material breach justifies immediate termination despite notice provisions.

These precedents should be considered when interpreting and applying the provisions in the current document."""
    
    def _generate_research_response(self):
        """Generate a mock legal research response."""
        return """# Legal Research Findings

## Question: What are the requirements for enforcing non-compete agreements in New York?

### Governing Law
In New York, non-compete agreements are governed by common law principles established through case precedent rather than specific statutes.

### Key Requirements for Enforceability
1. **Legitimate Business Interest**: The employer must demonstrate a legitimate business interest that justifies the restriction, such as:
   - Protection of trade secrets or confidential information
   - Protection of customer relationships
   - Protection of specialized training provided to employees

2. **Reasonable in Scope**: The agreement must be reasonable in:
   - Geographic scope
   - Duration
   - Scope of prohibited activities

3. **Not Harmful to Public**: The restriction cannot harm the public (e.g., by creating a monopoly or depriving the public of essential services).

4. **Not Unduly Burdensome**: The restriction cannot impose undue hardship on the employee.

### Notable Case Law
- **BDO Seidman v. Hirshberg (1999)**: Established the "reasonable test" for non-compete agreements in New York.
- **Reed, Roberts Associates v. Strauman (1976)**: Emphasized that non-competes are disfavored and strictly scrutinized.
- **Brown & Brown, Inc. v. Johnson (2016)**: Clarified that New York law applies to non-competes when there is a conflict of laws provision.

### Recent Developments
Courts have increasingly scrutinized non-compete agreements, particularly for lower-level employees. The trend is toward narrower enforcement of these provisions.

### Recommendations
1. Limit duration to 1-2 years maximum
2. Restrict geographic scope to areas where the employer actually conducts business
3. Narrowly define prohibited activities to those directly related to the employee's role
4. Consider using less restrictive alternatives like non-solicitation or confidentiality agreements

This research represents general legal principles in New York as of 2025 and should be verified with current case law for specific applications."""
    
    def _generate_generic_response(self):
        """Generate a generic response."""
        return """Thank you for your query. Based on the information provided, I've analyzed the document and have the following observations:

The document appears to be a legal instrument that establishes certain rights and obligations between the parties involved. The language is structured in a formal manner consistent with legal documentation.

Several key provisions are present, including definitions of terms, scope of the agreement, rights and responsibilities of each party, duration of the agreement, and procedures for handling disputes or termination.

From a legal perspective, the document seems to follow standard formatting and structural conventions. However, specific analysis would require more context about the nature of the agreement and the specific legal questions being asked.

If you have specific questions about particular clauses or legal implications, please provide more details so I can offer more targeted analysis.

Note that this represents a general assessment and should not be considered legal advice. For binding legal opinions, please consult with a qualified attorney who can review the complete document in the appropriate context."""


class MockVectorService:
    """Mock vector service for development and testing."""
    
    def __init__(self, name="Mock Vector", dimensions=768):
        self.name = name
        self.dimensions = dimensions
        logger.info(f"Initialized {self.name} service with {dimensions} dimensions")
    
    def search(self, query, limit=10, case_id=None):
        """
        Search for similar documents.
        
        Args:
            query: Query string
            limit: Maximum number of results
            case_id: Optional case ID to filter results
            
        Returns:
            List of search results
        """
        # Log the request
        logger.info(f"Searching with {self.name} (query='{query[:50]}...', limit={limit}, case_id={case_id})")
        
        # Simulate processing time
        time.sleep(0.5)
        
        # Generate mock results
        results = []
        for i in range(min(limit, 5)):
            results.append({
                'id': f"doc_{random.randint(1000, 9999)}",
                'title': f"Sample Document {i+1}",
                'content': f"This is a sample document that matches the query: '{query}'",
                'score': round(0.95 - (i * 0.1), 2),
                'metadata': {
                    'author': f"Author {i+1}",
                    'date': datetime.now().isoformat(),
                    'case_id': case_id if case_id else random.randint(1, 100),
                }
            })
        
        return results
