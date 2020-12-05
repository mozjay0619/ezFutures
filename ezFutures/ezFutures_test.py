from multiprocessing import Process, Manager, sharedctypes
from collections import defaultdict
import time


class WorkerProcess(Process):
    
    def __init__(self, shared_results_dict, shared_status_dict, shared_error_dict, task):
        super(WorkerProcess, self).__init__()
    
        self.shared_results_dict = shared_results_dict
        self.shared_status_dict = shared_status_dict
        self.shared_error_dict = shared_error_dict
        self.task = task
        
    def run(self):
        """
        We need a way to surface the failure reasons.
        In case of actual failed task.
        """
        
        task_idx, func, args, kwargs = self.task
        
        try:
            result = func(*args, **kwargs)
            self.shared_error_dict[task_idx] = None
            self.shared_status_dict[task_idx] = 'success'
            self.shared_results_dict[task_idx] = result
        except Exception as e:
            self.shared_error_dict[task_idx] = str(e)
            self.shared_status_dict[task_idx] = 'failure'
            self.shared_results_dict[task_idx] = None 


class ezFutures():
    
    def __init__(self, n_procs=4, verbose=False, show_progress=True):
        
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
        
        self.subprocs = []
        
        self.n_procs = n_procs
        self.verbose = verbose
        self.show_progress = show_progress
        
    def submit(self, func, *args, **kwargs):
        
        task_idx = int(self.task_idx)
        self.tasks.append([task_idx, func, args, kwargs])
        
        self.task_idx += 1
        
    def execute_task(self, task):
        
        subproc = WorkerProcess(
            self.shared_results_dict, 
            self.shared_status_dict, 
            self.shared_error_dict,
            task)

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

                self.subprocs.append(subproc)
                
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
                    
                    if self.verbose:
                        print('Looking at pending task {}'.format(pending_task))
                    
                    if pending_task_idx in self.failed_tasks_idx:
                        
                        fail_count = self.task_idx_attempt_dict[task_idx]
                        
                        if fail_count < 3:
                            
                            if self.verbose:
                                print('    pending --> tasks: {}'.format(pending_task))
                                print('    failed {} times'.format(fail_count))
                                
                            # don't append since that will try to do this again right away
                            self.tasks.insert(0, pending_task)
                            self.failed_tasks_idx.remove(pending_task_idx)  # give it another chance
                                
                        else:
                            
                            if self.verbose:
                                print('    pending --> failed tasks: {}'.format(pending_task))
                                print('    * reached MAX_ATTEMPT\n')
                                
                            # just leave the failed idx alone
                            
                    elif pending_task_idx in self.successful_tasks_idx:

                        if self.verbose:
                            print('    pending --> successful tasks: {}\n'.format(pending_task))
                        
                    else:
                        
                        if self.verbose:
                            print('    nothing to update\n')

                        self.pending_tasks.insert(0, pending_task)
                        
            if(self.show_progress):

                cur_len = int(len(self.successful_tasks_idx) + len(self.failed_tasks_idx)) 
                printProgressBar(cur_len, num_tasks)
       
            self.subprocs = [elem for elem in self.subprocs if elem.is_alive()]

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
            
        return pm.shared_results_dict.values()
                
                
