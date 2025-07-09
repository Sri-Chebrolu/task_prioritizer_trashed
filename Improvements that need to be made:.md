Improvements that need to be made:

1. When the task list is shown, the task list numbers should correspond with the task ID OR the task IDs should be updated in the DB corresponding to how they are shown in the list
 - Solution: Defined system prompt in markdown file and defined output format of task list

2. Instead of an integer value, a string value was being passed into the delete_task function
- Solution: Converted string values to integer within delete_task function

3. How does LLM know what is important to prioritize?