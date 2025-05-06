from typing import AsyncIterable
import typing
import re
import uuid
import logging
import requests
import time

from google_a2a.common.server.task_manager import InMemoryTaskManager
from google_a2a.common.types import(
    Artifact,
    JSONRPCResponse,
    Message,
    SendTaskRequest,
    SendTaskResponse,
    SendTaskStreamingRequest,
    SendTaskStreamingResponse,
    Task,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
)

import asyncio

from a2a_demo.agent import create_ollama_agent, run_ollama

logger = logging.getLogger(__name__)

class MathAgentClient:
    """Client for communicating with the Math Agent"""
    
    def __init__(self, math_agent_url=None, max_retries=3, retry_delay=2):
        self.math_agent_url = math_agent_url
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.agent_card = None
        
        # Don't try to connect if URL is None
        if self.math_agent_url:
            self._fetch_agent_card_with_retry()
    
    def _fetch_agent_card_with_retry(self):
        """Fetch the Math Agent's card with retry logic"""
        retries = 0
        while retries < self.max_retries:
            if self._fetch_agent_card():
                return True
            retries += 1
            if retries < self.max_retries:
                logger.info(f"Retrying connection to Math Agent in {self.retry_delay} seconds (attempt {retries+1}/{self.max_retries})...")
                time.sleep(self.retry_delay)
        return False

    def _fetch_agent_card(self):
        """Fetch the Math Agent's card to verify it's available"""
        if not self.math_agent_url:
            logger.warning("No Math Agent URL provided. Math delegation will be disabled.")
            return False
            
        try:
            response = requests.get(f"{self.math_agent_url}/.well-known/agent.json", timeout=5)
            response.raise_for_status()
            self.agent_card = response.json()
            logger.info(f"Connected to Math Agent: {self.agent_card.get('name')}")
            return True
        except requests.exceptions.ConnectionError as e:
            logger.warning(f"Failed to connect to Math Agent: {e}")
            return False
        except Exception as e:
            logger.warning(f"Error connecting to Math Agent: {e}")
            return False
    
    def is_available(self):
        """Check if the Math Agent is available"""
        return self.agent_card is not None
    
    def solve_math_problem(self, math_text):
        """
        Solve a math problem using either the Math Agent or local solver.
        """
        # Try to delegate to Math Agent first, fall back to local solver if needed
        if self.is_available():
            try:
                result = self._try_math_agent(math_text)
                if "Error" not in result and "failed" not in result:
                    return result
            except Exception as e:
                logger.warning(f"Math Agent error: {e}, falling back to local solver")
        
        # Fall back to local solver
        return self._solve_locally(math_text)
    
    def _try_math_agent(self, math_text):
        """Try to delegate to Math Agent"""
        task_id = str(uuid.uuid4())
        
        try:
            # Use JSON-RPC format with explicit endpoint
            payload = {
                "jsonrpc": "2.0",
                "id": str(uuid.uuid4()),
                "method": "tasks/send",
                "params": {
                    "id": task_id,
                    "message": {
                        "role": "user",
                        "parts": [{"text": math_text}]
                    }
                }
            }
            
            response = requests.post(
                f"{self.math_agent_url}/tasks/send",
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            result = response.json()
            
            # Extract response text from result
            if "result" in result and "status" in result["result"] and "message" in result["result"]["status"]:
                message = result["result"]["status"]["message"]
                if "parts" in message:
                    for part in message["parts"]:
                        if "text" in part:
                            return part["text"]
            
            return f"Error: Could not extract result from Math Agent response"
        except Exception as e:
            return f"Error: Math Agent communication failed - {str(e)}"
    
    def _solve_locally(self, math_text):
        """Solve math problem locally"""
        try:
            import re
            import math as math_lib
            
            logger.info(f"Solving math problem locally: {math_text}")
            
            # Basic arithmetic pattern
            arithmetic_match = re.search(r'(\d+(?:\.\d+)?)\s*([\+\-\*\/\^])\s*(\d+(?:\.\d+)?)', math_text)
            
            # Function pattern (sqrt, sin, cos, etc.)
            function_match = re.search(r'(sqrt|sin|cos|tan|log|exp)\((\d+(?:\.\d+)?)\)', math_text)
            
            if arithmetic_match:
                num1 = float(arithmetic_match.group(1))
                operator = arithmetic_match.group(2)
                num2 = float(arithmetic_match.group(3))
                
                if operator == '+': result = num1 + num2
                elif operator == '-': result = num1 - num2
                elif operator == '*': result = num1 * num2
                elif operator == '/': result = num1 / num2 if num2 != 0 else "Cannot divide by zero"
                elif operator == '^': result = num1 ** num2
                
                return f"(Local calculation) {num1} {operator} {num2} = {result}"
                
            elif function_match:
                func_name = function_match.group(1)
                num = float(function_match.group(2))
                
                if func_name == 'sqrt': result = math_lib.sqrt(num)
                elif func_name == 'sin': result = math_lib.sin(num)
                elif func_name == 'cos': result = math_lib.cos(num)
                elif func_name == 'tan': result = math_lib.tan(num)
                elif func_name == 'log': result = math_lib.log10(num)
                elif func_name == 'exp': result = math_lib.exp(num)
                    
                return f"(Local calculation) {func_name}({num}) = {result}"
            
            # Extract numbers as a last resort
            numbers = re.findall(r'\d+', math_text)
            if len(numbers) >= 2:
                num1, num2 = int(numbers[0]), int(numbers[1])
                return f"(Local calculation) Found numbers {num1} and {num2}. Their sum is {num1 + num2}"
            
            return f"I couldn't identify a math problem in your query: '{math_text}'"
            
        except Exception as e:
            logger.error(f"Error in local math solver: {e}")
            return f"Error solving math problem locally: {str(e)}"


class MyAgentTaskManager(InMemoryTaskManager):
    def __init__(
        self,
        ollama_host: str,
        ollama_model: typing.Union[None, str],
        math_agent_url: str = None
    ):
        super().__init__()
        if ollama_model is not None:
            self.ollama_agent = create_ollama_agent(
                ollama_base_url=ollama_host,
                ollama_model=ollama_model,
            )
        else:
            self.ollama_agent = None
        
        # Initialize the Math Agent client
        self.math_client = MathAgentClient(math_agent_url)
        
        # Log math delegation status
        if self.math_client.is_available():
            logger.info("Math delegation is enabled")
        else:
            logger.warning("Math delegation is disabled")

    def _is_math_question(self, text):
        """Detect if the text contains a math question or expression"""
        # Patterns to detect math questions
        patterns = [
            r'\d+\s*[\+\-\*\/\^\%]\s*\d+',  # Basic arithmetic operations
            r'(sqrt|sin|cos|tan|log|exp)\s*\(',  # Math functions
            r'calculate\s+',  # Words indicating calculation
            r'compute\s+',
            r'solve\s+',
            r'what is\s+\d+',  # "What is" followed by number
            r'what\'s\s+\d+',
            r'equals\s+',
            r'equal to\s+'
        ]
        
        # Check if any pattern matches
        for pattern in patterns:
            if re.search(pattern, text.lower()):
                return True
        
        return False

    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """
        This method queries or creates a task for the agent.
        The caller will receive exactly one response.
        """

        # Upsert a task stored by InMemoryTaskManager
        await self.upsert_task(request.params)

        task_id = request.params.id
        # Extract the user's message
        received_text = request.params.message.parts[0].text
        
        # Check if it's a math question
        if self._is_math_question(received_text) and self.math_client.is_available():
            logger.info(f"Detected math question: {received_text}")
            logger.info("Delegating to Math Agent")
            
            # Get the answer from the Math Agent
            math_result = self.math_client.solve_math_problem(received_text)
            
            # Format the response to acknowledge delegation
            response_text = f"I've delegated your math question to our specialized Math Agent: {math_result}"
        else:
            # Not a math question or Math Agent not available, process normally
            response_text = f"on_send_task received: {received_text}"
            if self.ollama_agent is not None:
                response_text = await run_ollama(ollama_agent=self.ollama_agent, prompt=received_text)
        
        task = await self._update_task(
            task_id=task_id,
            task_state=TaskState.COMPLETED,
            response_text=response_text,
        )
        
        # Send the response
        return SendTaskResponse(id=request.id, result=task)
    
    async def on_send_task_subscribe(
        self,
        request: SendTaskStreamingRequest
        ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        """
        This method subscribes the caller to future updates regarding a task.
        The caller will receive a response and additionally receive subscription
        updates over a session established between the client and the server
        """
        
        task_id = request.params.id
        is_new_task = task_id not in self.tasks

         # Upsert a task stored by InMemoryTaskManager
        await self.upsert_task(request.params)

        # Create a queue of work to be done for this task
        received_text = request.params.message.parts[0].text
        sse_event_queue = await self.setup_sse_consumer(task_id=task_id)
        
        # Check if it's a math question for new tasks
        if is_new_task and self._is_math_question(received_text) and self.math_client.is_available():
            logger.info(f"Detected math question (streaming): {received_text}")
            logger.info("Delegating to Math Agent")
            
            # Get the answer from the Math Agent
            math_result = self.math_client.solve_math_problem(received_text)
            
            # Format the response
            response_text = f"I've delegated your math question to our specialized Math Agent: {math_result}"
            
            # Create a completed task event
            task_update_event = TaskStatusUpdateEvent(
                id=task_id,
                status=TaskStatus(
                    state=TaskState.COMPLETED,
                    message=Message(
                        role="agent",
                        parts=[
                            {
                                "type": "text",
                                "text": response_text
                            }
                        ]
                    ),
                ),
                final=True,
            )
            await self.enqueue_events_for_sse(
                task_id=task_id,
                task_update_event=task_update_event,
            )
        elif not is_new_task and received_text == "N":
            task_update_event = TaskStatusUpdateEvent(
                id=task_id,
                status=TaskStatus(
                    state=TaskState.COMPLETED,
                    message=Message(
                        role="agent",
                        parts=[
                            {
                                "type": "text",
                                "text": "All done!"
                            }
                        ]
                    ),
                ),
                final=True,
            )
            await self.enqueue_events_for_sse(
                task_id=task_id,
                task_update_event=task_update_event,
            )
        else:
            # Start the asynchronous work for this task
            asyncio.create_task(self._stream_3_messages(request=request))
        

        # Tell the client to expect future streaming responses
        return self.dequeue_events_for_sse(
            request_id=request.id,
            task_id=task_id,
            sse_event_queue=sse_event_queue,
        )


    
    async def _update_task(
        self,
        task_id: str,
        task_state: TaskState,
        response_text: str,
    ) -> Task:
        task = self.tasks[task_id]
        agent_response_parts = [
            {
                "type": "text",
                "text": response_text,
            }
        ]
        task.status = TaskStatus (
            state=task_state,
            message=Message(
                role="agent",
                parts=agent_response_parts,
            )
        )
        task.artifacts = [
            Artifact(
                parts=agent_response_parts,
            )
        ]
        return task
    
    async def _stream_3_messages(self, request: SendTaskStreamingRequest):
        task_id = request.params.id
        received_test = request.params.message.parts[0].text

        text_messages = ["one", "two", "three"]
        for text in text_messages:
            if self.ollama_agent is not None:
                ollama_rsp = await run_ollama(ollama_agent=self.ollama_agent, prompt=f"one: {received_test}")
                message_text = f"{text}: {ollama_rsp}"
            else:
                message_text = f"{text}: {received_test}"
                
            parts = [
                {
                    "type": "text",
                    "text": message_text,
                }
            ]
            message = Message(role="agent", parts=parts)
            task_state = TaskState.WORKING
            task_status = TaskStatus(
                state=task_state,
                message=message
            )
            task_update_event = TaskStatusUpdateEvent(
                id=task_id,
                status=task_status,
                final=False,
            )
            await self.enqueue_events_for_sse(
                task_id=task_id,
                task_update_event=task_update_event,
            )
        
        ask_message = Message(
            role="agent",
            parts=[
                {
                    "type": "text",
                    "text": "Would you like more messages?(Y/N)"
                }
            ]
        )
        task_update_event = TaskStatusUpdateEvent(
            id=task_id,
            status=TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message=ask_message,
            ),
            final=True,
        )
        await self.enqueue_events_for_sse(
            task_id=task_id,
            task_update_event=task_update_event
        )