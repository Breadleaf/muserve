import multiprocessing

bind = "0.0.0.0:7000"

workers = multiprocessing.cpu_count() * 2 + 1

#certfile = "./server.crt"
#keyfile = "./server.key"
