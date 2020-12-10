from .core.managed_processes import ManagedProcesses
from .core.concurrent_futures_process_pool import ConcurrentFuturesProcessPool

class ezFutures():
    
    def __init__(self, n_procs=4, verbose=False, show_progress=True, timeout=60*60, n_retries=3, parallelism_mode='managed.processes'):
        
        self.parallelism_mode = parallelism_mode

        if self.parallelism_mode=='managed.processes':
            self.core = ManagedProcesses(n_procs=n_procs, verbose=verbose, show_progress=show_progress, timeout=timeout, n_retries=n_retries)
        elif self.parallelism_mode=='concurrent.futures.process.pool':
            self.core = ConcurrentFuturesProcessPool(n_procs=n_procs)
    
    def submit(self, func, *args, **kwargs):
        
        self.core.submit(func, *args, **kwargs)

    def globalize(self, local_var, global_name):

        if self.parallelism_mode=='managed.processes':
            return self.core.globalize(local_var, global_name)
        else:    
            raise Exception('[globalize] method only supported for parallelism_mode: managed.processes')
        
    def results(self):
        
        return self.core.results()

    def errors(self):

        if self.parallelism_mode=='managed.processes':
            return self.core.shared_error_dict.items()
        else:    
            raise Exception('[errors] method only supported for parallelism_mode: managed.processes')

