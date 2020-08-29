import sys
import logging
from PyQt5 import QtCore, QtGui, uic
from PyQt5.QtWidgets import QMainWindow, QAction, qApp, QApplication, QMessageBox, QVBoxLayout, QSizePolicy, QWidget
from PyQt5.QtGui import QIcon
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np

from Environment import Environment

qtCreatorFile = "Visual_UI.ui"
# 使用uic加载
Ui_MainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)

class MyMplCanvas(FigureCanvas):
    """这是一个窗口部件，即QWidget（当然也是FigureCanvasAgg）"""
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        # 每次plot()调用的时候，我们希望原来的坐标轴被清除(所以False)
        self.axes.hold(True)
        self.axes.grid('on')

        self.compute_initial_figure()

        #父类设定
        FigureCanvas.__init__(self, fig)
        self.setParent(parent)

        FigureCanvas.setSizePolicy(self,
                                   QSizePolicy.Expanding,
                                   QSizePolicy.Expanding)
        FigureCanvas.updateGeometry(self)

    def compute_initial_figure(self):
        pass


class MyDynamicMplCanvas(MyMplCanvas, env):
    """动态画布：每秒自动更新，更换一条折线。"""
    def __init__(self, *args, **kwargs):
        MyMplCanvas.__init__(self, *args, **kwargs)
        self.env = env
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.update_figure)
        timer.start(1000)

    def update_figure(self, env):
        self.env.run()

class MyApp(env, QMainWindow, Ui_MainWindow,):

    def __init__(self):
        self.env = env        
        QMainWindow.__init__(self)
        Ui_MainWindow.__init__(self)
        super().__init__()



        self.initUI()
        self.initBtn()
        self.initFrame()

    def initFrame(self):
        self.main_widget = self.frame
        self.layout = QVBoxLayout(self.main_widget)
        self.f = MyMplCanvas(self.main_widget)
        self.layout.addWidget(self.f)

    def initUI(self):               

        self.setupUi(self)
        self.setWindowTitle("PyQt5结合Matplotlib绘图")
        self.setWindowIcon(QIcon("rocket.ico"))   # 设置图标，linux下只有任务栏会显示图标

        self.show()

    def initBtn(self):
        self.btnPlot.clicked.connect(self.plotButton_callback)
        self.btnPlot.setToolTip("Button")         

    def plotButton_callback(self):

        self.drawFrame()

    def drawFrame(self):

        dc = MyDynamicMplCanvas(self.env, self.f, width=5, height=4, dpi=100)
        self.layout.replaceWidget(self.f,dc) # 替换控件


if __name__ == '__main__':

    env = Environment()
    app = QApplication(sys.argv)
    ex = MyApp(env)
    sys.exit(app.exec_())