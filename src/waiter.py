import time

class Waiter:
    def __init__(self, wait_for_seconds:float):
        self.wait_for_seconds = wait_for_seconds
        self.wait_until:float = time.time() + self.wait_for_seconds

    def checkDone(self):
        now = time.time()
        if now > self.wait_until:
            self.startWait()
            return True
        return False

    def startWait(self):
        self.wait_until = time.time() + self.wait_for_seconds
