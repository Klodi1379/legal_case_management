import time
import logging
import requests
from typing import Dict, Any, Optional
from django.utils import timezone
from ..models import LLMModel, AIAnalysisRequest, AIAnalysisResult

logger = logging.getLogger(__name__)

class MockGemmaService:
    """Mock service for simulating Gemma 3 model responses."""

    def __init__(self, model_instance: LLMModel):
        """Initialize with a model instance from the database."""
        self.model = model_instance
        self.default_params = {
            "temperature": model_instance.temperature,
            "max_tokens": model_instance.max_tokens,
        }

    def generate_text(self,
                      prompt: str,
                      system_prompt: Optional[str] = None,
                      **kwargs) -> Dict[str, Any]:
        """
        Generate text using the Gemma 3 model if available, otherwise use mock responses.

        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters to override defaults

        Returns:
            Dictionary containing the response and metadata
        """
        logger.info("=== STARTING GENERATE_TEXT METHOD ===")
        logger.info(f"Model: {self.model.name} ({self.model.model_version})")
        logger.info(f"Endpoint URL: {self.model.endpoint_url}")
        logger.info(f"Prompt length: {len(prompt)} characters")
        if system_prompt:
            logger.info(f"System prompt length: {len(system_prompt)} characters")
        else:
            logger.info("No system prompt provided")

        start_time = time.time()

        # Prepare parameters
        params = {**self.default_params, **kwargs}

        # Try to use the real Gemma 3 service first
        try:
            # Prepare the request payload based on deployment type
            if self.model.deployment_type == 'vllm':
                payload = {
                    "prompt": prompt,
                    "temperature": float(params.get("temperature", 0.7)),
                    "max_tokens": int(params.get("max_tokens", 4096)),
                    "stop": params.get("stop", []),
                }
                if system_prompt:
                    payload["system_prompt"] = system_prompt

            elif self.model.deployment_type == 'api':
                # First, check available models
                try:
                    models_url = "http://127.0.0.1:1234/v1/models"
                    models_response = requests.get(models_url, timeout=5)
                    models_response.raise_for_status()
                    models_data = models_response.json()
                    available_models = [model['id'] for model in models_data.get('data', [])]
                    logger.info(f"Available models: {available_models}")

                    # Look for the preferred model (gemma-3-12b-it-qat)
                    preferred_model = "gemma-3-12b-it-qat"
                    model_to_use = None

                    # First try to find the exact preferred model
                    if preferred_model in available_models:
                        model_to_use = preferred_model
                        logger.info(f"Found preferred model: {preferred_model}")
                    else:
                        # Try to find a model with similar name
                        for model_name in available_models:
                            if "gemma-3" in model_name.lower() and "12b" in model_name.lower():
                                model_to_use = model_name
                                logger.info(f"Found similar model to preferred: {model_name}")
                                break

                    # If still no model found, use the first available
                    if not model_to_use and available_models:
                        model_to_use = available_models[0]
                        logger.info(f"Using first available model: {model_to_use}")
                    elif not model_to_use:
                        model_to_use = preferred_model
                        logger.warning(f"No models available, defaulting to: {preferred_model}")
                except Exception as e:
                    logger.warning(f"Failed to get available models: {str(e)}")
                    model_to_use = "gemma-3-1b-it-qat"

                # For completions endpoint (more reliable with LM Studio)
                combined_prompt = ""
                if system_prompt:
                    combined_prompt = f"{system_prompt}\n\n"
                combined_prompt += prompt

                payload = {
                    "model": model_to_use,  # Use the model name from LM Studio
                    "prompt": combined_prompt,
                    "temperature": float(params.get("temperature", 0.7)),
                    "max_tokens": int(params.get("max_tokens", 4096)),
                }
            else:
                # Default format for containerized deployments
                payload = {
                    "model": f"{self.model.model_type}-{self.model.model_version}",
                    "prompt": prompt,
                    "system_prompt": system_prompt or "",
                    "temperature": float(params.get("temperature", 0.7)),
                    "max_length": int(params.get("max_tokens", 4096)),
                }

            # Try to connect to the real Gemma 3 service
            logger.info(f"Attempting to connect to Gemma 3 service at {self.model.endpoint_url}")
            logger.info(f"Payload: {payload}")

            # Try with a shorter timeout first to avoid blocking the UI
            try:
                response = requests.post(
                    self.model.endpoint_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=5  # Short timeout for initial attempt
                )
            except requests.exceptions.Timeout:
                logger.warning("Initial request timed out, trying with longer timeout...")
                # If it times out, try again with a longer timeout
                response = requests.post(
                    self.model.endpoint_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=60  # Longer timeout for second attempt
                )
            response.raise_for_status()
            result = response.json()

            end_time = time.time()
            processing_time = end_time - start_time

            # Extract the generated text based on the response format
            if 'choices' in result and len(result['choices']) > 0:
                if 'message' in result['choices'][0]:
                    # OpenAI-like chat format
                    generated_text = result['choices'][0]['message']['content']
                elif 'text' in result['choices'][0]:
                    # Completions format (LM Studio uses this)
                    generated_text = result['choices'][0]['text']
                else:
                    # Fallback to string representation
                    generated_text = str(result['choices'][0])
            elif 'output' in result:
                # Simple output format
                generated_text = result['output']
            elif 'text' in result:
                # Direct text format
                generated_text = result['text']
            else:
                # Last resort fallback
                generated_text = str(result)

            logger.info(f"Generated text (first 100 chars): {generated_text[:100]}...")

            # Log successful connection to Gemma 3
            logger.info(f"Successfully connected to Gemma 3 service at {self.model.endpoint_url}")

            return {
                "text": generated_text,
                "raw_response": result,
                "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                "processing_time": processing_time,
                "error": None
            }

        except requests.exceptions.RequestException as e:
            # Handle request-specific exceptions
            logger.warning(f"Request to Gemma 3 service failed: {str(e)}. Using mock response instead.")
            if hasattr(e, 'response') and e.response is not None:
                logger.warning(f"Response status code: {e.response.status_code}")
                try:
                    logger.warning(f"Response content: {e.response.text}")
                except:
                    pass

            # Generate a mock response based on the prompt
            if "summarize" in prompt.lower() or "summary" in prompt.lower():
                generated_text = self._generate_summary_response(prompt)
            elif "analyze" in prompt.lower() or "analysis" in prompt.lower():
                generated_text = self._generate_analysis_response(prompt)
            elif "research" in prompt.lower():
                generated_text = self._generate_research_response(prompt)
            elif "case management" in prompt.lower() or "legal case" in prompt.lower():
                generated_text = self._generate_case_management_response(prompt)
            else:
                generated_text = self._generate_generic_response(prompt)

            end_time = time.time()
            processing_time = end_time - start_time

            # Simulate token usage based on output length
            tokens_used = len(generated_text.split()) * 1.3

            return {
                "text": generated_text,
                "raw_response": {
                    "model": f"{self.model.model_type}-{self.model.model_version}",
                    "usage": {"total_tokens": int(tokens_used)},
                    "choices": [{"text": generated_text}],
                    "mock_response": True  # Indicate this is a mock response
                },
                "tokens_used": int(tokens_used),
                "processing_time": processing_time,
                "error": None
            }

        except Exception as e:
            # If the real service fails, fall back to mock responses
            logger.warning(f"Failed to connect to Gemma 3 service: {str(e)}. Using mock response instead.")

            # Generate a mock response based on the prompt
            if "summarize" in prompt.lower() or "summary" in prompt.lower():
                generated_text = self._generate_summary_response(prompt)
            elif "analyze" in prompt.lower() or "analysis" in prompt.lower():
                generated_text = self._generate_analysis_response(prompt)
            elif "research" in prompt.lower():
                generated_text = self._generate_research_response(prompt)
            elif "case management" in prompt.lower() or "legal case" in prompt.lower():
                generated_text = self._generate_case_management_response(prompt)
            else:
                generated_text = self._generate_generic_response(prompt)

            end_time = time.time()
            processing_time = end_time - start_time

            # Simulate token usage based on output length
            tokens_used = len(generated_text.split()) * 1.3

            return {
                "text": generated_text,
                "raw_response": {
                    "model": f"{self.model.model_type}-{self.model.model_version}",
                    "usage": {"total_tokens": int(tokens_used)},
                    "choices": [{"text": generated_text}],
                    "mock_response": True  # Indicate this is a mock response
                },
                "tokens_used": int(tokens_used),
                "processing_time": processing_time,
                "error": None
            }

    def _generate_summary_response(self, prompt: str) -> str:
        """Generate a mock summary response."""
        return """# Document Summary

This document appears to be a legal agreement between two parties. The key points are:

1. **Parties Involved**: The agreement is between Party A and Party B.
2. **Effective Date**: The agreement takes effect from the date of signing.
3. **Term**: The initial term is 12 months with automatic renewal provisions.
4. **Obligations**:
   - Party A is responsible for providing services as outlined in Exhibit A.
   - Party B is responsible for payment and cooperation.
5. **Payment Terms**: Net 30 days from invoice date with a 1.5% late fee.
6. **Termination**: Either party may terminate with 30 days written notice.
7. **Confidentiality**: Both parties agree to maintain confidentiality of shared information.
8. **Governing Law**: This agreement is governed by the laws of the State of California.

## Risk Assessment
The agreement appears to be a standard service contract with balanced terms. No significant legal risks were identified in the initial review."""

    def _generate_analysis_response(self, prompt: str) -> str:
        """Generate a mock analysis response."""
        return """# Contract Analysis

## Key Provisions

1. **Indemnification Clause (Section 8)**
   - Party A agrees to indemnify Party B against third-party claims
   - The indemnification is limited to direct damages
   - There is a cap on liability equal to fees paid in the previous 12 months

2. **Limitation of Liability (Section 9)**
   - Neither party is liable for consequential, incidental, or special damages
   - Total liability is capped at fees paid during the previous 12 months
   - Exclusions apply for breaches of confidentiality and intellectual property

3. **Intellectual Property (Section 10)**
   - Each party retains ownership of its pre-existing IP
   - Party B receives a limited license to use Party A's IP solely for the purposes outlined in the agreement
   - New IP created specifically for Party B is assigned to Party B upon full payment

## Potential Issues

1. The indemnification clause lacks reciprocity - Party A bears most of the risk
2. The limitation of liability may be insufficient for high-value transactions
3. The IP assignment provisions could be clearer regarding jointly developed materials

## Recommendations

1. Consider negotiating mutual indemnification provisions
2. Review the liability cap to ensure it's appropriate for the contract value
3. Clarify ownership of jointly developed intellectual property"""

    def _generate_research_response(self, prompt: str) -> str:
        """Generate a mock legal research response."""
        return """# Legal Research: Force Majeure Clauses Post-COVID

## Summary of Findings

Courts have significantly evolved their interpretation of force majeure clauses following the COVID-19 pandemic. The key developments include:

1. **Broader Interpretation**: Courts are now more willing to consider pandemics and public health emergencies as qualifying events under force majeure provisions, even when not explicitly listed.

2. **Foreseeability Standard**: The standard for what constitutes an "unforeseeable" event has shifted. Post-COVID, courts expect parties to anticipate potential pandemic scenarios in their contracts.

3. **Causation Requirements**: Courts have maintained strict causation requirements, requiring parties to demonstrate that their non-performance was directly caused by the force majeure event rather than merely made more difficult or expensive.

4. **Notice Provisions**: Strict compliance with notice requirements remains essential, with courts showing little leniency for delayed or improper notice.

## Key Cases

1. **ABC Corp v. XYZ Inc.** (S.D.N.Y. 2022): Court held that COVID-19 qualified as a force majeure event under a clause listing "epidemics" but not "pandemics," adopting a purposive interpretation.

2. **Smith Enterprises v. Johnson Manufacturing** (7th Cir. 2023): Court rejected a force majeure defense where the contract was signed in late 2020, finding that pandemic risks were foreseeable at that time.

3. **Global Shipping v. Continental Freight** (5th Cir. 2022): Court enforced strict causation requirements, finding that supply chain disruptions alone did not excuse performance without showing impossibility.

## Recommendations

1. Draft force majeure clauses with explicit reference to pandemics, epidemics, and public health emergencies
2. Include specific language addressing government orders and regulations
3. Clearly define the standard for causation (impossibility vs. impracticability)
4. Establish detailed notice requirements and procedures
5. Consider including provisions for contract adaptation rather than mere termination or suspension"""

    def _generate_case_management_response(self, prompt: str) -> str:
        """Generate a detailed response about legal case management systems."""
        return """# Key Components of a Legal Case Management System

As a legal assistant, I can provide a comprehensive overview of the essential components that make up an effective legal case management system:

## 1. Case Information Management
- **Case Intake & Classification**: Tools for capturing initial case details, categorizing by practice area, and assigning priority levels
- **Case Timeline Tracking**: Visual representation of case progress, key dates, and statute of limitations monitoring
- **Party Management**: Storage of all parties involved in a case (clients, opposing parties, witnesses, experts, etc.)
- **Court Information**: Integration with court systems for docket information, filing deadlines, and judge preferences

## 2. Document Management
- **Document Repository**: Centralized storage for all case-related documents with version control
- **Document Generation**: Templates for creating standard legal documents with auto-population of case data
- **Document Analysis**: AI-powered tools for reviewing and extracting key information from legal documents
- **E-Filing Integration**: Direct connection to court e-filing systems for streamlined submissions

## 3. Client Relationship Management
- **Client Profiles**: Comprehensive client information including contact details, communication preferences, and relationship history
- **Client Portal**: Secure interface for clients to view case status, access documents, and communicate with legal team
- **Conflict Checking**: Automated tools to identify potential conflicts of interest with new clients or cases
- **Client Billing**: Integration with billing systems for time tracking, expense recording, and invoice generation

## 4. Workflow Automation
- **Task Management**: Assignment and tracking of case-related tasks with due dates and priorities
- **Workflow Templates**: Predefined sequences of tasks for common case types to ensure consistency
- **Notification System**: Automated alerts for upcoming deadlines, new assignments, and status changes
- **Approval Processes**: Structured workflows for document review, settlement approvals, and other key decisions

## 5. Calendar & Scheduling
- **Court Date Management**: Tracking of hearings, trials, and other court appearances
- **Team Scheduling**: Coordination of attorney and staff availability for case-related events
- **Deadline Calculation**: Automated calculation of procedural deadlines based on jurisdiction rules
- **Calendar Integration**: Synchronization with personal calendars (Outlook, Google Calendar, etc.)

## 6. Communication Tools
- **Internal Messaging**: Secure communication between team members about case matters
- **Client Communication**: Tracked email and messaging with clients, including template responses
- **External Correspondence**: Management of communications with opposing counsel, courts, and other parties
- **Call Logging**: Recording of phone conversations with automatic association to relevant cases

## 7. Time & Billing Integration
- **Time Tracking**: Tools for recording billable hours directly associated with specific cases
- **Expense Management**: Tracking of case-related expenses for client billing and cost recovery
- **Budget Monitoring**: Comparison of actual time/expenses against estimated budgets
- **Invoice Generation**: Creation of detailed client invoices based on recorded time and expenses

## 8. Reporting & Analytics
- **Case Performance Metrics**: Analysis of case outcomes, durations, and profitability
- **Attorney Productivity**: Measurement of individual and team performance metrics
- **Financial Reporting**: Analysis of revenue, receivables, and profitability by practice area
- **Custom Dashboards**: Configurable views of key performance indicators for different user roles

## 9. Security & Compliance
- **Access Controls**: Role-based permissions to ensure appropriate information access
- **Audit Trails**: Comprehensive logging of all system activities for compliance and security
- **Data Encryption**: Protection of sensitive client and case information
- **Compliance Tools**: Features to ensure adherence to relevant regulations (GDPR, HIPAA, etc.)

## 10. AI & Advanced Features
- **Legal Research Integration**: Connection to legal research platforms with AI-assisted search
- **Predictive Analytics**: Tools to forecast case outcomes, costs, and durations
- **Document Analysis**: AI-powered contract review and due diligence assistance
- **Knowledge Management**: Systems to capture and leverage institutional knowledge and precedents

## Implementation Considerations
For successful implementation, consider these factors:
- **Scalability**: Ability to grow with the firm's needs
- **Integration Capabilities**: Compatibility with existing systems (accounting, email, etc.)
- **Mobile Access**: Secure access from smartphones and tablets
- **Training & Support**: Comprehensive onboarding and ongoing technical assistance
- **Customization Options**: Flexibility to adapt to specific practice areas and firm workflows

A well-designed legal case management system should streamline administrative tasks, improve collaboration, enhance client service, and ultimately allow legal professionals to focus more on practicing law rather than managing information.
"""

    def _generate_generic_response(self, prompt: str) -> str:
        """Generate a generic response for other types of prompts."""
        return """Thank you for your query. Based on my analysis, here are my thoughts:

The legal case management system you're implementing provides a comprehensive solution for managing legal matters, client information, and document workflows. The integration with Gemma 3 AI capabilities enhances the system's functionality by providing automated document analysis, legal research assistance, and semantic search capabilities.

Key components of the system include:

1. **Case Management**: Tracking case details, status, and associated parties
2. **Document Management**: Storing, organizing, and analyzing legal documents
3. **Client Management**: Managing client information and communications
4. **AI Integration**: Leveraging Gemma 3 for intelligent document processing
5. **Reporting**: Generating insights and analytics on case progress

The system architecture follows modern best practices with a modular design that separates concerns and allows for future expansion. The Django framework provides a solid foundation for building secure, scalable web applications.

For optimal performance, I recommend:
- Implementing regular database backups
- Setting up monitoring for the AI services
- Conducting user training to ensure adoption
- Establishing clear data governance policies

Please let me know if you need more specific information on any aspect of the system."""

    @classmethod
    def process_analysis_request(cls, request_id: int) -> None:
        """
        Process an AI analysis request from the database using the mock service.

        Args:
            request_id: ID of the AIAnalysisRequest to process
        """
        logger.info(f"=== STARTING PROCESS_ANALYSIS_REQUEST FOR ID {request_id} ===")
        try:
            # Get the analysis request
            analysis_request = AIAnalysisRequest.objects.get(id=request_id)
            logger.info(f"Found analysis request: {analysis_request.id} (status: {analysis_request.status})")

            # Update status to processing
            analysis_request.status = 'processing'
            analysis_request.save()
            logger.info(f"Updated status to 'processing'")

            # Get the model and create service instance
            model = analysis_request.llm_model
            logger.info(f"Using model: {model.name} ({model.model_version})")
            logger.info(f"Model endpoint URL: {model.endpoint_url}")

            service = cls(model)
            logger.info(f"Created service instance: {service.__class__.__name__}")

            # Get the system prompt if available
            system_prompt = analysis_request.prompt_template.system_prompt if analysis_request.prompt_template else None
            logger.info(f"System prompt: {system_prompt[:100]}..." if system_prompt else "No system prompt")

            # Log the prompt
            logger.info(f"Combined prompt: {analysis_request.combined_prompt[:100]}...")

            # Generate text
            logger.info(f"Generating text...")
            result = service.generate_text(
                prompt=analysis_request.combined_prompt,
                system_prompt=system_prompt
            )
            logger.info(f"Text generation complete")

            # Save the result
            logger.info(f"Saving result to database...")

            # Convert processing_time from float to timedelta
            from datetime import timedelta
            processing_time_seconds = result["processing_time"]
            processing_time_delta = timedelta(seconds=processing_time_seconds)

            ai_result = AIAnalysisResult.objects.create(
                analysis_request=analysis_request,
                output_text=result["text"],
                raw_response=result["raw_response"],
                tokens_used=result["tokens_used"],
                processing_time=processing_time_delta,
                has_error=bool(result["error"]),
                error_message=result["error"] or ""
            )
            logger.info(f"Result saved with ID: {ai_result.id}")

            # Update the request status
            new_status = 'completed' if not result["error"] else 'failed'
            logger.info(f"Updating request status to: {new_status}")
            analysis_request.status = new_status
            analysis_request.completed_at = timezone.now()
            analysis_request.save()
            logger.info(f"Request status updated successfully")

            logger.info(f"=== COMPLETED PROCESS_ANALYSIS_REQUEST FOR ID {request_id} ===")
            return ai_result

        except Exception as e:
            logger.error(f"Error processing analysis request {request_id}: {str(e)}", exc_info=True)

            if 'analysis_request' in locals():
                logger.info(f"Updating request status to 'failed'")
                analysis_request.status = 'failed'
                analysis_request.save()

                logger.info(f"Creating error result")
                error_result = AIAnalysisResult.objects.create(
                    analysis_request=analysis_request,
                    output_text="",
                    raw_response={},
                    has_error=True,
                    error_message=str(e)
                )
                logger.info(f"Error result created with ID: {error_result.id}")

            logger.info(f"=== FAILED PROCESS_ANALYSIS_REQUEST FOR ID {request_id} ===")
            return None
