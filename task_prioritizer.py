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
                
    def list_tasks(self):
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
    
    def process_command(self, user_input):
        """
        Process user input and determine what action to take
        """
        # Passing user input to LLM
        response_stream = chat(
            model='mistral',
            stream=True,
            messages=[
                {
                    'role': 'system',
                    'content': """You are a task management assistant. Your role is to:
                    1. Analyze user input
                    2. Determine the appropriate action
                    3. Return the action to take"""
                },
                {
                    'role': 'user',
                    'content': user_input
                }
            ]
        )

        # with streaming, API response is a generator object that lazily produces values
        # In order to access the content of the response, we need to iterate over the generator object
        
        for chunks in response_stream:
            print(chunks.message.content)

def main():
    llm = LLM()
    llm.process_command("Add a task to my task list")

if __name__ == "__main__":
    main()