from concurrent.futures import ProcessPoolExecutor
import concurrent.futures


class ezFutures():
    
    def __init__(self, n_procs=4):
        
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
    
    def printProgressBar (iteration, total, prefix = 'Progress:', suffix = '', decimals = 1, length = 50, fill = '█', printEnd = "\r"):
        """
        Call in a loop to create terminal progress bar
        @params:
            iteration   - Required  : current iteration (Int)
            total       - Required  : total iterations (Int)
            prefix      - Optional  : prefix string (Str)
            suffix      - Optional  : suffix string (Str)
            decimals    - Optional  : positive number of decimals in percent complete (Int)
            length      - Optional  : character length of bar (Int)
            fill        - Optional  : bar fill character (Str)
            printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
        """
        percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
        filledLength = int(length * iteration // total)
        bar = fill * filledLength + '-' * (length - filledLength)
        print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
        # Print New Line on Complete
        if iteration == total: 
            print(f'\r', end = printEnd)

