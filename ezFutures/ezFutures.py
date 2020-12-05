from .core.managed_processes import ManagedProcesses
from .core.concurrent_futures_process_pool import ConcurrentFuturesProcessPool

class ezFutures():
    
    def __init__(self, n_procs=4, verbose=False, show_progress=True, timeout=60*60, parallelism_mode='managed.processes'):
        
        self.parallelism_mode = parallelism_mode

        if self.parallelism_mode=='managed.processes':
            self.core = ManagedProcesses(n_procs=n_procs, verbose=verbose, show_progress=show_progress, timeout=timeout)
        elif self.parallelism_mode=='concurrent.futures.process.pool':
            self.core = ConcurrentFuturesProcessPool(n_procs=n_procs)
    
    def submit(self, func, *args, **kwargs):
        
        self.core.submit(func, *args, **kwargs)
        
    def results(self):
        
        return self.core.results()

    def errors(self):

        if self.parallelism_mode=='managed.processes':
            return self.core.shared_error_dict.items()
        else:    
            raise Exception('[errors] method only supported for parallelism_mode: managed.processes')

