/**
 * Workflow automation JavaScript functionality
 */

document.addEventListener('DOMContentLoaded', function() {
    // Task filtering
    const taskFilterButtons = document.querySelectorAll('.task-filter-btn');
    if (taskFilterButtons.length > 0) {
        taskFilterButtons.forEach(button => {
            button.addEventListener('click', function() {
                // Remove active class from all buttons
                taskFilterButtons.forEach(btn => btn.classList.remove('active'));
                
                // Add active class to clicked button
                this.classList.add('active');
                
                // Get filter value
                const filter = this.getAttribute('data-filter');
                
                // Filter tasks
                const taskItems = document.querySelectorAll('.task-item');
                taskItems.forEach(item => {
                    if (filter === 'all') {
                        item.style.display = 'block';
                    } else {
                        const status = item.getAttribute('data-status');
                        item.style.display = (status === filter) ? 'block' : 'none';
                    }
                });
            });
        });
    }
    
    // Task priority sorting
    const prioritySortButton = document.getElementById('sort-by-priority');
    if (prioritySortButton) {
        prioritySortButton.addEventListener('click', function() {
            const taskList = document.querySelector('.task-list');
            const tasks = Array.from(taskList.querySelectorAll('.task-item'));
            
            // Sort tasks by priority
            tasks.sort((a, b) => {
                const priorityA = parseInt(a.getAttribute('data-priority'));
                const priorityB = parseInt(b.getAttribute('data-priority'));
                return priorityB - priorityA; // Descending order
            });
            
            // Reorder tasks in the DOM
            tasks.forEach(task => taskList.appendChild(task));
        });
    }
    
    // Due date sorting
    const dueDateSortButton = document.getElementById('sort-by-due-date');
    if (dueDateSortButton) {
        dueDateSortButton.addEventListener('click', function() {
            const taskList = document.querySelector('.task-list');
            const tasks = Array.from(taskList.querySelectorAll('.task-item'));
            
            // Sort tasks by due date
            tasks.sort((a, b) => {
                const dateA = new Date(a.getAttribute('data-due-date') || '9999-12-31');
                const dateB = new Date(b.getAttribute('data-due-date') || '9999-12-31');
                return dateA - dateB; // Ascending order
            });
            
            // Reorder tasks in the DOM
            tasks.forEach(task => taskList.appendChild(task));
        });
    }
    
    // Task completion confirmation
    const completeTaskButtons = document.querySelectorAll('.complete-task-btn');
    if (completeTaskButtons.length > 0) {
        completeTaskButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to mark this task as completed?')) {
                    e.preventDefault();
                }
            });
        });
    }
    
    // Workflow transition confirmation
    const transitionButtons = document.querySelectorAll('.transition-btn');
    if (transitionButtons.length > 0) {
        transitionButtons.forEach(button => {
            button.addEventListener('click', function(e) {
                if (!confirm('Are you sure you want to transition the workflow?')) {
                    e.preventDefault();
                }
            });
        });
    }
    
    // Task due date highlighting
    const taskDueDates = document.querySelectorAll('.task-due-date');
    if (taskDueDates.length > 0) {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        
        taskDueDates.forEach(element => {
            const dueDate = new Date(element.getAttribute('data-date'));
            dueDate.setHours(0, 0, 0, 0);
            
            const diffTime = dueDate - today;
            const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
            
            if (diffDays < 0) {
                // Overdue
                element.classList.add('text-danger', 'fw-bold');
                element.innerHTML = `<i class="fas fa-exclamation-circle me-1"></i>${element.innerHTML} (Overdue)`;
            } else if (diffDays === 0) {
                // Due today
                element.classList.add('text-warning', 'fw-bold');
                element.innerHTML = `<i class="fas fa-clock me-1"></i>${element.innerHTML} (Today)`;
            } else if (diffDays <= 2) {
                // Due soon
                element.classList.add('text-primary');
                element.innerHTML = `<i class="fas fa-clock me-1"></i>${element.innerHTML} (Soon)`;
            }
        });
    }
});
