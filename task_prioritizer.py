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
                
    def list_task(self):
        """
        Display all tasks in a formatted list
        """
        if not self.tasks:
            print("\nNo tasks in your list!")
            return
        
        print("\nYour Task List:")
        print("-" * 50)
        for task in self.tasks:
            print(f"{task['id']}. {task['text']}: {task['status']}")
        print("-" * 50)

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
        if function_name == 'load_task':
            return {"result": "Tasks loaded", "tasks": self.task_manager.tasks}
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
        elif function_name == 'list_task':
            self.task_manager.list_task()
            return {"result": "Task list displayed", "tasks": self.task_manager.tasks}
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
You are a task management assistant.

[Your role is to]:
1. Read the user's input and determine what action to take on the task list.
2. Utilize the defined toolset to take action.
3. Show the user the updated task list.

[Important Instructions]:
1. DO NOT explain your reasoning or show steps of your thinking process.
2. DO NOT list numbered steps of what you plan to do.
3. Interact with the user naturally, asking only necessary confirmation questions.
4. When confirming actions, ask directly (e.g., "Should I add 'Email Sarah' to your task list?").
5. After confirmation, execute the action and show results without explaining the process.
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

        model='mistral'
        
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
            # Add the assistant's response to conversation
            messages.append({
                'role': 'assistant',
                'content': response.message.content,
                'tool_calls': response.message.tool_calls
            })
            
            # Execute each tool call
            for tool_call in response.message.tool_calls:
                tool_result = self.execute_tool_call(tool_call)
                
                # Add tool result to conversation
                messages.append({
                    'role': 'tool',
                    'content': json.dumps(tool_result),
                    'tool_call_id': tool_call['id']
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
            "name": "load_task",
            "description": "Load the task list",
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
    },
    {
        "type": "function",
        "function": {
            "name": "list_task",
            "description": "Print the entire task list",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": []
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