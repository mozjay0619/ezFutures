from .core.managed_processes import ManagedProcesses
from .core.concurrent_futures_process_pool import ConcurrentFuturesProcessPool

import psutil
from .utils import contains_return_statement
import multiprocessing
import warnings

def format_Warning(message, category, filename, lineno, line=''):
    return str(filename) + ':' + str(lineno) + ': ' + category.__name__ + ': ' +str(message) + '\n'

class PROCESS_DISCONNECTED(UserWarning):
    pass

class ezFutures():
	
	def __init__(self, n_procs=None, verbose=False, timeout=60*60, n_retries=3, parallelism_mode='managed.processes'):

		if n_procs is None:
			n_procs = psutil.cpu_count(logical=False)
		
		self.parallelism_mode = parallelism_mode

		if self.parallelism_mode=='managed.processes':
			self.core = ManagedProcesses(n_procs=n_procs, verbose=verbose, timeout=timeout, n_retries=n_retries)
		elif self.parallelism_mode=='concurrent.futures.process.pool':
			self.core = ConcurrentFuturesProcessPool(n_procs=n_procs)

		self.has_return_statement = False
		
	def submit(self, func, *args, **kwargs):
		
		self.core.submit(func, *args, **kwargs)

		self.has_return_statement = contains_return_statement(func)

	def globalize(self, local_var, global_name):

		if self.parallelism_mode=='managed.processes':
			return self.core.globalize(local_var, global_name)
		else:	
			raise Exception('[globalize] method only supported for parallelism_mode: managed.processes')
		
	def results(self, show_progress=True):

		results = self.core.results(show_progress=show_progress)

		if len(results)==0 and self.has_return_statement:

			errors = self.errors()
			mp_start_method = multiprocessing.get_start_method()

			if len(errors)==0 and mp_start_method in ['forkserver', 'spawn']:

				warning_msg = 'Please set multiprocessing start method to "fork" or move the function definition to a separate .py file and import it.'
				warnings.warn(warning_msg, PROCESS_DISCONNECTED)
		
		return results

	def errors(self):

		if self.parallelism_mode=='managed.processes':
			return self.core.shared_error_dict.items()
		else:	
			raise Exception('[errors] method only supported for parallelism_mode: managed.processes')

