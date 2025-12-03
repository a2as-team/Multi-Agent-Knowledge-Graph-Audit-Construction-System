"""
Helper utilities for working with ADK agents.
"""
import os
from dotenv import load_dotenv, find_dotenv
from typing import Optional, Dict, Any

from google.genai import types  # For creating message Content/Parts
from google.adk.agents import Agent
from google.adk.sessions import InMemorySessionService, Session
from google.adk.runners import Runner

from src.utils.logger import logger


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

        # Key Concept: run_async executes the agent logic and yields Events.
        # We iterate through events to find the final answer.
        async for event in self.runner.run_async(
            user_id=self.user_id, 
            session_id=self.session_id, 
            new_message=content
        ):
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

