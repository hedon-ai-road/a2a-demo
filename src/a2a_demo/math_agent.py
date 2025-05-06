import logging
import re
import click
from google_a2a.common.types import AgentSkill, AgentCapabilities, AgentCard
from google_a2a.common.server import A2AServer
from a2a_demo.math_task_manager import MathAgentTaskManager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@click.command()
@click.option("--host", default="localhost")
@click.option("--port", default=10003)
def main(host, port):
    # Define the Math Agent's skill
    skill = AgentSkill(
        id="math-calculation-skill",
        name="Math Calculator",
        description="Performs mathematical calculations",
        tags=["math", "calculator", "arithmetic"],
        examples=["What is 25 * 13?", "Calculate the square root of 144"],
        inputModes=["text"],
        outputModes=["text"],
    )
    logging.info(skill)

    # Define the agent's capabilities
    capabilities = AgentCapabilities(
        streaming=False,  # For simplicity, let's not use streaming in the math agent
    )
    
    # Create the Agent Card
    agent_card = AgentCard(
        name="Math Agent",
        description="An agent that performs mathematical calculations",
        url=f"http://{host}:{port}/",
        version="0.1.0",
        defaultInputModes=["text"],
        defaultOutputModes=["text"],
        capabilities=capabilities,
        skills=[skill]
    )
    logging.info(agent_card)

    # Initialize task manager and server
    task_manager = MathAgentTaskManager()
    server = A2AServer(
        agent_card=agent_card,
        task_manager=task_manager,
        host=host,
        port=port,
    )
    server.start()

if __name__ == "__main__":
    main()