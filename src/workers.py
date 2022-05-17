import time
import random

from PyQt5 import QtCore
from devices import Arduino


class CollectDataWorker(QtCore.QObject):
    """Worker class that collects time series data in infinite loop"""

    sgl_data = QtCore.pyqtSignal(list)
    sgl_finished = QtCore.pyqtSignal()

    def __init__(self, arduino: Arduino):
        super().__init__()

        self.arduino = arduino

        self.running = True

    def run(self):
        while self.running:
            data = self.arduino.read_data()

            # convert incoming data to list
            data = data.split(",")

            # pass data to main loop
            self.sgl_data.emit(data)

        self.sgl_finished.emit()

    def test(self):
        x = 0

        while self.running:
            data = [x, random.randrange(20, 50, 3)]

            # pass data to main loop
            self.sgl_data.emit(data)

            # print(data)
            x += 1

            time.sleep(0.2)

        self.sgl_finished.emit()


class UpdatePlotWorker(QtCore.QObject):
    """Worker class that emits clock signal"""

    sgl_update = QtCore.pyqtSignal()
    sgl_finished = QtCore.pyqtSignal()

    def __init__(self, delay: int = 1):
        super().__init__()

        self.delay = delay

        self.running = True

    def run(self):
        while self.running:
            time.sleep(self.delay)
            self.sgl_update.emit()

        self.sgl_finished.emit()
