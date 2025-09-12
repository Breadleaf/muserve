# Muserve Auth State Server

This service implements a simple in memory, garbage collected, atomic,
multiprocess safe, JWT state manager. Using python's
`multiprocess.managers.BaseManager` class to implement a protocol in which
several processes may safely interact with a shared socket. The service will
also save the state in a json file to give some level of persistence.
