import re
import math
import logging
from typing import Dict, Any, Optional, AsyncIterable

from google_a2a.common.server.task_manager import InMemoryTaskManager
from google_a2a.common.types import (
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

logger = logging.getLogger(__name__)

class MathAgentTaskManager(InMemoryTaskManager):
    def __init__(self):
        super().__init__()
    
    async def on_send_task(self, request: SendTaskRequest) -> SendTaskResponse:
        """Handle math calculation requests"""
        # Store the task in memory
        await self.upsert_task(request.params)
        
        task_id = request.params.id
        
        # Extract the message text from the request
        message_text = request.params.message.parts[0].text
        logger.info(f"Math Agent received: {message_text}")
        
        # Process the math expression
        result = self._process_math_expression(message_text)
        
        # Update the task with the result
        task = await self._update_task(
            task_id=task_id,
            task_state=TaskState.COMPLETED,
            response_text=result,
        )
        
        # Return the response
        return SendTaskResponse(id=request.id, result=task)
    
    async def on_send_task_subscribe(
        self,
        request: SendTaskStreamingRequest
    ) -> AsyncIterable[SendTaskStreamingResponse] | JSONRPCResponse:
        pass
    
    def _process_math_expression(self, text: str) -> str:
        """Process mathematical expressions in the text"""
        try:
            # Try to extract a math expression using patterns
            # Pattern for basic arithmetic: digits and operators
            basic_math_pattern = r'(\d+\s*[\+\-\*\/\^\%]\s*\d+(?:\s*[\+\-\*\/\^\%]\s*\d+)*)'
            # Pattern for functions like sqrt, sin, cos, etc.
            function_pattern = r'(sqrt|sin|cos|tan|log|exp)\s*\(\s*\d+(?:\.\d+)?\s*\)'
            
            # Check for basic arithmetic
            basic_match = re.search(basic_math_pattern, text)
            # Check for functions
            function_match = re.search(function_pattern, text)
            
            if basic_match:
                expression = basic_match.group(1)
                # Replace ^ with ** for Python's power operator
                expression = expression.replace('^', '**')
                result = eval(expression)
                return f"The result of {expression.replace('**', '^')} is {result}"
            elif function_match:
                full_expr = function_match.group(0)
                func_name = function_match.group(1)
                
                # Extract the number inside the parentheses
                num_match = re.search(r'\(\s*(\d+(?:\.\d+)?)\s*\)', full_expr)
                if num_match:
                    num = float(num_match.group(1))
                    
                    if func_name == 'sqrt':
                        result = math.sqrt(num)
                    elif func_name == 'sin':
                        result = math.sin(num)
                    elif func_name == 'cos':
                        result = math.cos(num)
                    elif func_name == 'tan':
                        result = math.tan(num)
                    elif func_name == 'log':
                        result = math.log10(num)
                    elif func_name == 'exp':
                        result = math.exp(num)
                    else:
                        return f"I don't know how to calculate {full_expr}"
                    
                    return f"The result of {full_expr} is {result}"
            
            # If no math expression is found, try to extract numbers and do a simple addition
            numbers = re.findall(r'\d+', text)
            if len(numbers) >= 2:
                num1 = int(numbers[0])
                num2 = int(numbers[1])
                result = num1 + num2
                return f"I found numbers {num1} and {num2}, their sum is {result}"
            
            return "I couldn't find a valid mathematical expression to calculate."
        
        except Exception as e:
            logger.error(f"Error processing math expression: {str(e)}")
            return f"I encountered an error while calculating: {str(e)}"
    
    async def _update_task(
        self,
        task_id: str,
        task_state: TaskState,
        response_text: str,
    ) -> Task:
        """Update a task with a response"""
        task = self.tasks[task_id]
        agent_response_parts = [
            {
                "type": "text",
                "text": response_text,
            }
        ]
        task.status = TaskStatus(
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