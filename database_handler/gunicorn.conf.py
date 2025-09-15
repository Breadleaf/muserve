import multiprocessing

bind = "0.0.0.0:6000"

workers = multiprocessing.cpu_count() * 2 + 1
