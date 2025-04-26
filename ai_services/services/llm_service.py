"""
LLM service for Gemma 3 integration.

This module provides the service for interacting with Gemma 3 models
for various legal tasks.
"""

import time
import logging
import requests
import json
from typing import Dict, Any, Optional, List, Union
from django.utils import timezone
from django.conf import settings
from ..models import LLMModel, AIAnalysisRequest, AIAnalysisResult
from .. import settings as ai_settings

logger = logging.getLogger(__name__)

class GemmaService:
    """Service for interacting with Gemma 3 model."""
    
    def __init__(self, model_instance: LLMModel):
        """
        Initialize with a model instance from the database.
        
        Args:
            model_instance: The LLM model configuration
        """
        self.model = model_instance
        self.endpoint_url = model_instance.endpoint_url
        self.api_key = model_instance.api_key
        self.default_params = {
            "temperature": model_instance.temperature,
            "max_tokens": model_instance.max_tokens,
        }
        logger.info(f"Initialized GemmaService with model: {model_instance.name}")
    
    def generate_text(self, 
                      prompt: str, 
                      system_prompt: Optional[str] = None,
                      **kwargs) -> Dict[str, Any]:
        """
        Generate text using the Gemma 3 model.
        
        Args:
            prompt: The user prompt
            system_prompt: Optional system prompt
            **kwargs: Additional parameters to override defaults
            
        Returns:
            Dictionary containing the response and metadata
        """
        logger.info(f"Generating text with model: {self.model.name}")
        start_time = time.time()
        
        # Prepare parameters
        params = {**self.default_params, **kwargs}
        
        # Combine system prompt and user prompt if both are provided
        combined_prompt = prompt
        if system_prompt:
            # For models that don't natively support system prompts, we prepend it to the user prompt
            if self.model.deployment_type in ['local', 'containerized']:
                combined_prompt = f"{system_prompt}\n\n{prompt}"
        
        # Prepare the request payload based on deployment type
        if self.model.deployment_type == 'vllm':
            payload = {
                "prompt": combined_prompt,
                "temperature": float(params.get("temperature", 0.7)),
                "max_tokens": int(params.get("max_tokens", 4096)),
                "stop": params.get("stop", []),
            }
            if system_prompt and self.model.deployment_type == 'vllm':
                payload["system_prompt"] = system_prompt
                
        elif self.model.deployment_type == 'api':
            # Format for LM Studio or similar API
            model_to_use = f"{self.model.model_type}-{self.model.model_version}"
            
            # For LM Studio, we need to use the model name as it appears in the UI
            if "LM Studio" in self.model.name:
                model_to_use = ai_settings.DEFAULT_MODEL_NAME
            
            payload = {
                "model": model_to_use,
                "prompt": combined_prompt,
                "temperature": float(params.get("temperature", 0.7)),
                "max_tokens": int(params.get("max_tokens", 4096)),
            }
            
            # Some APIs support system prompts directly
            if system_prompt and "system_prompt" in kwargs:
                payload["system_prompt"] = system_prompt
        else:
            # Default format for containerized deployments
            payload = {
                "model": f"{self.model.model_type}-{self.model.model_version}",
                "prompt": combined_prompt,
                "temperature": float(params.get("temperature", 0.7)),
                "max_length": int(params.get("max_tokens", 4096)),
            }
            
        # Prepare headers
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
            
        logger.debug(f"Request payload: {json.dumps(payload, indent=2)}")
        
        try:
            # Send request to the LLM API
            response = requests.post(
                self.endpoint_url,
                json=payload,
                headers=headers,
                timeout=ai_settings.LLM_REQUEST_TIMEOUT
            )
            response.raise_for_status()
            result = response.json()
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            logger.debug(f"Response: {json.dumps(result, indent=2)}")
            
            # Extract the generated text based on the response format
            if 'choices' in result and len(result['choices']) > 0:
                if 'message' in result['choices'][0]:
                    # OpenAI-like format
                    generated_text = result['choices'][0]['message']['content']
                elif 'text' in result['choices'][0]:
                    # vLLM-like format
                    generated_text = result['choices'][0]['text']
                else:
                    generated_text = str(result['choices'][0])
            elif 'output' in result:
                # Simple output format
                generated_text = result['output']
            elif 'response' in result:
                # Another common format
                generated_text = result['response']
            elif 'generated_text' in result:
                # Yet another format
                generated_text = result['generated_text']
            else:
                # Fallback
                generated_text = str(result)
                
            logger.info(f"Successfully generated text in {processing_time:.2f} seconds")
            
            return {
                "text": generated_text,
                "raw_response": result,
                "tokens_used": result.get("usage", {}).get("total_tokens", 0),
                "processing_time": processing_time,
                "error": None
            }
            
        except requests.exceptions.RequestException as e:
            end_time = time.time()
            processing_time = end_time - start_time
            
            error_message = f"Request error: {str(e)}"
            if hasattr(e, 'response') and e.response is not None:
                error_message += f" (Status code: {e.response.status_code})"
                try:
                    error_message += f" - {e.response.text}"
                except:
                    pass
                    
            logger.error(error_message)
            
            return {
                "text": "",
                "raw_response": {},
                "tokens_used": 0,
                "processing_time": processing_time,
                "error": error_message
            }
            
        except Exception as e:
            end_time = time.time()
            processing_time = end_time - start_time
            
            error_message = f"Unexpected error: {str(e)}"
            logger.error(error_message)
            
            return {
                "text": "",
                "raw_response": {},
                "tokens_used": 0,
                "processing_time": processing_time,
                "error": error_message
            }
    
    @classmethod
    def process_analysis_request(cls, request_id: int) -> Optional[AIAnalysisResult]:
        """
        Process an AI analysis request from the database.
        
        Args:
            request_id: ID of the AIAnalysisRequest to process
            
        Returns:
            The created AIAnalysisResult or None if processing failed
        """
        try:
            # Get the analysis request
            analysis_request = AIAnalysisRequest.objects.get(id=request_id)
            
            # Update status to processing
            analysis_request.status = 'PROCESSING'
            analysis_request.save(update_fields=['status'])
            
            logger.info(f"Processing analysis request {request_id} for document: {analysis_request.document.title if analysis_request.document else 'N/A'}")
            
            # Get the LLM model
            model = analysis_request.llm_model
            
            # Create service instance
            service = cls(model)
            
            # Get the system prompt if available
            system_prompt = None
            if analysis_request.prompt_template and analysis_request.prompt_template.system_prompt:
                system_prompt = analysis_request.prompt_template.system_prompt
            
            # Generate text
            result = service.generate_text(
                prompt=analysis_request.combined_prompt,
                system_prompt=system_prompt
            )
            
            # Create the result
            ai_result = AIAnalysisResult.objects.create(
                analysis_request=analysis_request,
                output_text=result["text"],
                raw_response=result["raw_response"],
                tokens_used=result["tokens_used"],
                processing_time=result["processing_time"],
                has_error=bool(result["error"]),
                error_message=result["error"] or ""
            )
            
            # Update the request status
            analysis_request.status = 'COMPLETED' if not result["error"] else 'FAILED'
            analysis_request.completed_at = timezone.now()
            analysis_request.save(update_fields=['status', 'completed_at'])
            
            logger.info(f"Completed analysis request {request_id} with status: {analysis_request.status}")
            
            return ai_result
            
        except AIAnalysisRequest.DoesNotExist:
            logger.error(f"Analysis request {request_id} not found")
            return None
            
        except Exception as e:
            logger.error(f"Error processing analysis request {request_id}: {str(e)}")
            
            # Update request status if possible
            try:
                if 'analysis_request' in locals():
                    analysis_request.status = 'FAILED'
                    analysis_request.completed_at = timezone.now()
                    analysis_request.save(update_fields=['status', 'completed_at'])
                    
                    AIAnalysisResult.objects.create(
                        analysis_request=analysis_request,
                        output_text="",
                        raw_response={},
                        has_error=True,
                        error_message=str(e)
                    )
            except Exception as inner_e:
                logger.error(f"Error updating analysis request status: {str(inner_e)}")
                
            return None
