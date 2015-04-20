import threading
import time


class MultiThreader(object):
    """Throw bound methods at it and it joins you threads together."""
    threads = list()         # Holds all threads together.

    def go(self, *args):
        for i, line in enumerate(args):
            thread = threading.Thread(target=line, args=(i+1,))
            thread.daemon = True
            thread.start()
            self.threads.append(thread)

    def join_threads(self):
        """
        Join threads in interruptable fashion.
        From http://stackoverflow.com/a/9790882/145400
        """
        for t in self.threads:
            while t.isAlive():
                t.join(5)

    @staticmethod
    def repeater(thread):
        """Test method for tinkering with threading."""
        i = 0
        while True:
            print("Thread {}: Seconds {}".format(thread, i))
            i += 5
            time.sleep(5)


if __name__ == "__main__":
    threader = MultiThreader()
    threader.go(threader.repeater, threader.repeater, threader.repeater)
    try:
        threader.join_threads()
    except KeyboardInterrupt:
        print("Exiting.")