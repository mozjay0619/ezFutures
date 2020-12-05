from ..utils import printProgressBar

from concurrent.futures import ProcessPoolExecutor
import concurrent.futures


class ConcurrentFuturesProcessPool():
    
    def __init__(self, n_procs=4, *args, **kwargs):
        
        self.executor = executor = ProcessPoolExecutor(max_workers=n_procs)
        self.futures_list = []
        self.results_list = []
    
    def submit(self, func, *args, **kwargs):
        
        future = self.executor.submit(func, *args, **kwargs)
        self.futures_list.append(future)
        
    def results(self):
        
        num_tasks = len(self.futures_list)
        
        if num_tasks > 0:
            printProgressBar(0, num_tasks)

            for idx, future in enumerate(concurrent.futures.as_completed(self.futures_list)):

                self.results_list.append(future.result())
                printProgressBar(idx, num_tasks)

            self.futures_list = []

            printProgressBar(num_tasks, num_tasks)

            self.executor.shutdown(wait=True)
        
        return self.results_list
    
    