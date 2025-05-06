import logging
import click
from google_a2a.common.types import AgentSkill, AgentCapabilities, AgentCard
from google_a2a.common.server import A2AServer
from a2a_demo.task_manager import MyAgentTaskManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def echo_agent(host, port, ollama_host, ollama_model, math_agent_url):
    """Run the Echo Agent that can delegate math questions to the Math Agent"""
    # Define the Echo Agent's skill
    skill = AgentSkill(
        id="my-project-echo-skill",
        name="Echo Tool",
        description="Echos the input given, and delegates math questions to a Math Agent",
        tags=["echo", "repeater", "delegation"],
        examples=["I will see this echoed back to me", "What is 25 * 13?"],
        inputModes=["text"],
        outputModes=["text"],
    )
    logger.info(skill)

    # Define the agent's capabilities
    capabilities = AgentCapabilities(
        streaming=True,
    )
    
    # Create the Agent Card
    agent_card = AgentCard(
        name="Echo Agent",
        description="An agent that echoes your input and delegates math questions",
        url=f"http://{host}:{port}/",
        version="0.1.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=capabilities,
        skills=[skill]
    )
    logger.info(agent_card)

    # Initialize task manager and server
    task_manager = MyAgentTaskManager(
        ollama_host=ollama_host,
        ollama_model=ollama_model,
        math_agent_url=math_agent_url
    )
    server = A2AServer(
        agent_card=agent_card,
        task_manager=task_manager,
        host=host,
        port=port,
    )
    server.start()

def math_agent(host, port):
    """Run the Math Agent"""
    try:
        # Import here to avoid circular imports
        from a2a_demo.math_agent import main as math_main
        # Since math_main is a Click command, we need to invoke it in a different way
        from a2a_demo import math_agent
        math_agent.main(["--host", host, "--port", str(port)])
    except Exception as e:
        logger.error(f"Failed to start Math Agent: {e}")
        logger.error("Math Agent will not be available")

@click.command()
@click.option("--echo-host", default="localhost")
@click.option("--echo-port", default=10002)
@click.option("--math-host", default="localhost")
@click.option("--math-port", default=10003)
@click.option("--ollama-host", default="http://localhost:11434")
@click.option("--ollama-model", default="llama3.2")
@click.option("--not-start-math", is_flag=True, default=False, help="Whether not to start the Math Agent")
def main(echo_host, echo_port, math_host, math_port, ollama_host, ollama_model, not_start_math):
    """Run both Echo and Math agents simultaneously"""
    import threading
    import time
    
    math_thread = None
    if not not_start_math:
        # Start the Math Agent in a separate thread
        math_thread = threading.Thread(
            target=math_agent,
            kwargs={"host": math_host, "port": math_port}
        )
        math_thread.daemon = True
        math_thread.start()
        
        # Give the Math Agent a moment to start up
        time.sleep(2)
    
    # Start the Echo Agent in the main thread
    math_agent_url = f"http://{math_host}:{math_port}" if not not_start_math else None
    echo_agent(
        host=echo_host,
        port=echo_port,
        ollama_host=ollama_host,
        ollama_model=ollama_model,
        math_agent_url=math_agent_url
    )


if __name__ == "__main__":
    main()