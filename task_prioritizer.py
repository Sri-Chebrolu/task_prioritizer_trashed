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
    def add_task(self, task_text, category=None, priority=None):
        # Generate next available ID
        existing_ids = [task["id"] for task in self.tasks] if self.tasks else []
        next_id = max(existing_ids) + 1 if existing_ids else 1
        
        task = {
            "id": next_id,
            "text": task_text,
            "category": category,
            "priority": priority,
            "status": "Incomplete",
            "created_at": datetime.now().isoformat(),
            "status_update_time": datetime.now().isoformat()
        }
        self.tasks.append(task)
        self.save_tasks()
        return task
    
    def delete_task(self, task_id):
        """
        Delete task - simpler version
        """
        # Convert to int if needed
        task_id = int(task_id) if isinstance(task_id, str) else task_id
        
        # Count tasks before deletion
        original_count = len(self.tasks)
        
        # Filter out the task with matching ID
        self.tasks = [task for task in self.tasks if task["id"] != task_id]
        
        # Check if anything was actually deleted
        if len(self.tasks) < original_count:
            self.save_tasks()
            print(f"Task {task_id} deleted successfully!")
            return True
        else:
            print(f"Task {task_id} not found!")
            return False

    def update_task(self, task_id, **updates):
        """
        Update task with any provided fields
        """
        task_id = int(task_id) if isinstance(task_id, str) else task_id
        
        for task in self.tasks:
            if task["id"] == task_id:
                # Update any provided fields
                for key, value in updates.items():
                    if key in task:
                        task[key] = value
                task["status_update_time"] = datetime.now().isoformat()
                self.save_tasks()
                print(f'Task {task_id} updated')
                return task
        
        print(f'Task {task_id} not found')
        return False
                

# user enters prompt into chatbox
# LLM interprets user query and identifies what action needs to be taken
# LLM makes function call asssociated with the action that needs to be taken

class LLM:
    
    # create instance of tool set agent can use to interact with the to do list
    def __init__(self, tools, task_manager):
        self.tools = tools
        self.task_manager = task_manager
        
        # Load system prompt once at initialization
        try:
            with open('system_prompt.md', 'r') as f:
                self.system_prompt = f.read()
        except FileNotFoundError:
            print('The product was unable to load the prompt')
        
    def execute_tool_call(self, tool_call):
        """
        Execute a tool call and return the result
        """
        function_name = tool_call['function']['name']
        arguments = tool_call['function'].get('arguments', {})
        
        # Add debug prints to see what's being passed
        print(f"DEBUG: Function name: {function_name}")
        print(f"DEBUG: Arguments received: {arguments}")
        print(f"DEBUG: Arguments type: {type(arguments)}")
        
        # Map function names to TaskManager methods
        if function_name == 'list_task':
            tasks = self.task_manager.load_tasks()
            print(f"DEBUG: Raw tasks being sent to LLM: {tasks}")
            return {"tasks": tasks}
        elif function_name == 'save_task':
            self.task_manager.save_tasks()
            return {"result": "Tasks saved successfully"}
        elif function_name == 'add_task':
            task_text = arguments['task_text']
            category = arguments['category']
            priority = arguments['priority']      
            task = self.task_manager.add_task(task_text, category=category, priority=priority)
            return {"result": "Task added successfully", "task": task}
        elif function_name == 'delete_task':
            print(f"DEBUG: task_id value: {arguments['task_id']}")
            print(f"DEBUG: task_id type: {type(arguments['task_id'])}")
            success = self.task_manager.delete_task(arguments['task_id'])
            return {"result": "Task deleted successfully" if success else "Task not found"}
        elif function_name == 'update_task':
            task_id = arguments['task_id']
            updates = {k: v for k, v in arguments.items() if k != 'task_id'}
            task = self.task_manager.update_task(task_id, **updates)
            return {"result": "Task updated successfully" if task else "Task not found"}
        else:
            return {"error": f"Unknown function: {function_name}"}

    def process_command(self, user_input, conversation_history=None):
        """
        Process user input and determine what action to take
        """
        if conversation_history is None:
            messages = [
                {
                    'role': 'system',
                    'content': self.system_prompt  # Use the loaded prompt
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
            "description": "Add tasks to the task list with priority and category",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_text": {
                        "type": "string",
                        "description": "String description of what the task is"
                    },
                    "category": {
                        "type": "string",
                        "description": "Task category (e.g., Health, Work, Personal, etc.)"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Task priority: High, Medium, or Low"
                    }
                },
                "required": ["task_text", "category", "priority"]
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
    # # Test block only
    # print("=== Testing load_tasks function ===")
    # tm = TaskManager()
    # print(f"Loaded tasks: {tm.tasks}")
    # print(f"Number of tasks: {len(tm.tasks)}")
    # for i, task in enumerate(tm.tasks):
    #     print(f"Task {i+1}: {task}")
    
    # Comment out main() to only run the test
    main()