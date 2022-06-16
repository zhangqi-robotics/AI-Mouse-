# !/usr/bin/python
# -*- coding:gbk -*-

# from cProfile import label
from gc import callbacks
import sys
import configparser
import cv2
import os
import numpy
import math
import random
import win32gui
import win32con
import pyautogui as pg
from PIL import Image
from PIL import ImageGrab
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from apscheduler.schedulers.background import BackgroundScheduler
# from goto import with_goto

global _game_windows_flag
class GameWindowsSetting():
    def __init__(self, flag, rect_0, rect_1, rect_2, rect_3):
        self.game_windows_flag = flag
        self.game_windows_rect = [rect_0, rect_1, rect_2, rect_3]

    def setFlagValue(self, flag):
        self.game_windows_flag = flag

    def setRectValue(self, rect_0, rect_1, rect_2, rect_3):
        self.game_windows_rect = [rect_0, rect_1, rect_2, rect_3]

    def printInfo(self):
        print("窗口: %s" %self.game_windows_flag)
        print(self.game_windows_rect)


def write_log(value):
    file_name = 'D:/AI-study/yys-scrite/run/getData-gty.log'
    log_file = open(file_name,'a') #这里用追加模式，如果文件不存在的话会自动创建
    log_file.write(value)
    log_file.close()

def calculate(image1, image2):
    image1 = cv2.cvtColor(numpy.asarray(image1), cv2.COLOR_RGB2BGR)
    image2 = cv2.cvtColor(numpy.asarray(image2), cv2.COLOR_RGB2BGR)
    hist1 = cv2.calcHist([image1], [0], None, [256], [0.0, 255.0])
    hist2 = cv2.calcHist([image2], [0], None, [256], [0.0, 255.0])
    # 计算直方图的重合度
    degree = 0
    for i in range(len(hist1)):
        if hist1[i] != hist2[i]:
            degree = degree + (1 - abs(hist1[i] - hist2[i]) / max(hist1[i], hist2[i]))
        else:
            degree = degree + 1
    degree = degree / len(hist1)
    return degree

def classify_hist_with_split(image1, image2, size=(256, 256)):
    image1 = Image.open(image1)
    image2 = Image.open(image2)
    # 将图像resize后，分离为RGB三个通道，再计算每个通道的相似值
    image1 = cv2.cvtColor(numpy.asarray(image1), cv2.COLOR_RGB2BGR)
    image2 = cv2.cvtColor(numpy.asarray(image2), cv2.COLOR_RGB2BGR)
    image1 = cv2.resize(image1, size)
    image2 = cv2.resize(image2, size)
    sub_image1 = cv2.split(image1)
    sub_image2 = cv2.split(image2)
    sub_data = 0
    for im1, im2 in zip(sub_image1, sub_image2):
        sub_data += calculate(im1, im2)
    sub_data = sub_data / 3
    return sub_data

class QTitleLabel(QLabel):
    """
    新建标题栏标签类
    """
    def __init__(self, *args):
        super(QTitleLabel, self).__init__(*args)
        self.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.setFixedHeight(20)

class QTitleButton(QPushButton):
    """
    新建标题栏按钮类
    """
    def __init__(self, *args):
        super(QTitleButton, self).__init__(*args)
        self.setFont(QFont("Webdings")) # 特殊字体以不借助图片实现最小化最大化和关闭按钮
        self.setFixedWidth(20)

class Main(QMainWindow):
    run_path = ""
    timer_count = 0
    timer_flag = 0
    run_flag = 0
    run_count = 0
    x_pos_his = 0
    y_pos_his = 0
    xy_flag_cnt = 0
    def __init__(self):
        super(Main, self).__init__()
        self.run_path = os.path.split(os.path.realpath(__file__))[0]
        print(self.run_path)
        self.run_flag = 0
        self.sd = BackgroundScheduler()
        self.sd.add_job(self.timer, 'interval', seconds=1)
        self.sd.start()
        self.cf = configparser.ConfigParser()
        self.cf.read(self.run_path+'/run/config.ini')
        self.im = configparser.ConfigParser()
        self.im.read(self.run_path+'/run/image.ini')
        self.setWindowTitle('智能鼠标计划')
        self.setWindowIcon(QIcon(self.run_path+'/run/ZDYC.jpeg'))
        self.resize(400,400)
        self.move(150,200)
        # 增加一个button按钮
        btn = QPushButton('截图',self)
        btn.setGeometry(340,20,50,30)          # 设置窗口大小
        btn.clicked.connect(self.pic_window)
        label = QLabel(self)
        label.setObjectName('pic_name_lable')
        label.resize(120,30)
        label.move(10,20)
        label.setText('特征图片名称')
        self.txt = QLineEdit(self)
        self.txt.resize(200,30)
        self.txt.move(130,20)
        self.txt.setText(".png")
        label_m = QLabel(self)
        label_m.setObjectName('moudle_lable')
        label_m.resize(120,20)
        label_m.move(10,60)
        label_m.setText('模块内容')
        self.list_module = QListWidget(self)
        self.list_module.move(10, 90)
        self.list_module.resize(150,250)
        self.secs = self.cf.sections()
        self.list_module.addItems(self.secs)
        self.list_module.itemSelectionChanged.connect(self.module_select)
        label_c = QLabel(self)
        label_c.setObjectName('context_lable')
        label_c.resize(120,20)
        label_c.move(180,60)
        label_c.setText('详细步骤')
        self.label_l = QLabel(self)
        self.label_l.setObjectName('long_cnt_lable')
        self.label_l.resize(40,20)
        self.label_l.move(310,60)
        self.label_l.setText('0')
        self.list_context = QListWidget(self)
        self.list_context.move(180, 90)
        self.list_context.resize(200,250)
        # self.options = self.cf.options("启动软件")
        # self.value = self.cf.get("启动软件", "step_1")
        # self.items = self.cf.items("启动软件")  #获取键值对
        # self.list_context.addItems(self.options)
        # self.list_context.itemSelectionChanged.connect(self.module_select)
        btn_edit_m = QPushButton('增加模块',self)
        btn_edit_m.setGeometry(15,360,80,30)
        btn_edit_m.clicked.connect(self.add_module)
        # btn_edit_m.clicked.connect(self.pic_window)
        btn_edit_c = QPushButton('删除模块',self)
        btn_edit_c.setGeometry(110,360,80,30)
        btn_edit_c.clicked.connect(self.delete_module)
        btn_run = QPushButton('运行模块',self)
        btn_run.setGeometry(215,360,80,30)
        btn_run.clicked.connect(self.run_module)
        btn_stop = QPushButton('停止模块',self)
        btn_stop.setGeometry(310,360,80,30)
        btn_stop.clicked.connect(self.stop_module)
        self.pic_win = Child()
        self.add_win = ChildModule()

    def pic_window(self):
        self.pic_win.show()

    def add_module(self):
        secs = self.im.sections()
        self.add_win.list_src.addItems(secs)
        self.add_win.show()

    def module_select(self):
        curtext = self.list_module.selectedItems()
        self.options = self.cf.options(curtext[0].text())
        # self.value = self.cf.get("启动软件", "step_1")
        # self.items = self.cf.items("启动软件")  #获取键值对
        # self.cf.add_section("关闭游戏")
        # self.cf.set("关闭游戏", "key", "value")
        # self.cf.write(open('D:/AI-study/yys-scrite/run/config.ini','w'))
        self.list_context.clear()
        self.list_context.addItems(self.options)
        # label.setText(curtext[0].text())

    def delete_module(self):
        curtext = self.list_module.selectedItems()
        self.cf.remove_section(curtext[0].text())
        self.cf.write(open(self.run_path+'/run/config.ini','w'))
        selected = self.list_module.selectedItems()
        if len(selected) <= 0:
            return
        for item in selected:
            self.list_module.removeItemWidget(self.list_module.takeItem(self.list_module.row(item)))
        count = self.list_context.count()
        for i in range(count):
            self.list_context.removeItemWidget(self.list_context.item(i))

    def stop_module(self):
        self.timer_count = 0
        self.run_flag = 0

    def run_module(self):
        self.timer_count = 0
        self.timer_flag=0
        self.run_flag = 1
        self.run_count = 0


    def timer(self):
        if self.run_flag == 1:
            count = 0
            curtext = self.list_module.selectedItems()
            options = self.cf.options(curtext[0].text())
            for i in options:
                if count < self.timer_count:
                    count = count+1
                    continue
                value = self.cf.get(curtext[0].text(), i)
                x_start = int(self.im.get(value,"x_start"))
                y_start = int(self.im.get(value,"y_start"))
                x_end = int(self.im.get(value,"x_end"))
                y_end = int(self.im.get(value,"y_end"))
                xy_box = (x_start,y_start,x_end,y_end)
                # print(value , xy_box)
                img = ImageGrab.grab(xy_box)
                img.save(self.run_path+'/run/run.png')
                img1_path = self.run_path+'/run/run.png'
                img2_path = self.run_path+'/image/'+value
                result = classify_hist_with_split(img1_path, img2_path)
                # print("result: " + "%.2f%%" % (result * 100))
                if result > 0.95:
                    rand = random.random()
                    pos_x_0 = math.ceil((x_end-x_start)/4+rand*((x_end-x_start)/2))
                    rand = random.random()
                    pos_y_0 = math.ceil((y_end-y_start)/4+rand*((y_end-y_start)/2))
                    rand = random.random()
                    if self.x_pos_his == pos_x_0 and self.y_pos_his == pos_y_0:
                        xy_flag_cnt = xy_flag_cnt + 1
                    else:
                        xy_flag_cnt = 0
                        self.x_pos_his = pos_x_0
                        self.y_pos_his = pos_y_0
                    if xy_flag_cnt < 3:
                        pg.moveTo(x_start+pos_x_0, y_start+pos_y_0, 0.15+rand/10)
                        pg.click()
                        self.timer_flag = 1
                else:
                    if self.timer_flag == 1:
                        self.timer_flag=0
                        self.timer_count = self.timer_count+1
                        if self.timer_count == len(options):
                            self.timer_count = 0
                        elif self.timer_count == 1:
                            self.run_count = self.run_count+1
                            write_log("Run Counter is: %d\n" % self.run_count)
                            self.label_l.setText(str(self.run_count))
                            rand = random.random()
                            pos_x = math.ceil((x_end-x_start)/4+rand*((x_end-x_start)/2)-rand*400)
                            rand = random.random()
                            pos_y = math.ceil((y_end-y_start)/4+rand*((y_end-y_start)/2)-rand*300)
                            rand = random.random()
                            pg.moveTo(x_start+pos_x, y_start+pos_y, 0.4+rand/5)
                break

class Child(QWidget,object):
    xy_box = (0,0,0,0)
    def __init__(self):
        super().__init__()
        self.setWindowTitle('截图窗口')
        self.setWindowOpacity(0.3)
        self.resize(200,200)
        self.setWindowFlags(Qt.FramelessWindowHint)
        self._tracking = False
        self._startPos = None
        self._endPos = None
        self._padding = 10 # 设置边界宽度为10
        self.setMinimumWidth(50)
        self.setMinimumHeight(50)
        self._corner_drag = False
        self._bottom_drag = False
        self._right_drag = False
        self._TitleLabel = QTitleLabel(self)
        self.setCloseButton(True)
        self.setOkButton(True)

    def onClicked(self):
        self.close()
        self.xy_box = (self.x(),self.y(),self.x()+self.width(),self.y()+self.height())
        img = ImageGrab.grab(self.xy_box)
        img.save(main.run_path+'/image/'+main.txt.text())
        main.im.add_section(main.txt.text())
        main.im.set(main.txt.text(), "x_start", str(self.xy_box[0]))
        main.im.set(main.txt.text(), "y_start", str(self.xy_box[1]))
        main.im.set(main.txt.text(), "x_end", str(self.xy_box[2]))
        main.im.set(main.txt.text(), "y_end", str(self.xy_box[3]))
        main.im.write(open(main.run_path+'/run/image.ini','w'))
        #3943 x 2451     1705 x 1563       2560 1600     1167 x 1020

    def setCloseButton(self, bool):
        # 给widget定义一个setCloseButton函数，为True时设置一个关闭按钮
        if bool == True:
            self._CloseButton = QTitleButton(b'\xef\x81\xb2'.decode("utf-8"), self)
            self._CloseButton.setObjectName("CloseButton") # 设置按钮的ObjectName以在qss样式表内定义不同的按钮样式
            self._CloseButton.setToolTip("关闭窗口")
            self._CloseButton.setMouseTracking(True) # 设置按钮鼠标跟踪（如不设，则按钮在widget上层，无法实现跟踪）
            self._CloseButton.setFixedHeight(self._TitleLabel.height()) # 设置按钮高度为标题栏高度
            self._CloseButton.clicked.connect(self.close) # 按钮信号连接到关闭窗口的槽函数
            self._CloseButton.move(0,0)

    def setOkButton(self, bool):
        # 给widget定义一个setOkButton函数，为True时设置一个关闭按钮
        if bool == True:#\xE2\xAD\x95   \xE2\x97\x8F   \x4F\x4B  \xE2\x9D\xA4
            self._OkButton = QTitleButton(b'\xef\x80\xb1'.decode("utf-8"), self)
            self._OkButton.setObjectName("OkButton") # 设置按钮的ObjectName以在qss样式表内定义不同的按钮样式
            self._OkButton.setToolTip("截图窗口")
            self._OkButton.setMouseTracking(True) # 设置按钮鼠标跟踪（如不设，则按钮在widget上层，无法实现跟踪）
            self._OkButton.setFixedHeight(self._TitleLabel.height()) # 设置按钮高度为标题栏高度
            self._OkButton.clicked.connect(self.onClicked) # 按钮信号连接到关闭窗口的槽函数
            self._OkButton.move(20,0)

    def resizeEvent(self, a0: QResizeEvent) :
        # 重新调整边界范围以备实现鼠标拖放缩放窗口大小，采用三个列表生成式生成三个列表
        self._right_rect = [QPoint(x,y) for x in range(self.width() - self._padding, self.width() + 1)
                                        for y in range(1, self.height() - self._padding)]
        self._bottom_rect = [QPoint(x, y) for x in range(1, self.width() - self._padding)
                                        for y in range(self.height() - self._padding, self.height() + 1)]
        self._corner_rect = [QPoint(x, y) for x in range(self.width() - self._padding, self.width() + 1)
                                        for y in range(self.height() - self._padding, self.height() + 1)]

    def mouseMoveEvent(self, a0: QMouseEvent) :
        if a0.pos() in self._corner_rect:
            self.setCursor(Qt.SizeFDiagCursor)
        elif a0.pos() in self._bottom_rect:
            self.setCursor(Qt.SizeVerCursor)
        elif a0.pos() in self._right_rect:
            self.setCursor(Qt.SizeHorCursor)
        else:
            self.setCursor(Qt.ArrowCursor)
        if Qt.LeftButton and self._right_drag:
            # 右侧调整窗口宽度
            self.resize(a0.pos().x(), self.height())
            a0.accept()
        elif Qt.LeftButton and self._bottom_drag:
            # 下侧调整窗口高度
            self.resize(self.width(), a0.pos().y())
            a0.accept()
        elif Qt.LeftButton and self._corner_drag:
            # 右下角同时调整高度和宽度
            self.resize(a0.pos().x(), a0.pos().y())
            a0.accept()
        elif Qt.LeftButton and self._tracking:
            self._endPos = a0.pos() - self._startPos
            self.move(self.pos() + self._endPos)
            a0.accept()

    def mousePressEvent(self, a0: QMouseEvent) :
        if (a0.button() == Qt.LeftButton) and (a0.pos() in self._corner_rect):
            # 鼠标左键点击右下角边界区域
            self._corner_drag = True
            a0.accept()
        elif (a0.button() == Qt.LeftButton) and (a0.pos() in self._right_rect):
            # 鼠标左键点击右侧边界区域
            self._right_drag = True
            a0.accept()
        elif (a0.button() == Qt.LeftButton) and (a0.pos() in self._bottom_rect):
            # 鼠标左键点击下侧边界区域
            self._bottom_drag = True
            a0.accept()
        elif a0.button() == Qt.LeftButton:
            self._startPos = QPoint(a0.x(), a0.y())
            self._tracking = True
            a0.accept()

    def mouseReleaseEvent(self, a0: QMouseEvent) :
        if a0.button() == Qt.LeftButton:
            self._tracking = False
            self._startPos = None
            self._endPos = None
            self._corner_drag = False
            self._bottom_drag = False
            self._right_drag = False

class ChildModule(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('添加窗口')
        self.setWindowIcon(QIcon(os.path.split(os.path.realpath(__file__))[0]+'/run/ADDMODULE.jpeg'))
        self.setWindowOpacity(0.9)
        self.resize(400,300)
        self.move(150,250)
        label = QLabel(self)
        label.setObjectName('module_name')
        label.resize(80,30)
        label.move(5,20)
        label.setText('模块名称')
        self.txt = QLineEdit(self)
        self.txt.resize(200,30)
        self.txt.move(85,20)
        self.txt.setText("")
        btn = QPushButton('添加',self)
        btn.resize(50,30)
        btn.move(290,20)
        btn.clicked.connect(self.add_fun)
        self.list_src = QListWidget(self)
        self.list_src.move(10, 60)
        self.list_src.resize(190,200)
        # self.list_src.itemSelectionChanged.connect(self.module_select)
        self.list_dec = QListWidget(self)
        self.list_dec.move(210, 60)
        self.list_dec.resize(180,200)
        btn_add = QPushButton('添加',self)
        btn_add.setGeometry(20,265,80,30)
        btn_add.clicked.connect(self.add_module)
        # btn_edit_m.clicked.connect(self.pic_window)
        btn_del = QPushButton('删除',self)
        btn_del.setGeometry(300,265,80,30)
        btn_del.clicked.connect(self.delete_module)

    def delete_module(self):
        selected = self.list_dec.selectedItems()
        if len(selected) <= 0:
            return
        for item in selected:
            self.list_dec.removeItemWidget(self.list_dec.takeItem(self.list_dec.row(item)))

    def add_module(self):
        curtext = self.list_src.selectedItems()
        self.list_dec.addItem(curtext[0].text())

    def add_fun(self):
        main.cf.add_section(self.txt.text())
        count = self.list_dec.count()
        for i in range(count):
            main.cf.set(self.txt.text(), str(i), self.list_dec.item(i).text())
        main.cf.write(open(main.run_path+'/run/config.ini','w'))
        main.list_module.addItem(self.txt.text())

def callback(hwnd, extra):
    global _game_windows_flag
    rect = win32gui.GetWindowRect(hwnd)
    if rect[0] == rect[1] == rect[2] == rect[3] == 0:
        pass
    else:
        # print("Window %s:" %win32gui.GetWindowText(hwnd))
        # print(rect)
        # 以下软件仅仅用于个人测试该代码是否可以正常使用，具体还请个人用于可以减轻个人重复性工作的地方。
        if win32gui.GetWindowText(hwnd) == "阴阳师-网易游戏":
            win32gui.SetWindowPos(hwnd, 0, 1360, 800, 1200, 720, win32con.SWP_NOZORDER)
        
        if win32gui.GetWindowText(hwnd) == "阴阳师 - MuMu模拟器":
            win32gui.SetWindowPos(hwnd, 0, 10, 750, 1200, 757, win32con.SWP_NOZORDER)



if __name__ =="__main__":
    win32gui.EnumWindows(callback, None)
    _game_window_setting_1 = GameWindowsSetting(1,0,0,0,0)
    _game_window_setting_2 = GameWindowsSetting(2,0,0,0,0)
    _game_window_setting_1.printInfo()
    _game_window_setting_2.printInfo()
    app = 0
    app = QApplication(sys.argv)
    app.setStyleSheet(open(os.path.split(os.path.realpath(__file__))[0]+'/run/UnFrameStyle.qss').read())
    main = Main()
    ch = Child()
    chm = ChildModule()
    main.show()
    sys.exit(app.exec_())

# (1349, 801, 2563, 1530)  1214   729     0.6      5:3
# (1622, 945, 2560, 1518)  938    537     0.57
# (1179, 702, 2564, 1527)  1385   825     0.59