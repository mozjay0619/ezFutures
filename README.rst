ezFutures
=========

ezFutures is a Python parallel computation tool that provides the user API similar to that of concurrent futures, with various parallelism backends. 

Install
-------

::

	pip install ezFutures


Getting started
---------------

First, we need to import the class:

.. code:: python

	from ezFutures import ezFutures

In order to start working with ezFutures, you must instantiate the class object. The most important parameter to set is the ``n_procs`` parameter which defines the number of processes to run in parallel.

.. code:: python

	ez = ezFutures(n_procs=19)

From there, you can ``submit`` jobs in a sequential manner, just as you do with concurrent futures. However, because ezFutures default parallelism backend is not concurrent futures, merely submitting a task will not start the job. You have the option of using concurrent futures process pool as the parallelism backend (we will update documentation in the future to describe this)

.. code:: python
    
    def some_task(elem):
        return(elem)

    for i in range(10):
        ez.submit(task, i)

You can start the jobs by invoking ``results`` method, just as you would with the concurrent futures API. 




