#Problem: 
# Users have to keep writing down or typing tasks, create reminders, or execute menial tasks which ironically
# takes away from time of actually doing things. 
# Organizing and prioritizing tasks takes away from execution time. 

# Problem statement:
# Users don't have a single input ability to organize and prioritize tasks, 
# decreasing the amount of time available for execution.

# What is the code supposed to do:
# 1. Take user input in the form of text, audio
# 2. Parses task from user input and passess to LLM
# 3. LLM reads current task list and inserts new tasks into list
# 4. LLM prioritizes the task based on:
#   - P0: user preference
#   - P0: the other tasks on the list
#   - P1: the general prioritization preferences user has
# 4.1 LLM shows user task list and asks if okay?
# 5. LLM makes an API call to the users calendar of choice
#   - Authentication required if using gmail or outlook?
# 6. LLM notifies user of new event added to calendar
#   - shows what was added to calendar
# 7. LLM asks user for permission to execute some tasks in background
#   - what are some buckets for tasks?
# 8. LLM updates task lists as tasks are completed
#   - shows end of day summary and tomorrow's tasks

from ollama import chat
from ollama import ChatResponse
import json
from datetime import datetime

# response: ChatResponse = chat(model='mistral', messages=[
#   {
#     'role': 'user',
#     'content': 'Why is the sky blue?',
#   },
# ])
# print(response['message']['content'])
# # or access fields directly from the response object
# print(response.message.content)

class TaskManager:
    def __init__(self, filename="tasks.json"):
        self.filename = filename
        self.tasks = self.load_tasks()
    
    def load_tasks(self):
        try:
            with open(self.filename, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return []
    
    def save_tasks(self):
        with open(self.filename, 'w') as f:
            json.dump(self.tasks, f, indent=2)
    
    # How is task_text extracted from the user_input?
    def add_task(self, task_text):
        task = {
            "id": len(self.tasks) + 1,
            "text": task_text,
            "created_at": datetime.now().isoformat(),
            "status": "Incomplete",
            "status_update_time": datetime.now().isoformat()
        }
        self.tasks.append(task)
        self.save_tasks()
        return task
    
    def delete_task(self, task_id):
        """
        Delete task
        """

        for i, task in enumerate(self.tasks):
            if task["id"] == task_id:
                del self.tasks[i]
                self.save_tasks()
                print(f"Task {task_id} deleted successfully!")
                return True
        print(f"Task {task_id} not found!")
        return False

    def update_task(self, task_id):
        """
        Update task status 
        """
        # check if task exists in list

        for task in self.tasks:
            if task["id"] == task_id:
                
                print('Task updated')
                self.save_tasks()
                return task
            
            else:
                print('Please enter a valid task ID number')

        return False
                

# user enters prompt into chatbox
# LLM interprets user query and identifies what action needs to be taken
# LLM makes function call asssociated with the action that needs to be taken

class LLM:
    
    # create instance of tool set agent can use to interact with the to do list
    def __init__(self, tools, task_manager):
        self.tools = tools
        self.task_manager = task_manager

    def execute_tool_call(self, tool_call):
        """
        Execute a tool call and return the result
        """
        function_name = tool_call['function']['name']
        arguments = tool_call['function'].get('arguments', {})
        
        # Map function names to TaskManager methods
        if function_name == 'list_task':
            # Always load fresh data from file and return it
            tasks = self.task_manager.load_tasks()
            return {"tasks": tasks}
        elif function_name == 'save_task':
            self.task_manager.save_tasks()
            return {"result": "Tasks saved successfully"}
        elif function_name == 'add_task':
            task = self.task_manager.add_task(arguments['task_text'])
            return {"result": "Task added successfully", "task": task}
        elif function_name == 'delete_task':
            success = self.task_manager.delete_task(arguments['task_id'])
            return {"result": "Task deleted successfully" if success else "Task not found"}
        elif function_name == 'update_task':
            task = self.task_manager.update_task(arguments['task_id'])
            return {"result": "Task updated successfully" if task else "Task not found"}
        else:
            return {"error": f"Unknown function: {function_name}"}

    def process_command(self, user_input, conversation_history=None):
        """
        Process user input and determine what action to take
        """
        # Initialize or use existing conversation history
        if conversation_history is None:
            # Initial conversation with LLM
            messages = [
                {
                    'role': 'system',
                    'content': """
You are a task management assistant with access to specific tools.

MANDATORY: You MUST use the provided tools for every task operation. 

[Your role is to]:
1. Read the user's input and determine what action to take.
2. Utilize the defined toolset to take action.
3. Show the user the updated task list.

[Tool Usage Guidelines]:
- You can call the same tool multiple times in a single response to execute the same action across multiple tasks.

[Important Instructions]:
1. DO NOT explain your reasoning or show steps of your thinking process.
2. DO NOT list numbered steps of what you plan to do.
3. Interact with the user naturally, asking only necessary confirmation questions.
4. When confirming actions, ask directly (e.g., "Should I add 'Email Sarah' to your task list?").
5. After confirmation, execute the action and show results without explaining the process.
6. Save the task list after each action.
"""
                }
            ]
        else:
            # Use existing conversation history
            messages = conversation_history
        
        # Add the latest user input to messages
        messages.append({
            'role': 'user',
            'content': user_input
        })

        model = 'llama3.2:3b'
        
        # In the process_command method, right before the chat call:
        print("DEBUG: Number of tools being passed:", len(self.tools))
        print("DEBUG: Tool names:", [tool['function']['name'] for tool in self.tools])

        # Get initial response from LLM
        response = chat(
            model=model,
            stream=False,
            messages=messages,
            tools=self.tools
        )

        print('user input passed to LLM API')

        # Check if the LLM wants to use tools
        if hasattr(response.message, 'tool_calls') and response.message.tool_calls:
            print(f"DEBUG: LLM wants to use {len(response.message.tool_calls)} tools")
            for tool_call in response.message.tool_calls:
                print(f"DEBUG: Calling tool: {tool_call['function']['name']}")
            # Add the assistant's response to conversation
            messages.append({
                'role': 'assistant',
                'content': response.message.content,
                'tool_calls': response.message.tool_calls
            })
            
            # Execute each tool call
            for tool_call in response.message.tool_calls:
                tool_result = self.execute_tool_call(tool_call)
                
                # Debug: Print the tool_call structure to see what's available
                print("DEBUG: tool_call structure:", tool_call)
                
                # Add tool result to conversation
                messages.append({
                    'role': 'tool',
                    'content': json.dumps(tool_result)
                    # Temporarily remove tool_call_id until we figure out the structure
                })
            
            # Get final response from LLM after tool execution
            final_response = chat(
                model=model,
                stream=False,
                messages=messages,
                tools=self.tools
            )
            
            # Add the final response to conversation history
            messages.append({
                'role': 'assistant',
                'content': final_response.message.content
            })
            
            print(final_response.message.content)
        else:
            print("DEBUG: No tool calls made by LLM")
            print(response.model)
            # No tools needed, just add the response to conversation history
            messages.append({
                'role': 'assistant',
                'content': response.message.content
            })
            print(response.message.content)
        
        # Return the updated conversation history
        return messages

# create tool set
tools = [
    {
        "type": "function",
        "function": {
            "name": "list_task",
            "description": "Load and display the user's current task list from storage. Use this whenever the user wants to see, show, list, display, or view their tasks.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "save_task",
            "description": "Save the task list",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_task",
            "description": "Add tasks to the task list",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_text": {
                        "type": "string",
                        "description": "String description of what the task is"
                    }
                },
                "required": ["task_text"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_task",
            "description": "Delete task from the task list",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "Task ID number assigned to each task"
                    }
                },
                "required": ["task_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_task",
            "description": "Update task from the task list",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "integer",
                        "description": "Task ID number assigned to each task"
                    }
                },
                "required": ["task_id"]
            }
        }
    }
]

def main():
    tm = TaskManager()
    llm = LLM(tools, tm)
    
    # Initialize conversation history
    conversation_history = None
    
    while True:
        user_input = input("What would you like to do with your task list today? (type 'exit' to quit): ")
        if user_input.lower() == 'exit':
            break
        
        # Process command and get updated conversation history
        conversation_history = llm.process_command(user_input, conversation_history)

if __name__ == "__main__":
    main()