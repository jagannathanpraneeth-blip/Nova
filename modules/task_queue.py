"""
Task Queue Manager for parallel task execution.
Allows Nova to handle multiple commands simultaneously.
"""

import threading
import queue
import logging
from typing import Dict, Any, Callable
import time

class TaskQueueManager:
    """
    Manages parallel execution of tasks so Nova can multitask.
    Long-running tasks execute in background without blocking voice listening.
    """
    
    def __init__(self):
        self.logger = logging.getLogger('TaskQueue')
        self.task_queue = queue.Queue()
        self.active_tasks = {}
        self.task_counter = 0
        self.running = True
        
        # Start worker threads for parallel execution
        self.num_workers = 3  # Can handle 3 tasks simultaneously
        self.workers = []
        
        for i in range(self.num_workers):
            worker = threading.Thread(target=self._worker, daemon=True, name=f"Worker-{i+1}")
            worker.start()
            self.workers.append(worker)
            
        self.logger.info(f"TaskQueueManager started with {self.num_workers} workers")
    
    def _worker(self):
        """Worker thread that processes tasks from the queue"""
        while self.running:
            try:
                # Get task from queue (blocks until available)
                task_id, task_func, task_args, task_kwargs = self.task_queue.get(timeout=1)
                
                self.logger.info(f"Worker {threading.current_thread().name} executing task {task_id}")
                
                try:
                    # Execute the task
                    result = task_func(*task_args, **task_kwargs)
                    self.active_tasks[task_id] = {
                        'status': 'completed',
                        'result': result,
                        'error': None
                    }
                    self.logger.info(f"Task {task_id} completed successfully")
                    
                except Exception as e:
                    self.logger.error(f"Task {task_id} failed: {e}", exc_info=True)
                    self.active_tasks[task_id] = {
                        'status': 'failed',
                        'result': None,
                        'error': str(e)
                    }
                
                finally:
                    self.task_queue.task_done()
                    
            except queue.Empty:
                continue
            except Exception as e:
                self.logger.error(f"Worker error: {e}", exc_info=True)
    
    def add_task(self, task_func: Callable, *args, **kwargs) -> int:
        """
        Add a task to the queue for parallel execution.
        
        Args:
            task_func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            task_id: Unique ID for tracking this task
        """
        self.task_counter += 1
        task_id = self.task_counter
        
        self.active_tasks[task_id] = {
            'status': 'queued',
            'result': None,
            'error': None
        }
        
        self.task_queue.put((task_id, task_func, args, kwargs))
        self.logger.info(f"Task {task_id} queued: {task_func.__name__}")
        
        return task_id
    
    def get_task_status(self, task_id: int) -> Dict[str, Any]:
        """Get the status of a task"""
        return self.active_tasks.get(task_id, {'status': 'unknown', 'result': None, 'error': 'Task not found'})
    
    def wait_for_task(self, task_id: int, timeout: float = None) -> Dict[str, Any]:
        """
        Wait for a task to complete and return its result.
        
        Args:
            task_id: ID of the task to wait for
            timeout: Maximum time to wait in seconds
            
        Returns:
            Task result dictionary
        """
        start_time = time.time()
        
        while True:
            status = self.get_task_status(task_id)
            
            if status['status'] in ['completed', 'failed']:
                return status
            
            if timeout and (time.time() - start_time) > timeout:
                self.logger.warning(f"Task {task_id} wait timeout after {timeout}s")
                return {'status': 'timeout', 'result': None, 'error': 'Timeout waiting for task'}
            
            time.sleep(0.1)
    
    def is_task_running(self, task_id: int) -> bool:
        """Check if a task is currently running"""
        status = self.get_task_status(task_id)
        return status['status'] not in ['completed', 'failed', 'unknown']
    
    def get_queue_size(self) -> int:
        """Get number of tasks waiting in queue"""
        return self.task_queue.qsize()
    
    def get_active_count(self) -> int:
        """Get number of tasks currently being processed"""
        return sum(1 for t in self.active_tasks.values() if t['status'] == 'queued')
    
    def stop(self):
        """Stop the task queue manager and all workers"""
        self.logger.info("Stopping TaskQueueManager...")
        self.running = False
        
        # Wait for all workers to finish
        for worker in self.workers:
            worker.join(timeout=2)
        
        self.logger.info("TaskQueueManager stopped")

# Global task queue instance
_task_queue = None

def get_task_queue() -> TaskQueueManager:
    """Get or create the global task queue instance"""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueueManager()
    return _task_queue

def execute_async(func: Callable, *args, **kwargs) -> int:
    """
    Execute a function asynchronously in the background.
    
    Returns:
        task_id for tracking the task
    """
    task_queue = get_task_queue()
    return task_queue.add_task(func, *args, **kwargs)

def execute_sync(func: Callable, *args, **kwargs) -> Any:
    """
    Execute a function synchronously (blocking).
    
    Returns:
        The result of the function
    """
    return func(*args, **kwargs)
