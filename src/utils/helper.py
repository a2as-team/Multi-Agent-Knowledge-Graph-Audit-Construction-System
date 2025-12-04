"""
Helper utilities for working with ADK agents.
"""
import os
import re
import asyncio
import time
from dotenv import load_dotenv, find_dotenv
from typing import Optional, Dict, Any

from google.genai import types  # For creating message Content/Parts
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import Runner

try:
    from litellm import RateLimitError
except ImportError:
    # Fallback if litellm is not available
    RateLimitError = Exception

from src.utils.logger import logger
from src.utils.config import (
    GEMINI_FREE_TIER_WAIT_TIME,
    GEMINI_FREE_TIER_MIN_INTERVAL,
    MAX_RETRIES_ON_RATE_LIMIT,
    RETRY_BACKOFF_MULTIPLIER
)


def extract_retry_delay_from_error(error: Exception) -> Optional[float]:
    """
    Extract the retry delay from a rate limit error message.
    
    Gemini API error messages typically contain: "Please retry in X.XXs"
    Returns the delay in seconds, or None if not found.
    
    Args:
        error: The exception object containing the error message
        
    Returns:
        The retry delay in seconds, or None if not found
    """
    error_str = str(error)
    
    # Pattern to match "Please retry in X.XXs" or "retry in X.XX seconds"
    patterns = [
        r"retry in ([\d.]+)\s*s",  # Matches "retry in 35.75s" or "retry in 35.75 seconds"
        r"retry.*?([\d.]+)\s*seconds?",  # More flexible pattern
        r"RetryDelay.*?([\d.]+)",  # For structured error responses
        r"retry.*?([\d.]+)\s*second",  # Alternative format
    ]
    
    for pattern in patterns:
        match = re.search(pattern, error_str, re.IGNORECASE)
        if match:
            try:
                delay = float(match.group(1))
                # Sanity check: delay should be reasonable (between 1 second and 1 hour)
                if 1.0 <= delay <= 3600.0:
                    return delay
            except (ValueError, IndexError):
                continue
    
    return None


def load_env():
    """Load environment variables from .env file."""
    try:
        env_path = find_dotenv()
        if env_path:
            load_dotenv(env_path, override=True)
        else:
            # Try to load from project root
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent
            env_file = project_root / ".env"
            if env_file.exists():
                load_dotenv(env_file, override=True)
    except Exception:
        # If .env file has issues, continue without it
        pass


def get_neo4j_import_dir():
    """Gets the neo4j import directory from an environment variable."""
    load_env()
    neo4j_import_dir = os.getenv("NEO4J_IMPORT_DIR")
    return neo4j_import_dir


class AgentCaller:
    """A simple wrapper class for interacting with an ADK agent."""
    
    def __init__(self, agent: Agent, runner: Runner, user_id: str, session_id: str):
        """Initialize the AgentCaller with required components."""
        self.agent = agent
        self.runner = runner
        self.user_id = user_id
        self.session_id = session_id
    
    def get_session(self):
        """Get the current session."""
        return self.runner.session_service.get_session(
            app_name=self.runner.app_name, 
            user_id=self.user_id, 
            session_id=self.session_id
        )

    async def call(self, query: str, verbose: bool = False):
        """
        Call the agent with a query and return the response.
        Implements retry logic with exponential backoff for rate limit errors.
        
        Args:
            query: User query string
            verbose: Whether to print detailed event information
        
        Returns:
            Final response text from the agent
        """
        logger.info(f"User Query: {query}")

        # Prepare the user's message in ADK format
        content = types.Content(role='user', parts=[types.Part(text=query)])

        final_response_text = "Agent did not produce a final response."  # Default
        events_received = False

        # Retry logic for rate limit errors with exponential backoff
        retry_count = 0
        
        while retry_count <= MAX_RETRIES_ON_RATE_LIMIT:
            try:
                # Key Concept: run_async executes the agent logic and yields Events.
                # We iterate through events to find the final answer.
                async for event in self.runner.run_async(
                    user_id=self.user_id, 
                    session_id=self.session_id, 
                    new_message=content
                ):
                    events_received = True
                    # Log detailed event information if verbose
                    if verbose:
                        logger.debug(
                            f"Event - Author: {event.author}, "
                            f"Type: {type(event).__name__}, "
                            f"Final: {event.is_final_response()}, "
                            f"Content: {event.content}"
                        )

                    # Key Concept: is_final_response() marks the concluding message for the turn.
                    if event.is_final_response():
                        if event.content and event.content.parts:
                            # Assuming text response in the first part
                            final_response_text = event.content.parts[0].text
                        elif event.actions and event.actions.escalate:  # Handle potential errors/escalations
                            final_response_text = f"Agent escalated: {event.error_message or 'No specific message.'}"
                        if event.author == self.agent.name:
                            break  # Stop processing events once the final response is found
                
                # Check if we completed the event loop without getting a final response
                if final_response_text == "Agent did not produce a final response.":
                    if events_received:
                        # Agent processed the request but didn't produce a text response
                        # This can happen when the agent only calls tools without responding
                        # Check session state to see if approval was successful
                        session = self.runner.session_service.get_session(
                            app_name=self.runner.app_name,
                            user_id=self.user_id,
                            session_id=self.session_id
                        )
                        # Try to provide a helpful message based on context
                        if session and session.state:
                            # Check if approval was successful
                            from src.utils.constants import APPROVED_CONSTRUCTION_PLAN
                            if APPROVED_CONSTRUCTION_PLAN in session.state:
                                final_response_text = "Schema has been approved successfully."
                            else:
                                final_response_text = "Agent completed processing but did not produce a text response. Check the session state for results."
                    else:
                        # No events received at all - this is unusual
                        final_response_text = "Agent did not process the request. No events were generated."
                
                # Success - break retry loop
                break
                
            except RateLimitError as e:
                retry_count += 1
                if retry_count > MAX_RETRIES_ON_RATE_LIMIT:
                    logger.error(f"Max retries ({MAX_RETRIES_ON_RATE_LIMIT}) exceeded for rate limit error")
                    raise
                
                # Try to extract exact retry delay from error message
                extracted_delay = extract_retry_delay_from_error(e)
                
                if extracted_delay:
                    # Use the exact delay from the error message
                    wait_time = extracted_delay
                    logger.warning(
                        f"Rate limit error encountered (attempt {retry_count}/{MAX_RETRIES_ON_RATE_LIMIT}). "
                        f"Using exact retry delay from API: {wait_time:.2f} seconds..."
                    )
                else:
                    # Fall back to exponential backoff if we can't parse the delay
                    wait_time = GEMINI_FREE_TIER_WAIT_TIME * (RETRY_BACKOFF_MULTIPLIER ** (retry_count - 1))
                    logger.warning(
                        f"Rate limit error encountered (attempt {retry_count}/{MAX_RETRIES_ON_RATE_LIMIT}). "
                        f"Could not parse retry delay, using exponential backoff: {wait_time:.2f} seconds..."
                    )
                
                await asyncio.sleep(wait_time)
                
            except Exception as e:
                # Check if it's a RateLimitError wrapped in another exception
                error_str = str(e).lower()
                if "ratelimit" in error_str or "rate limit" in error_str or "429" in error_str:
                    retry_count += 1
                    if retry_count > MAX_RETRIES_ON_RATE_LIMIT:
                        logger.error(f"Max retries ({MAX_RETRIES_ON_RATE_LIMIT}) exceeded for rate limit error")
                        raise
                    
                    # Try to extract exact retry delay from error message
                    extracted_delay = extract_retry_delay_from_error(e)
                    
                    if extracted_delay:
                        wait_time = extracted_delay
                        logger.warning(
                            f"Rate limit error detected in exception (attempt {retry_count}/{MAX_RETRIES_ON_RATE_LIMIT}). "
                            f"Using exact retry delay from API: {wait_time:.2f} seconds..."
                        )
                    else:
                        wait_time = GEMINI_FREE_TIER_WAIT_TIME * (RETRY_BACKOFF_MULTIPLIER ** (retry_count - 1))
                        logger.warning(
                            f"Rate limit error detected in exception (attempt {retry_count}/{MAX_RETRIES_ON_RATE_LIMIT}). "
                            f"Could not parse retry delay, using exponential backoff: {wait_time:.2f} seconds..."
                        )
                    
                    await asyncio.sleep(wait_time)
                else:
                    # For other errors, check if it's a tool not found error
                    error_str = str(e)
                    if "not found in the tools_dict" in error_str or ("Function" in error_str and "not found" in error_str):
                        # Extract the function name from the error
                        import re
                        match = re.search(r"Function (\w+) is not found", error_str)
                        if match:
                            function_name = match.group(1)
                            logger.error(
                                f"Agent tried to call non-existent function: {function_name}. "
                                f"This is likely a model hallucination. Available tools should be listed in agent instructions."
                            )
                            # Provide a helpful error message
                            final_response_text = (
                                f"I apologize, but I tried to use a function called '{function_name}' that doesn't exist. "
                                "This may be due to model limitations. Please try rephrasing your request or use the exact tool names listed in the instructions."
                            )
                            # Break out of retry loop since this is not a retryable error
                            break
                    
                    # For other errors, log with more detail and re-raise
                    import traceback
                    logger.error(f"Unexpected error during agent call: {e}")
                    logger.error(f"Error type: {type(e).__name__}")
                    logger.error(f"Traceback: {traceback.format_exc()}")
                    raise

        self.session = self.runner.session_service.get_session(
            app_name=self.runner.app_name, 
            user_id=self.user_id, 
            session_id=self.session_id
        )

        logger.info(f"Agent Response: {final_response_text}")
        return final_response_text


async def make_agent_caller(
    agent: Agent, 
    initial_state: Optional[Dict[str, Any]] = None
) -> AgentCaller:
    """
    Create and return an AgentCaller instance for the given agent.
    
    Args:
        agent: The ADK Agent instance
        initial_state: Optional initial state dictionary for the session
    
    Returns:
        AgentCaller instance ready to use
    """
    if initial_state is None:
        initial_state = {}
    
    session_service = InMemorySessionService()
    app_name = agent.name + "_app"
    user_id = agent.name + "_user"
    session_id = agent.name + "_session_01"
    
    # Initialize a session
    await session_service.create_session(
        app_name=app_name,
        user_id=user_id,
        session_id=session_id,
        state=initial_state
    )
    
    runner = Runner(
        agent=agent,
        app_name=app_name,
        session_service=session_service
    )
    
    logger.info(f"Created AgentCaller for agent: {agent.name}")
    return AgentCaller(agent, runner, user_id, session_id)

