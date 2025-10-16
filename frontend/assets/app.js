class TaskPrioritizer {
  constructor() {
    this.tasks = JSON.parse(localStorage.getItem('tasks')) || [];
    this.nextId = Math.max(0, ...this.tasks.map(t => t.id)) + 1;
    this.init();
  }

  init() {
    this.bindEvents();
    this.renderTasks();
  }

  bindEvents() {
    document.getElementById('add-task-btn').addEventListener('click', () => {
      this.showTaskInput();
    });

    document.getElementById('save-task').addEventListener('click', () => {
      this.saveTask();
    });

    document.getElementById('cancel-task').addEventListener('click', () => {
      this.hideTaskInput();
    });

    // Add task on Enter key
    document.getElementById('task-title').addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        this.saveTask();
      }
    });
  }

  showTaskInput() {
    document.getElementById('task-input').style.display = 'block';
    document.getElementById('task-title').focus();
    document.getElementById('task-title').value = '';
    document.getElementById('task-priority').value = '5';
  }

  hideTaskInput() {
    document.getElementById('task-input').style.display = 'none';
  }

  saveTask() {
    const title = document.getElementById('task-title').value.trim();
    const priority = parseInt(document.getElementById('task-priority').value);

    if (!title) {
      alert('Please enter a task title');
      return;
    }

    const task = {
      id: this.nextId++,
      title: title,
      priority: priority,
      completed: false,
      createdAt: new Date().toISOString()
    };

    this.tasks.push(task);
    this.saveToStorage();
    this.renderTasks();
    this.hideTaskInput();
  }

  toggleComplete(taskId) {
    const task = this.tasks.find(t => t.id === taskId);
    if (task) {
      task.completed = !task.completed;
      this.saveToStorage();
      this.renderTasks();
    }
  }

  deleteTask(taskId) {
    if (confirm('Are you sure you want to delete this task?')) {
      this.tasks = this.tasks.filter(t => t.id !== taskId);
      this.saveToStorage();
      this.renderTasks();
    }
  }

  getPriorityClass(priority) {
    if (priority >= 8) return 'priority-urgent';
    if (priority >= 5) return 'priority-high';
    if (priority >= 3) return 'priority-medium';
    return 'priority-low';
  }

  getPriorityLabel(priority) {
    if (priority >= 8) return 'Urgent';
    if (priority >= 5) return 'High';
    if (priority >= 3) return 'Medium';
    return 'Low';
  }

  renderTasks() {
    const taskList = document.getElementById('task-list');
    
    if (this.tasks.length === 0) {
      taskList.innerHTML = '<div class="empty-state">No tasks yet. Add your first task above!</div>';
      return;
    }

    // Sort tasks by priority (highest first), then by creation date
    const sortedTasks = [...this.tasks].sort((a, b) => {
      if (a.completed !== b.completed) {
        return a.completed ? 1 : -1;
      }
      return b.priority - a.priority;
    });

    taskList.innerHTML = sortedTasks.map(task => `
      <div class="task-item ${task.completed ? 'task-completed' : ''}">
        <div class="task-content">
          <div class="task-title">${this.escapeHtml(task.title)}</div>
          <span class="task-priority ${this.getPriorityClass(task.priority)}">
            ${this.getPriorityLabel(task.priority)} (${task.priority})
          </span>
        </div>
        <div class="task-actions">
          <button class="btn-small btn-complete" onclick="app.toggleComplete(${task.id})">
            ${task.completed ? 'Undo' : 'Complete'}
          </button>
          <button class="btn-small btn-delete" onclick="app.deleteTask(${task.id})">
            Delete
          </button>
        </div>
      </div>
    `).join('');
  }

  saveToStorage() {
    localStorage.setItem('tasks', JSON.stringify(this.tasks));
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
}

// Initialize the app
const app = new TaskPrioritizer();