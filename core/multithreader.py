# coding=utf-8
import threading


class MultiThreader:
    """
    The MultiThreader object has simple syntax to keep many processes in simple threads that are daemonic, therefore
    will be killed when the main process is killed too.

    :ivar threads: A list of all threads to coordinate them.
    :type threads: list
    :vartype threads: list
    :ivar lock: A Lock that can be acquired from all instances to share that specific thread lock.
    :type lock: threading.Lock
    :vartype threads: list
    """

    def __init__(self):
        self.threads = []
        self.lock = threading.Lock()

    def go(self, *args):
        """
        Main method to get all threads together. First you call `go`, then `join_threads`. The arguments for this have
        to be a list, where [`function`, `arguments`]

        :param args: All threads planned to be threaded.
        """
        for line in args:
            if len(line) == 1:
                thread = threading.Thread(target=line[0])
            else:
                thread = threading.Thread(target=line[0], args=[1])
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

    def join_threads(self):
        """
        Join all threads given by `go` in an interruptable fashion.
        """
        for t in self.threads:
            while t.isAlive():
                t.join(5)

    def get_lock(self):
        """
        Returns the Lock object for this instance and main thread.

        :return: threading.Lock
        """
        return self.lock
