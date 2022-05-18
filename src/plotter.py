import os
import sys
import csv
import numpy as np

import qtmodern.styles
import qtmodern.windows

from PyQt5 import QtWidgets, QtCore, QtGui
from pyqtgraph import PlotWidget

from devices import Arduino
from workers import CollectDataWorker, UpdatePlotWorker


class MainWindow(QtWidgets.QMainWindow):
    """Create user interface and manage data threads"""

    sgl_stop = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        # reserve space in memory for data
        self.data = np.empty((2, int(1e9)), np.float64)

        self.counter = 0  # tracks current data index
        self.interval = 100  # determines when data is saved to file
        self.display = 100  # controls plot domain

        # self.arduino = Arduino(port="COM3", baudrate=115200)
        self.arduino = object()

        # initialize layouts
        self.layout_central = QtWidgets.QVBoxLayout()
        self.layout_controls = QtWidgets.QHBoxLayout()
        self.layout_display = QtWidgets.QVBoxLayout()

        # initialize widgets
        self.plt = PlotWidget()
        self.btn_start = QtWidgets.QPushButton("Start")
        self.btn_stop = QtWidgets.QPushButton("Stop")
        self.lbl_display = QtWidgets.QLabel("No. data points")
        self.txt_display = QtWidgets.QLineEdit(str(self.display))

        # restrict line width
        self.txt_display.setMaximumWidth(100)

        # only allow user to input integer data
        self.txt_display.setValidator(QtGui.QIntValidator(0, 100))

        # connect the "clicked" signal to callback functions
        self.btn_start.clicked.connect(self.start_recording)
        self.btn_stop.clicked.connect(self.stop_recording)

        # update display value when user presses enter
        self.txt_display.returnPressed.connect(self.update_display_value)

        # populate layouts
        self.layout_display.addWidget(self.lbl_display)
        self.layout_display.addWidget(self.txt_display)
        self.layout_controls.addLayout(self.layout_display)
        self.layout_controls.addWidget(self.btn_start)
        self.layout_controls.addWidget(self.btn_stop)
        self.layout_central.addWidget(self.plt)
        self.layout_central.addLayout(self.layout_controls)

        # self.setWindowTitle("Plotting Application")

        self.setGeometry(300, 100, 800, 600)
        self.setCentralWidget(QtWidgets.QWidget(self))
        self.centralWidget().setLayout(self.layout_central)

    def update_display_value(self):
        self.display = int(self.txt_display.text())

    def start_recording(self):
        """Re-initialize plot and counter, and setup data/timer threads"""

        # clear plot and reset counter
        self.plt.clear()
        self.counter = 0

        self.data_thread = QtCore.QThread()
        self.data_worker = CollectDataWorker(arduino=self.arduino)
        self.data_worker.moveToThread(self.data_thread)
        self.data_thread.started.connect(self.data_worker.test)
        self.data_worker.sgl_finished.connect(self.data_thread.quit)
        self.data_worker.sgl_finished.connect(self.data_worker.deleteLater)
        self.data_thread.finished.connect(self.data_thread.deleteLater)
        self.data_worker.sgl_data.connect(self.update_data)

        self.plot_thread = QtCore.QThread()
        self.plot_worker = UpdatePlotWorker(delay=0.5)
        self.plot_worker.moveToThread(self.plot_thread)
        self.plot_thread.started.connect(self.plot_worker.run)
        self.plot_worker.sgl_finished.connect(self.plot_thread.quit)
        self.plot_worker.sgl_finished.connect(self.plot_worker.deleteLater)
        self.plot_thread.finished.connect(self.plot_thread.deleteLater)
        self.plot_worker.sgl_update.connect(self.update_plot)

        # start threads
        self.data_thread.start()
        self.plot_thread.start()

    def stop_recording(self):
        """Break worker loops and safely close serial port"""

        self.data_worker.running = False
        self.plot_worker.running = False

        self.arduino.close()

    def update_data(self, data: list):
        """Write data to reserved locations in memory"""

        self.data[0][self.counter] = data[0]
        self.data[1][self.counter] = data[1]

        self.counter += 1

        if not self.counter % self.interval:
            self.write_data_to_file()

    def update_plot(self):
        """Update plot using counter to set data range"""

        self.plt.clear()

        # check if user wants to restrict data presentation
        if self.display > 9:
            if self.counter < self.display:
                self.plt.plot(
                    self.data[0][: self.counter], self.data[1][: self.counter]
                )
            else:
                self.plt.plot(
                    self.data[0][self.counter - self.display : self.counter],
                    self.data[1][self.counter - self.display : self.counter],
                )
        else:
            self.plt.plot(self.data[0][: self.counter], self.data[1][: self.counter])

    def write_data_to_file(self):
        path = "/Users/lukasvasadi/Desktop/data.csv"

        if os.path.exists(path):
            with open(path, "a", newline="") as file:
                writer = csv.writer(file)

                for i in range(self.counter - self.interval, self.counter):
                    writer.writerow(self.data[:, i])
        else:
            fieldnames = ["time", "data"]

            with open(path, "w", newline="") as file:
                writer = csv.writer(file)
                writer.writerow(fieldnames)

                for i in range(self.counter):
                    writer.writerow(self.data[:, i])


def main():
    app = QtWidgets.QApplication(sys.argv)
    win = MainWindow()

    qtmodern.styles.dark(app)

    main = qtmodern.windows.ModernWindow(win)
    main.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
