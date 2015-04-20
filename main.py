from MultiThreader import MultiThreader

if __name__ == "__main__":
    thr = MultiThreader()
    thr.go(thr.repeater, thr.repeater, thr.repeater)
    try:
        thr.join_threads()
    except KeyboardInterrupt:
        print("Exiting.")