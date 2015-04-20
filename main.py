from core.MultiThreader import MultiThreader
from core.MassdropBot import MassdropBot

if __name__ == "__main__":
    mb = MassdropBot()
    thr = MultiThreader()
    thr.go(thr.repeater, thr.repeater, thr.repeater)
    try:
        thr.join_threads()
    except KeyboardInterrupt:
        print("Exiting.")