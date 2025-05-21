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

    def update_task(self, task_id):
        """
        Update task status 
        """
        # check if task exists in list

        for task in self.tasks:
            if task["id"] == task_id:

                print('Task found. Enter a number to update the task status: ')
                print('1. Completed')
                print('2. In progress')

                status_update = input().strip().lower()

                # update task status to complete
                if status_update == "1":
                    task["status"] = 'Completed'
                    task["status_update_time"] = datetime.now().isoformat()

                elif status_update == "2":
                    task["status"] = 'In progress'
                    task["status_update_time"] = datetime.now().isoformat()

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

def get_user_task():
    """
    Get a task from the user via text input.
    Returns the task as a string.
    """
    print("Enter your task. Enter 'exit' or 'quit' to exit):")
    task = input().strip()
    return task

def main():
    task_manager = TaskManager()
    
    while True:
        print("\nOptions:")
        print("1. Add task")
        print("2. Show tasks")
        print("3. Update task status")
        print("4. Quit or just enter quit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            task = get_user_task()
            if task.lower() in ['quit', 'exit']:
                break
            new_task = task_manager.add_task(task)
            print(f"Added task: {new_task['text']}")
            
        elif choice == "2":
            task_manager.list_tasks()
            
        elif choice == "3":
            task_manager.list_tasks()  # Show tasks first

            print('Enter task ID to update task status')
        
            task_id = int(input())
            
            task_manager.update_task(task_id)
            
        elif choice in ["4", "quit"]:
            break
        
        # TODO: Add LLM processing here
        # TODO: Add task prioritization here
        # TODO: Add calendar integration here

if __name__ == "__main__":
    main()

