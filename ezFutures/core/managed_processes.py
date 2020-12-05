from multiprocessing import Process, Manager, sharedctypes
from collections import defaultdict
import time

from ..utils import printProgressBar
from ..utils import Timeout


class WorkerProcess(Process):
    
    def __init__(self, shared_results_dict, shared_status_dict, shared_error_dict, task, timeout):
        super(WorkerProcess, self).__init__()
    
        self.shared_results_dict = shared_results_dict
        self.shared_status_dict = shared_status_dict
        self.shared_error_dict = shared_error_dict
        self.task = task
        self.timeout = timeout
        
    def run(self):
        """
        We need a way to surface the failure reasons.
        In case of actual failed task.
        """
        
        task_idx, func, args, kwargs = self.task
        
        try:

            with Timeout(seconds=self.timeout):

                result = func(*args, **kwargs)
                self.shared_error_dict[task_idx] = None
                self.shared_status_dict[task_idx] = 'success'
                self.shared_results_dict[task_idx] = result

        except Exception as e:

            self.shared_error_dict[task_idx] = str(e)
            self.shared_status_dict[task_idx] = 'failure'
            self.shared_results_dict[task_idx] = None 


class ManagedProcesses():
    
    def __init__(self, n_procs=4, verbose=False, show_progress=True, timeout=60*60, n_retries=3, *args, **kwargs):
        
        self.task_idx = 0
        
        self.tasks = []
        self.pending_tasks = []
        
        self.failed_tasks_idx = []
        self.successful_tasks_idx = []
        self.task_idx_attempt_dict = defaultdict(int)
        
        manager = Manager()
        self.shared_results_dict = manager.dict()
        self.shared_status_dict = manager.dict()
        self.shared_error_dict = manager.dict()
        
        self.subprocs = dict()
        self.subprocs_start_times = dict()
        
        self.n_procs = n_procs
        self.verbose = verbose
        self.show_progress = show_progress
        self.timeout = timeout
        self.n_retries = n_retries
        
        self.scattered_vars = dict()
        
    def globalize(self, local_var, global_name):
        
        self.scattered_vars[global_name] = local_var
        
    def submit(self, func, *args, **kwargs):
        
        if len(self.scattered_vars) > 0:
            func.__globals__.update(self.scattered_vars)
        
        task_idx = int(self.task_idx)
        self.tasks.append([task_idx, func, args, kwargs])
        
        self.task_idx += 1
        
    def execute_task(self, task):

        timeout = int(self.timeout)
        
        subproc = WorkerProcess(
            self.shared_results_dict, 
            self.shared_status_dict, 
            self.shared_error_dict,
            task,
            timeout)

        subproc.daemon = True
        subproc.start()
        return subproc

    def results(self):
        
        self.tasks = self.tasks[::-1]
        num_tasks = len(self.tasks)
        
        if(self.show_progress):
            printProgressBar(0, num_tasks)
        
        while(len(self.pending_tasks) > 0 or len(self.tasks) > 0):

            # if we can run more subprocs and if there are tasks remaining
            # run a task in subproc
            while(len(self.subprocs) < self.n_procs and len(self.tasks) > 0):

                task = self.tasks.pop()
                task_idx = task[0]
                
                self.pending_tasks.append(task)
                
                subproc = self.execute_task(task)
                self.task_idx_attempt_dict[task_idx] += 1

                self.subprocs[task_idx] = subproc
                self.subprocs_start_times[task_idx] = time.time()
                
            # these are not just pending but completed tasks, whether failed or succeeded
            if(len(self.shared_status_dict.keys()) > 0):

                for tried_task_idx in self.shared_status_dict.keys():

                    if self.shared_status_dict[tried_task_idx] == 'success':
        
                        if self.verbose:
                            print('Task execution successful: {}\n'.format(tried_task_idx))
                        self.successful_tasks_idx.append(tried_task_idx)
                        
                    elif self.shared_status_dict[tried_task_idx] == 'failure':

                        if self.verbose:
                            print('Task execution failed: {}\n'.format(tried_task_idx))

                        # we need to push these back to tasks
                        # since we need to start the process again, 
                        # no need for any wait time 
                        # (there is nothing to wait for! it failed!)
                        self.failed_tasks_idx.append(tried_task_idx)
                        
                    self.shared_status_dict.pop(tried_task_idx)
                        
            if(len(self.pending_tasks) > 0):
                
                for _ in range(len(self.pending_tasks)):
                    
                    pending_task = self.pending_tasks.pop()
                    pending_task_idx = pending_task[0]
                    
                    current_time = time.time()
                    start_time = self.subprocs_start_times[pending_task_idx]
                    passed_time = current_time - start_time
                    
                    if self.verbose:
                        print('Looking at pending task {}'.format(pending_task))
                    
                    if pending_task_idx in self.failed_tasks_idx:
                        
                        fail_count = self.task_idx_attempt_dict[task_idx]
                        
                        if fail_count < self.n_retries:
                            
                            if self.verbose:
                                print('    pending --> tasks: {}'.format(pending_task_idx))
                                print('    failed {} times'.format(fail_count))
                                
                            # don't append since that will try to do this again right away
                            self.tasks.insert(0, pending_task)
                            self.failed_tasks_idx.remove(pending_task_idx)  # give it another chance
                                
                        else:
                            
                            if self.verbose:
                                print('    pending --> failed tasks: {}'.format(pending_task_idx))
                                print('    * reached MAX_ATTEMPT\n')
                                
                            # just leave the failed idx alone
                            
                    elif pending_task_idx in self.successful_tasks_idx:

                        if self.verbose:
                            print('    pending --> successful tasks: {}\n'.format(pending_task_idx))
                    
                    # premature and sudden death of Process
                    elif pending_task_idx not in self.subprocs:
                        
                        if self.verbose:
                            print('    Process terminated abruptly while task {} pending'.format(pending_task_idx))
                            print('    pending --> tasks')
                        
                        fail_count = self.task_idx_attempt_dict[task_idx]
                        
                        if fail_count < self.n_retries:
                            
                            self.tasks.insert(0, pending_task)
                            
                        else:
                            
                            self.failed_tasks_idx.append(pending_task_idx)
                    
                    # timeout 
                    elif passed_time > self.timeout:
                        
                        self.subprocs[pending_task_idx].terminate()
                        
                        if self.verbose:
                            print('    pending task {} --> timed out'.format(pending_task_idx))
                    
                        fail_count = self.task_idx_attempt_dict[task_idx]
                        
                        if fail_count < self.n_retries:
                            
                            self.tasks.insert(0, pending_task)
                            
                        else:
                            
                            self.failed_tasks_idx.append(pending_task_idx)
                        
                    else:
                        
                        if self.verbose:
                            print('    nothing to update\n')

                        self.pending_tasks.insert(0, pending_task)
                        
            if(self.show_progress):

                cur_len = int(len(self.successful_tasks_idx) + len(self.failed_tasks_idx))  
                printProgressBar(cur_len, num_tasks)
            
            # subproc dies only after updating shared dicts
            # by the time the subprocs list updated and IF one drops
            # that means the shared dicts HAVE to have been updated
            self.subprocs = {k: v for k, v in self.subprocs.items() if v.is_alive()}

            if self.verbose:
                print('SUBPROC STATUS')
                print('number of outstanding tasks: {} ( {} )'.format(len(self.tasks), self.tasks))
                print('number of running procs: {}'.format(len(self.subprocs))); print()

            # if all procs are busy, there is no gain from trying to 
            # assign work to them at the moment
            if(len(self.subprocs) == self.n_procs):
                time.sleep(0.1)

            # if number of tasks is 0, there is no gain from trying to
            # assign work to them at the moment
            # also, if subproc is still running, sleep to give it time to finish
            if(len(self.subprocs) > 0 and len(self.tasks) == 0):
                time.sleep(0.1)
                
        if(self.show_progress):
            printProgressBar(num_tasks, num_tasks)
            print()
            
        return self.shared_results_dict.values()
                
                