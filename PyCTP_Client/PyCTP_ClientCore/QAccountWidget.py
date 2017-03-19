# -*- coding: utf-8 -*-

"""
Module implementing QAccountWidget.
"""
from PyQt4 import QtGui, QtCore
from PyQt4.QtGui import QWidget
from PyQt4.QtCore import pyqtSlot
from PyQt4.QtCore import QPoint
from PyQt4.QtGui import QTabBar
from Ui_QAccountWidget import Ui_Form
import json
from Strategy import Strategy
from QMessageBox import QMessageBox
from StrategyDataModel import StrategyDataModel


try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

"""
function structure
1. slot_update_strategy(obj_strategy)
    调用情景：发送参数（一个策略）、查询参数（所有策略）

2. update_statistics(obj_strategy)
    调用情景：成交回报（一个策略）、市场行情变化（一个策略）

3. update_spread()
    调用情景：市场行情变化（一个策略）

4. update_account_info()
    调用情景：查询账户、市场行情变化（定时任务0.5秒）
"""


class QAccountWidget(QWidget, Ui_Form):
    """
    Class documentation goes here.
    """
    Signal_SendMsg = QtCore.pyqtSignal(str)  # 自定义信号
    signal_update_groupBox_trade_args_for_query = QtCore.pyqtSignal(Strategy)  # 定义信号：更新界面参数框
    signal_send_msg = QtCore.pyqtSignal(str)  # 窗口修改策略 -> SocketManager发送修改指令
    signal_show_QMessageBox = QtCore.pyqtSignal(list)  # 定义信号：弹窗 -> ClientMain(主线程)中槽函数调用弹窗
    signal_lineEdit_duotoujiacha_setText = QtCore.pyqtSignal(str)  # 定义信号：多头价差lineEdit更新
    signal_lineEdit_kongtoujiacha_setText = QtCore.pyqtSignal(str)  # 定义信号：self.lineEdit_kongtoujiacha.setText()
    signal_lineEdit_duotoujiacha_setStyleSheet = QtCore.pyqtSignal(str)  # 定义信号：lineEdit_duotoujiacha.setStyleSheet()
    signal_lineEdit_kongtoujiacha_setStyleSheet = QtCore.pyqtSignal(str)  # 定义信号：lineEdit_kongtoujiacha.setStyleSheet()

    # QAccountWidget(ClientMain=self.__client_main,
    #                CTPManager=self,
    #                SocketManager=self.__socket_manager,
    #                User=self)
    # def __init__(self, str_widget_name, obj_user=None, list_user=None, parent=None, ClientMain=None, SocketManager=None, CTPManager=None):
    def __init__(self, parent=None):
        """
        Constructor
        
        @param parent reference to the parent widget
        @type QWidget
        """
        super(QAccountWidget, self).__init__(parent)
        self.setupUi(self)  # 调用父类中配置界面的方法
        self.popMenu = QtGui.QMenu(self.tableWidget_Trade_Args)  # 创建鼠标右击菜单
        self.tabBar = QtGui.QTabBar(self.widget_tabbar)  # 创建QTabBar，选项卡
        self.tabBar.currentChanged.connect(self.slot_tab_changed)  # 信号槽连接：信号为自带的currentChanged，槽函数为slot_tab_changed，QTabBar切换tab时触发
        self.__dict_clicked_info = dict()  # 记录鼠标点击策略，{tab_name: strategy_id,}
        self.slot_addTabBar("所有账户")
        # self.tabBar.addTab("所有账户")

        self.__init_finished = False  # QAccountWidget界面初始化完成标志位，初始值为False

        """初始化StrategyDataModel"""
        # self.StrategyDataModel = StrategyDataModel(mylist=self.__ctp_manager.get_list_strategy_view())
        # self.tableView_Trade_Args.setModel(self.StrategyDataModel)

        """
        # 设置tableWidget列的宽度
        # self.tableWidget_Trade_Args.setColumnWidth(0, 50)  # 开关
        # self.tableWidget_Trade_Args.setColumnWidth(1, 90)  # 期货账号
        # self.tableWidget_Trade_Args.setColumnWidth(2, 90)  # 策略编号
        # self.tableWidget_Trade_Args.setColumnWidth(3, 120)  # 交易合约
        # self.tableWidget_Trade_Args.setColumnWidth(4, 90)  # 总持仓
        # self.tableWidget_Trade_Args.setColumnWidth(5, 90)  # 买持仓
        # self.tableWidget_Trade_Args.setColumnWidth(6, 90)  # 卖持仓
        # self.tableWidget_Trade_Args.setColumnWidth(7, 90)  # 持仓盈亏
        # self.tableWidget_Trade_Args.setColumnWidth(8, 90)  # 平仓盈亏
        # self.tableWidget_Trade_Args.setColumnWidth(9, 90)  # 手续费，缺少净盈亏
        # self.tableWidget_Trade_Args.setColumnWidth(10, 90)  # 成交量
        # self.tableWidget_Trade_Args.setColumnWidth(11, 90)  # 成交额
        # self.tableWidget_Trade_Args.setColumnWidth(12, 90)  # 平均滑点， 换成A成交率、B成交率
        # self.tableWidget_Trade_Args.setColumnWidth(13, 90)  # 交易模型
        # self.tableWidget_Trade_Args.setColumnWidth(14, 90)  # 下单算法
        """

        # 禁用GroupBox中的按钮
        self.pushButton_set_strategy.setEnabled(False)
        self.pushButton_query_strategy.setEnabled(False)
        self.pushButton_set_position.setEnabled(False)

        # 初始化comboBox_jiaoyimoxing
        # 客户端存储的交易模型可选项，服务端仅保留策略所设置交易模型，当前交易模型空白
        # 初始化comboBox_xiadansuanfa
        # index_item = -1
        # for i in self.__socket_manager.get_list_algorithm_info():
        #     index_item += 1
        #     self.comboBox_xiadansuanfa.insertItem(index_item, i['name'])

        # 添加策略菜单
        self.action_add = QtGui.QAction("添加策略", self)
        self.action_add.triggered.connect(self.slot_action_add_strategy)
        self.popMenu.addAction(self.action_add)
        # 删除策略菜单
        self.action_del = QtGui.QAction("删除策略", self)
        self.action_del.triggered.connect(self.slot_action_del_strategy)
        self.popMenu.addAction(self.action_del)

        """信号槽绑定"""
        self.__signal_pushButton_set_position_setEnabled_connected = False  # 信号槽绑定标志，初始值为False
        self.Signal_SendMsg.connect(self.slot_SendMsg)  # 绑定信号、槽函数
        self.signal_lineEdit_duotoujiacha_setText.connect(self.lineEdit_duotoujiacha.setText)
        self.signal_lineEdit_kongtoujiacha_setText.connect(self.lineEdit_kongtoujiacha.setText)
        self.signal_lineEdit_duotoujiacha_setStyleSheet.connect(self.lineEdit_duotoujiacha.setStyleSheet)
        self.signal_lineEdit_kongtoujiacha_setStyleSheet.connect(self.lineEdit_kongtoujiacha.setStyleSheet)

        """类局部变量声明"""
        self.__spread_long = None  # 界面价差初始值
        self.__spread_short = None  # 界面价差初始值
        self.__item_on_off_status = None  # 策略开关item的状态，dict
        self.__item_only_close_status = None  # 策略开关item的状态，dict
        self.__clicked_item = None  # 鼠标点击的item对象
        self.__clicked_status = None  # 鼠标点击的信息



    # 初始化创建tableWidget内的item，根据期货账户的策略数量总和来决定行数
    def slot_init_tableWidget(self, list_strategy_arguments):
        print("QAccountWidget.slot_init_tableWidget() list_strategy_arguments =", list_strategy_arguments)
        for i in list_strategy_arguments:
            self.slot_insert_strategy(i)

    # 自定义槽
    @pyqtSlot(str)
    def slot_SendMsg(self, msg):
        print("QAccountWidget.slot_SendMsg()", msg)
        # send json to server
        self.__client_main.get_SocketManager().send_msg(msg)

    def slot_addTabBar(self, user_id):
        self.__dict_clicked_info[user_id] = dict()
        self.tabBar.addTab(user_id)
        print(">>> QAccountWidget.slot_addTabBar() self.__dict_clicked_info =", self.__dict_clicked_info)

    def showEvent(self, QShowEvent):
        pass
        # print(">>> showEvent()", self.objectName(), "widget_name=", self.__widget_name)
        # self.__client_main.set_show_widget(self)  # 显示在最前端的窗口设置为ClientMain的属性，全局唯一
        # self.__client_main.set_show_widget_name(self.__widget_name)  # 显示在最前端的窗口名称设置为ClientMain的属性，全局唯一
        # 获取tab——name
        # print(">>> tabName")
        # self.__client_main.set_showEvent(True)  # 是否有任何窗口显示了

    def hideEvent(self, QHideEvent):
        pass
        # print(">>> hideEvent()", self.objectName(), "widget_name=", self.__widget_name)
        # self.__client_main.set_hideQAccountWidget(self)  # 将当前隐藏的窗口对象设置为ClienMain类的属性

    # 槽函数，连接信号：QCTP.signal_on_tab_accounts_currentChanged，切换tab页的时候动态设置obj_user给QAccountWidget
    def slot_tab_changed(self, int_tab_index):
        self.__current_tab_name = self.tabBar.tabText(int_tab_index)
        print("QAccountWidget.slot_tab_changed() self.__current_tab_name =", self.__current_tab_name)
        if len(self.__dict_clicked_info[self.__current_tab_name]) > 0:
            row = self.__dict_clicked_info[self.__current_tab_name]['row']
            self.tableWidget_Trade_Args.setCurrentCell(row, 0)
        self.update_tableWidget_Trade_Args()
        self.update_groupBox()

    def set_ClientMain(self, obj_ClientMain):
        self.__client_main = obj_ClientMain
        
    def get_ClientMain(self):
        return self.__client_main

    def set_SocketManager(self, obj_SocketManager):
        self.__socket_manager = obj_SocketManager

    def get_SocketManager(self):
        return self.__socket_manager

    def set_QLogin(self, obj_QLogin):
        self.__q_login = obj_QLogin

    def get_QLogin(self):
        return self.__q_login

    def set_CTPManager(self, obj_CTPManager):
        self.__ctp_manager = obj_CTPManager

    def get_CTPManager(self):
        return self.__ctp_manager

    # 形参为user对象或ctpmanager对象，ctpmanager代表所有期货账户对象的总和
    def set_user(self, obj_user):
        self.__user = obj_user

    def get_user(self):
        return self.__user

    def get_widget_name(self):
        # print(">>> QAccountWidget.get_widget_name() widget_name=", self.__widget_name, 'user_id=', self.__clicked_status['user_id'], 'strategy_id=', self.__clicked_status['strategy_id'])
        return self.__widget_name

    # 设置窗口名称
    def set_widget_name(self, str_name):
        # print(">>> QAccountWidget.set_widget_name() widget_name=", self.__widget_name, 'user_id=', self.__clicked_status['user_id'], 'strategy_id=', self.__clicked_status['strategy_id'])
        self.__widget_name = str_name

    # 设置鼠标点击状态，信息包含:item所在行、item所在列、widget_name、user_id、strategy_id
    def set_clicked_status(self, dict_input):
        self.__clicked_status = dict_input
        self.__client_main.set_clicked_status(dict_input)  # 保存鼠标点击状态到ClientMain的属性，保存全局唯一一个鼠标最后点击位置
        item = self.tableWidget_Trade_Args.item(dict_input['row'], dict_input['column'])
        self.__client_main.set_clicked_item(item)  # 鼠标点击的item设置为ClientMain的属性，全局唯一
        print(">>> QAccountWidget.set_clicked_status() widget_name=", self.__widget_name, 'user_id=', self.__clicked_status['user_id'], 'strategy_id=', self.__clicked_status['strategy_id'])

    # return dict()
    def get_clicked_status(self):
        print(">>> QAccountWidget.get_clicked_status() self.sender()=", self.sender(), " widget_name=", self.__widget_name, 'user_id=',
              self.__clicked_status['user_id'], 'strategy_id=', self.__clicked_status['strategy_id'])
        return self.__clicked_status
    
    def set_list_strategy(self, list_strategy):
        self.__list_strategy = list_strategy
        
    def get_list_strategy(self):
        return self.__list_strategy

    # 传入形参：table对象和字符串，返回同名的表头所在的列标
    def getHeaderItemColumn(self, obj_tableWidget, str_column_name):
        print(">>> QAccountWidget.getHeaderItemColumn() widget_name=", self.__widget_name, 'user_id=',
              self.__clicked_status['user_id'], 'strategy_id=', self.__clicked_status['strategy_id'])
        for i in range(obj_tableWidget.rowCount()):
            if obj_tableWidget.horizontalHeaderItem(i).text() == str_column_name:
                return i
        return -1

    # 设置信号槽连接状态的标志位
    def set_signal_pushButton_set_position_setEnabled_connected(self, bool_input):
        self.__signal_pushButton_set_position_setEnabled_connected = bool_input
        # print(">>> QAccountWidget.set_signal_pushButton_set_position_setEnabled_connected() widget_name=", self.__widget_name, "信号槽连接状态设置为", self.__signal_pushButton_set_position_setEnabled_connected)

    def get_signal_pushButton_set_position_setEnabled_connected(self):
        return self.__signal_pushButton_set_position_setEnabled_connected

    # 判断当前窗口是否单账户
    def is_single_user_widget(self):
        if self.__widget_name == "总账户":
            return False
        else:
            return True

    """
    # 向界面插入策略，形参是任何策略对象，该方法自动判断策略是否属于本窗口
    @QtCore.pyqtSlot(object)
    def slot_insert_strategy(self, obj_strategy):
        # 总账户窗口或策略所属的单账户窗口
        if self.is_single_user_widget() is False or obj_strategy.get_user_id() == self.__widget_name:
            i_row = self.tableWidget_Trade_Args.rowCount()  # 将要出入到的行标
            self.tableWidget_Trade_Args.insertRow(i_row)
            print(">>> QAccountWidget.slot_insert_strategy() 添加策略，widget_name=", self.__widget_name, "i_row=", i_row, "user_id=", obj_strategy.get_user_id(), "strategy_id=", obj_strategy.get_strategy_id(), "self.sender=", self.sender())
            dict_strategy_args = obj_strategy.get_arguments()  # 获取策略参数
            dict_position = obj_strategy.get_position()  # 获取策略持仓
            item_strategy_on_off = QtGui.QTableWidgetItem()  # 开关
            if dict_strategy_args['strategy_on_off'] == 0:
                item_strategy_on_off.setCheckState(QtCore.Qt.Unchecked)
                item_strategy_on_off.setText('关')
            elif dict_strategy_args['strategy_on_off'] == 1:
                item_strategy_on_off.setCheckState(QtCore.Qt.Checked)
                item_strategy_on_off.setText('开')
            # item_strategy_only_close = QtGui.QTableWidgetItem()  # 只平
            # if dict_strategy_args['only_close'] == 0:
            #     item_strategy_only_close.setCheckState(QtCore.Qt.Unchecked)
            #     item_strategy_only_close.setText('关')
            # elif dict_strategy_args['only_close'] == 1:
            #     item_strategy_only_close.setCheckState(QtCore.Qt.Checked)
            #     item_strategy_only_close.setText('开')
            item_user_id = QtGui.QTableWidgetItem(obj_strategy.get_user_id())  # 期货账号
            item_strategy_id = QtGui.QTableWidgetItem(obj_strategy.get_strategy_id())  # 策略编号
            # str_tmp = ''
            # for j in obj_strategy.get_list_instrument_id():
            #     str_tmp += j
            #     if j != obj_strategy.get_list_instrument_id()[-1]:
            #         str_tmp += ','
            str_tmp = obj_strategy.get_a_instrument_id() + obj_strategy.get_b_instrument_id()
            item_instrument_id = QtGui.QTableWidgetItem(str_tmp)  # 交易合约
            item_position = QtGui.QTableWidgetItem(str(dict_position['position_a_buy'] + dict_position['position_a_sell']))  # 总持仓
            item_position_buy = QtGui.QTableWidgetItem(str(dict_position['position_a_buy']))  # 买持仓
            item_position_sell = QtGui.QTableWidgetItem(str(dict_position['position_a_sell']))  # 卖持仓
            item_position_profit = QtGui.QTableWidgetItem('-')  # 持仓盈亏
            item_close_profit = QtGui.QTableWidgetItem('-')  # 平仓盈亏
            item_commission = QtGui.QTableWidgetItem('-')  # 手续费
            item_profit = QtGui.QTableWidgetItem('-')  # 净盈亏
            item_trade_count = QtGui.QTableWidgetItem('-')  # 成交量
            item_amount = QtGui.QTableWidgetItem('-')  # 成交金额
            item_a_trade_rate = QtGui.QTableWidgetItem('-')  # A成交率
            item_b_trade_rate = QtGui.QTableWidgetItem('-')  # B成交率
            item_trade_model = QtGui.QTableWidgetItem(dict_strategy_args['trade_model'])  # 交易模型
            item_order_algorithm = QtGui.QTableWidgetItem(dict_strategy_args['order_algorithm'])  # 下单算法
            self.tableWidget_Trade_Args.setItem(i_row, 0, item_strategy_on_off)  # 开关
            # self.tableWidget_Trade_Args.setItem(i_row, 1, item_strategy_only_close)  # 只平
            self.tableWidget_Trade_Args.setItem(i_row, 1, item_user_id)  # 期货账号
            self.tableWidget_Trade_Args.setItem(i_row, 2, item_strategy_id)  # 策略编号
            self.tableWidget_Trade_Args.setItem(i_row, 3, item_instrument_id)  # 交易合约
            self.tableWidget_Trade_Args.setItem(i_row, 4, item_position)  # 总持仓
            self.tableWidget_Trade_Args.setItem(i_row, 5, item_position_buy)  # 买持仓
            self.tableWidget_Trade_Args.setItem(i_row, 6, item_position_sell)  # 卖持仓
            self.tableWidget_Trade_Args.setItem(i_row, 7, item_position_profit)  # 持仓盈亏
            self.tableWidget_Trade_Args.setItem(i_row, 8, item_close_profit)  # 平仓盈亏
            self.tableWidget_Trade_Args.setItem(i_row, 9, item_commission)  # 手续费
            self.tableWidget_Trade_Args.setItem(i_row, 10, item_profit)  # 净盈亏
            self.tableWidget_Trade_Args.setItem(i_row, 11, item_trade_count)  # 成交量
            self.tableWidget_Trade_Args.setItem(i_row, 12, item_amount)  # 成交金额
            self.tableWidget_Trade_Args.setItem(i_row, 13, item_a_trade_rate)  # A成交率
            self.tableWidget_Trade_Args.setItem(i_row, 14, item_b_trade_rate)  # B成交率
            self.tableWidget_Trade_Args.setItem(i_row, 15, item_trade_model)  # 交易模型
            self.tableWidget_Trade_Args.setItem(i_row, 16, item_order_algorithm)  # 下单算法
            self.tableWidget_Trade_Args.setCurrentCell(i_row, 0)  # 设置当前行为“当前行”

            self.set_on_tableWidget_Trade_Args_cellClicked(i_row, 0)  # 触发鼠标左击单击该策略行

            # 绑定信号槽：向界面插入策略的时候，绑定策略对象与窗口对象之间的信号槽关系
            # 信号槽连接：策略对象修改策略 -> 窗口对象更新策略显示（Strategy.signal_update_strategy -> QAccountWidget.slot_update_strategy()）
            if self.is_single_user_widget():
                if self.__widget_name == obj_strategy.get_user_id():
                    # print(">>> QAccountWidget.slot_insert_strategy() 向界面插入策略时绑定信号槽，widget_id=", self.__widget_name, "user_id=", obj_strategy.get_user_id(), "strategy_id=", obj_strategy.get_strategy_id())
                    # 信号槽连接：策略对象的信号signal_update_spread_signal -> 所属的单账户窗口对象的槽函数slot_update_spread
                    obj_strategy.signal_update_spread_signal.connect(self.slot_update_spread)
                    # 信号槽连接：策略对象修改策略 -> 窗口对象更新策略显示（Strategy.signal_update_strategy -> QAccountWidget.slot_update_strategy()）
                    obj_strategy.signal_update_strategy.connect(self.slot_update_strategy)
                    # 信号槽连接：策略对象持仓发生变化 -> 界面刷新持仓显示（Strategy.signal_update_strategy_position -> QAccountWidget.slot_update_strategy_position）
                    obj_strategy.signal_update_strategy_position.connect(self.slot_update_strategy_position)
                    # 信号槽连接：策略对象修改持仓方法被调用 -> 窗口对象修改设置持仓按钮状态
                    obj_strategy.signal_pushButton_set_position_setEnabled.connect(self.slot_pushButton_set_position_setEnabled)
            # 策略与总账户窗口信号slot_update_spread连接
            else:
                # print(">>> QAccountWidget.slot_insert_strategy() 向界面插入策略时绑定信号槽，widget_id=", self.__widget_name, "user_id=", obj_strategy.get_user_id(), "strategy_id=", obj_strategy.get_strategy_id())
                # 信号槽连接：策略对象的信号signal_update_spread_total -> 总账户窗口对象的槽函数slot_update_spread
                obj_strategy.signal_update_spread_total.connect(self.slot_update_spread)
                # 信号槽连接：策略对象修改策略 -> 窗口对象更新策略显示（Strategy.signal_update_strategy -> QAccountWidget.slot_update_strategy()）
                obj_strategy.signal_update_strategy.connect(self.slot_update_strategy)
                # 信号槽连接：策略对象持仓发生变化 -> 界面刷新持仓显示（Strategy.signal_update_strategy_position -> QAccountWidget.slot_update_strategy_position）
                obj_strategy.signal_update_strategy_position.connect(self.slot_update_strategy_position)
                # 信号槽连接：策略对象修改持仓方法被调用 -> 窗口对象修改设置持仓按钮状态
                obj_strategy.signal_pushButton_set_position_setEnabled.connect(self.slot_pushButton_set_position_setEnabled)
                # 界面初始化完成状态、即程序运行中添加策略成功，弹窗提醒
                if self.__ctp_manager.get_init_UI_finished():
                    QMessageBox().showMessage("通知", "新建策略成功，期货账号" + obj_strategy.get_user_id() + "策略编号" + obj_strategy.get_strategy_id())
    """

    # 向界面插入策略，形参是任何策略对象，所有策略数量有增加时调用该方法
    # 形参dict{'user_id': '012345', 'strategy_id': '01'}
    def slot_insert_strategy(self, dict_strategy_arguments):
        # 总账户窗口或策略所属的单账户窗口
        i_row = self.tableWidget_Trade_Args.rowCount()  # 将要出入到的行标
        self.tableWidget_Trade_Args.insertRow(i_row)  # 在tableWidget中插入行
        print(">>> QAccountWidget.slot_insert_strategy() user_id =", dict_strategy_arguments['user_id'], "strategy_id =", dict_strategy_arguments['strategy_id'], "i_row =", i_row, " dict_strategy_arguments =", dict_strategy_arguments)
        item_strategy_on_off = QtGui.QTableWidgetItem()  # 开关
        item_strategy_on_off.setCheckState(QtCore.Qt.Unchecked)
        item_strategy_on_off.setText('关')
        item_user_id = QtGui.QTableWidgetItem(dict_strategy_arguments['user_id'])  # 期货账号
        item_strategy_id = QtGui.QTableWidgetItem(dict_strategy_arguments['strategy_id'])  # 策略编号
        str_instruments = ','.join([dict_strategy_arguments['a_instrument_id'], dict_strategy_arguments['b_instrument_id']])
        item_instrument_id = QtGui.QTableWidgetItem(str_instruments)  # 交易合约
        # item_position = QtGui.QTableWidgetItem(
        #     str(dict_strategy_position['position_a_buy'] + dict_strategy_position['position_a_sell']))  # 总持仓
        # item_position_buy = QtGui.QTableWidgetItem(str(dict_strategy_position['position_a_buy']))  # 买持仓
        # item_position_sell = QtGui.QTableWidgetItem(str(dict_strategy_position['position_a_sell']))  # 卖持仓
        # item_position_profit = QtGui.QTableWidgetItem(str(dict_strategy_statistics['position_profit']))  # 持仓盈亏
        # item_close_profit = QtGui.QTableWidgetItem(str(dict_strategy_statistics['close_profit']))  # 平仓盈亏
        # item_commission = QtGui.QTableWidgetItem(str(dict_strategy_statistics['commission']))  # 手续费
        # item_profit = QtGui.QTableWidgetItem(str(dict_strategy_statistics['profit']))  # 净盈亏
        # traded_count = str(dict_strategy_statistics['a_traded_count'] + dict_strategy_statistics['b_traded_count'])
        # item_trade_count = QtGui.QTableWidgetItem(traded_count)  # 成交量
        # traded_amount = str(dict_strategy_statistics['a_traded_mount'] + dict_strategy_statistics['b_traded_mount'])
        # item_amount = QtGui.QTableWidgetItem(traded_amount)  # 成交金额
        # item_a_trade_rate = QtGui.QTableWidgetItem(str(dict_strategy_statistics['a_trade_rate']))  # A成交率
        # item_b_trade_rate = QtGui.QTableWidgetItem(str(dict_strategy_statistics['b_trade_rate']))  # B成交率
        # item_trade_model = QtGui.QTableWidgetItem(dict_strategy_arguments['trade_model'])  # 交易模型
        # item_order_algorithm = QtGui.QTableWidgetItem(dict_strategy_arguments['order_algorithm'])  # 下单算法
        item_position = QtGui.QTableWidgetItem('0')  # 总持仓
        item_position_buy = QtGui.QTableWidgetItem('0')  # 买持仓
        item_position_sell = QtGui.QTableWidgetItem('0')  # 卖持仓
        item_position_profit = QtGui.QTableWidgetItem('0')  # 持仓盈亏
        item_close_profit = QtGui.QTableWidgetItem('0')  # 平仓盈亏
        item_commission = QtGui.QTableWidgetItem('0')  # 手续费
        item_profit = QtGui.QTableWidgetItem('0')  # 净盈亏
        item_trade_count = QtGui.QTableWidgetItem('0')  # 成交量
        item_amount = QtGui.QTableWidgetItem('0')  # 成交金额
        item_a_trade_rate = QtGui.QTableWidgetItem('0.0')  # A成交率
        item_b_trade_rate = QtGui.QTableWidgetItem('0.0')  # B成交率
        item_trade_model = QtGui.QTableWidgetItem('')  # 交易模型
        item_order_algorithm = QtGui.QTableWidgetItem('')  # 下单算法
        self.tableWidget_Trade_Args.setItem(i_row, 0, item_strategy_on_off)  # 开关
        self.tableWidget_Trade_Args.setItem(i_row, 1, item_user_id)  # 期货账号
        self.tableWidget_Trade_Args.setItem(i_row, 2, item_strategy_id)  # 策略编号
        self.tableWidget_Trade_Args.setItem(i_row, 3, item_instrument_id)  # 交易合约
        self.tableWidget_Trade_Args.setItem(i_row, 4, item_position)  # 总持仓
        self.tableWidget_Trade_Args.setItem(i_row, 5, item_position_buy)  # 买持仓
        self.tableWidget_Trade_Args.setItem(i_row, 6, item_position_sell)  # 卖持仓
        self.tableWidget_Trade_Args.setItem(i_row, 7, item_position_profit)  # 持仓盈亏
        self.tableWidget_Trade_Args.setItem(i_row, 8, item_close_profit)  # 平仓盈亏
        self.tableWidget_Trade_Args.setItem(i_row, 9, item_commission)  # 手续费
        self.tableWidget_Trade_Args.setItem(i_row, 10, item_profit)  # 净盈亏
        self.tableWidget_Trade_Args.setItem(i_row, 11, item_trade_count)  # 成交量
        self.tableWidget_Trade_Args.setItem(i_row, 12, item_amount)  # 成交金额
        self.tableWidget_Trade_Args.setItem(i_row, 13, item_a_trade_rate)  # A成交率
        self.tableWidget_Trade_Args.setItem(i_row, 14, item_b_trade_rate)  # B成交率
        self.tableWidget_Trade_Args.setItem(i_row, 15, item_trade_model)  # 交易模型
        self.tableWidget_Trade_Args.setItem(i_row, 16, item_order_algorithm)  # 下单算法

        # self.tableWidget_Trade_Args.setCurrentCell(i_row, 0)  # 设置当前行为“当前行”
        # self.set_on_tableWidget_Trade_Args_cellClicked(i_row, 0)  # 触发鼠标左击单击该策略行

    """
    # 从界面删除策略
    @QtCore.pyqtSlot(object)
    def slot_remove_strategy(self, obj_strategy):
        # 总账户窗口或策略所属的单账户窗口
        if self.is_single_user_widget() is False or obj_strategy.get_user_id() == self.__widget_name:
            for i_row in range(self.tableWidget_Trade_Args.rowCount()):
                # 在table中找到对应的策略行，更新界面显示，跳出for
                if self.tableWidget_Trade_Args.item(i_row, 2).text() == obj_strategy.get_user_id() and self.tableWidget_Trade_Args.item(i_row, 3).text() == obj_strategy.get_strategy_id():
                    # print(">>> QAccountWidget.remove_strategy() 删除策略，widget_name=", self.__widget_name, "user_id=", obj_strategy.get_user_id(), "strategy_id=", obj_strategy.get_strategy_id())
                    self.tableWidget_Trade_Args.removeRow(i_row)
                    if self.is_single_user_widget():
                        QMessageBox().showMessage("通知", "删除策略成功，期货账号"+obj_strategy.get_user_id()+"策略编号"+obj_strategy.get_strategy_id())
                    break
            # 如果tableWidget_Trade_Args中不存在策略，将groupBox中内容清空
            if self.tableWidget_Trade_Args.rowCount() == 0:
                # print(">>> QAccountWidget.slot_remove_strategy() widget_name=", self.__widget_name, "窗口中没有策略，清空groupBox")
                # 期货账号
                self.lineEdit_qihuozhanghao.setText('')
                # 策略编号
                self.lineEdit_celuebianhao.setText('')
                # 交易模型
                index_comboBox = self.comboBox_jiaoyimoxing.findText('')
                if index_comboBox != -1:
                    self.comboBox_jiaoyimoxing.setCurrentIndex(index_comboBox)
                # 下单算法
                index_comboBox = self.comboBox_xiadansuanfa.findText('')
                if index_comboBox != -1:
                    self.comboBox_xiadansuanfa.setCurrentIndex(index_comboBox)
                # 总手
                self.lineEdit_zongshou.setText('')
                # 每份
                self.lineEdit_meifen.setText('')
                # 止损
                self.spinBox_zhisun.setValue(0)
                # 超价触发
                self.spinBox_rangjia.setValue(0)
                # A等待
                self.spinBox_Adengdai.setValue(0)
                # B等待
                self.spinBox_Bdengdai.setValue(0)
                # 市场空头价差
                self.lineEdit_kongtoujiacha.setText('')
                # 持仓多头价差
                self.lineEdit_duotoujiacha.setText('')
                # A限制
                self.lineEdit_Achedanxianzhi.setText('')
                # B限制
                self.lineEdit_Bchedanxianzhi.setText('')
                # A撤单
                self.lineEdit_Achedan.setText('')
                # B撤单
                self.lineEdit_Bchedan.setText('')
                # 空头开
                self.doubleSpinBox_kongtoukai.setValue(0)
                self.doubleSpinBox_kongtoukai.setSingleStep(0)
                # 空头平
                self.doubleSpinBox_kongtouping.setValue(0)
                self.doubleSpinBox_kongtouping.setSingleStep(1)
                # 多头开
                self.doubleSpinBox_duotoukai.setValue(0)
                self.doubleSpinBox_duotoukai.setSingleStep(1)
                # 多头平
                self.doubleSpinBox_duotouping.setValue(0)
                self.doubleSpinBox_duotouping.setSingleStep(1)
                # 空头开-开关
                self.checkBox_kongtoukai.setCheckState(QtCore.Qt.Unchecked)
                # 空头平-开关
                self.checkBox_kongtouping.setCheckState(QtCore.Qt.Unchecked)
                # 多头开-开关
                self.checkBox_duotoukai.setCheckState(QtCore.Qt.Unchecked)
                # 多头平-开关
                self.checkBox_duotouping.setCheckState(QtCore.Qt.Unchecked)
                # A总卖
                self.lineEdit_Azongsell.setText('')
                # A昨卖
                self.lineEdit_Azuosell.setText('')
                # B总买
                self.lineEdit_Bzongbuy.setText('')
                # B昨买
                self.lineEdit_Bzuobuy.setText('')
                # A总买
                self.lineEdit_Azongbuy.setText('')
                # A昨买
                self.lineEdit_Azuobuy.setText('')
                # B总卖
                self.lineEdit_Bzongsell.setText('')
                # B昨卖
                self.lineEdit_Bzuosell.setText('')
                # 禁用groupBox中的按钮
                self.pushButton_set_strategy.setEnabled(False)
                self.pushButton_query_strategy.setEnabled(False)
                self.pushButton_set_position.setEnabled(False)
            # 如果tableWidget_Trade_Args中还存在策略，将主动触发clicked_table_widget事件，以更新groupBox显示
            elif self.tableWidget_Trade_Args.rowCount() > 0:
                self.set_on_tableWidget_Trade_Args_cellClicked(0, 0)
    """

    # 从界面删除策略
    @QtCore.pyqtSlot(object)
    def slot_remove_strategy(self, obj_strategy):
        # 总账户窗口或策略所属的单账户窗口
        if self.is_single_user_widget() is False or obj_strategy.get_user_id() == self.__widget_name:
            for i_row in range(self.tableWidget_Trade_Args.rowCount()):
                # 在table中找到对应的策略行，更新界面显示，跳出for
                if self.tableWidget_Trade_Args.item(i_row,
                                                    2).text() == obj_strategy.get_user_id() and self.tableWidget_Trade_Args.item(
                        i_row, 3).text() == obj_strategy.get_strategy_id():
                    # print(">>> QAccountWidget.remove_strategy() 删除策略，widget_name=", self.__widget_name, "user_id=", obj_strategy.get_user_id(), "strategy_id=", obj_strategy.get_strategy_id())
                    self.tableWidget_Trade_Args.removeRow(i_row)
                    if self.is_single_user_widget():
                        QMessageBox().showMessage("通知",
                                                  "删除策略成功，期货账号" + obj_strategy.get_user_id() + "策略编号" + obj_strategy.get_strategy_id())
                    break
            # 如果tableWidget_Trade_Args中不存在策略，将groupBox中内容清空
            if self.tableWidget_Trade_Args.rowCount() == 0:
                # print(">>> QAccountWidget.slot_remove_strategy() widget_name=", self.__widget_name, "窗口中没有策略，清空groupBox")
                # 期货账号
                self.lineEdit_qihuozhanghao.setText('')
                # 策略编号
                self.lineEdit_celuebianhao.setText('')
                # 交易模型
                index_comboBox = self.comboBox_jiaoyimoxing.findText('')
                if index_comboBox != -1:
                    self.comboBox_jiaoyimoxing.setCurrentIndex(index_comboBox)
                # 下单算法
                index_comboBox = self.comboBox_xiadansuanfa.findText('')
                if index_comboBox != -1:
                    self.comboBox_xiadansuanfa.setCurrentIndex(index_comboBox)
                # 总手
                self.lineEdit_zongshou.setText('')
                # 每份
                self.lineEdit_meifen.setText('')
                # 止损
                self.spinBox_zhisun.setValue(0)
                # 超价触发
                self.spinBox_rangjia.setValue(0)
                # A等待
                self.spinBox_Adengdai.setValue(0)
                # B等待
                self.spinBox_Bdengdai.setValue(0)
                # 市场空头价差
                self.lineEdit_kongtoujiacha.setText('')
                # 持仓多头价差
                self.lineEdit_duotoujiacha.setText('')
                # A限制
                self.lineEdit_Achedanxianzhi.setText('')
                # B限制
                self.lineEdit_Bchedanxianzhi.setText('')
                # A撤单
                self.lineEdit_Achedan.setText('')
                # B撤单
                self.lineEdit_Bchedan.setText('')
                # 空头开
                self.doubleSpinBox_kongtoukai.setValue(0)
                self.doubleSpinBox_kongtoukai.setSingleStep(0)
                # 空头平
                self.doubleSpinBox_kongtouping.setValue(0)
                self.doubleSpinBox_kongtouping.setSingleStep(1)
                # 多头开
                self.doubleSpinBox_duotoukai.setValue(0)
                self.doubleSpinBox_duotoukai.setSingleStep(1)
                # 多头平
                self.doubleSpinBox_duotouping.setValue(0)
                self.doubleSpinBox_duotouping.setSingleStep(1)
                # 空头开-开关
                self.checkBox_kongtoukai.setCheckState(QtCore.Qt.Unchecked)
                # 空头平-开关
                self.checkBox_kongtouping.setCheckState(QtCore.Qt.Unchecked)
                # 多头开-开关
                self.checkBox_duotoukai.setCheckState(QtCore.Qt.Unchecked)
                # 多头平-开关
                self.checkBox_duotouping.setCheckState(QtCore.Qt.Unchecked)
                # A总卖
                self.lineEdit_Azongsell.setText('')
                # A昨卖
                self.lineEdit_Azuosell.setText('')
                # B总买
                self.lineEdit_Bzongbuy.setText('')
                # B昨买
                self.lineEdit_Bzuobuy.setText('')
                # A总买
                self.lineEdit_Azongbuy.setText('')
                # A昨买
                self.lineEdit_Azuobuy.setText('')
                # B总卖
                self.lineEdit_Bzongsell.setText('')
                # B昨卖
                self.lineEdit_Bzuosell.setText('')
                # 禁用groupBox中的按钮
                self.pushButton_set_strategy.setEnabled(False)
                self.pushButton_query_strategy.setEnabled(False)
                self.pushButton_set_position.setEnabled(False)
            # 如果tableWidget_Trade_Args中还存在策略，将主动触发clicked_table_widget事件，以更新groupBox显示
            elif self.tableWidget_Trade_Args.rowCount() > 0:
                self.set_on_tableWidget_Trade_Args_cellClicked(0, 0)

    # 更新tableWidget_Trade_Args
    def update_tableWidget_Trade_Args(self):
        row_count = self.tableWidget_Trade_Args.rowCount()  # 将要出入到的行标
        if row_count == 0:
            return
        # 获取要更新的数据
        dict_user_process_data = self.__socket_manager.get_dict_user_process_data()
        list_update_data = list()  # list_update_data是要更新到界面的数据
        for user_id in dict_user_process_data:
            if self.__current_tab_name == "所有账户" or self.__current_tab_name == user_id:
                dict_strategy_arguments = dict_user_process_data[user_id]['running']['strategy_arguments']
                dict_strategy_position = dict_user_process_data[user_id]['running']['strategy_position']
                dict_strategy_statistics = dict_user_process_data[user_id]['running']['strategy_statistics']
                for strategy_id in dict_strategy_arguments:
                    dict_update_data_on_strategy = dict()
                    dict_update_data_on_strategy['strategy_on_off'] = dict_strategy_arguments[strategy_id]['on_off']
                    dict_update_data_on_strategy['user_id'] = dict_strategy_arguments[strategy_id]['user_id']
                    dict_update_data_on_strategy['strategy_id'] = dict_strategy_arguments[strategy_id]['strategy_id']
                    dict_update_data_on_strategy['trade_instrument'] = ','.join([dict_strategy_arguments[strategy_id]['a_instrument_id'],dict_strategy_arguments[strategy_id]['b_instrument_id']])
                    dict_update_data_on_strategy['trade_model'] = dict_strategy_arguments[strategy_id]['trade_model']
                    dict_update_data_on_strategy['order_algorithm'] = dict_strategy_arguments[strategy_id]['order_algorithm']
                    for i_strategy_id in dict_strategy_position:
                        if strategy_id == i_strategy_id:
                            dict_update_data_on_strategy['position'] = dict_strategy_position[strategy_id]['position_a_buy'] + dict_strategy_position[strategy_id]['position_a_sell']
                            dict_update_data_on_strategy['position_buy'] = dict_strategy_position[strategy_id]['position_a_buy']
                            dict_update_data_on_strategy['position_sell'] = dict_strategy_position[strategy_id]['position_a_sell']
                            break
                    for i_strategy_id in dict_strategy_statistics:
                        if strategy_id == i_strategy_id:
                            dict_update_data_on_strategy['profit_position'] = '待'  # 待续，需改为dict_strategy_statistics[strategy_id]['profit_position']
                            dict_update_data_on_strategy['profit_close'] = '待'  # 待续，需改为dict_strategy_statistics[strategy_id]['profit_close']
                            dict_update_data_on_strategy['profit'] = '待'  # 待续，需改为dict_strategy_statistics[strategy_id]['profit_close']
                            dict_update_data_on_strategy['commission'] = '待'  # 待续，需改为dict_strategy_statistics[strategy_id]['commission']
                            dict_update_data_on_strategy['total_traded_count'] = '待'  # 待续，需改为dict_strategy_statistics[strategy_id]['total_traded_count']
                            dict_update_data_on_strategy['total_traded_amount'] = '待'  # 待续，需改为dict_strategy_statistics[strategy_id]['total_traded_amount']
                            dict_update_data_on_strategy['a_trade_rate'] = dict_strategy_statistics[strategy_id]['a_trade_rate']
                            dict_update_data_on_strategy['b_trade_rate'] = dict_strategy_statistics[strategy_id]['b_trade_rate']
                            break
                    list_update_data.append(dict_update_data_on_strategy)
            # 将list_update_data更新到界面，数据样本如下：
            # >>>>>>>>>>>>>>>>> list_update_data = [{'total_traded_amount': '待', 'trade_instrument': 'rb1710,rb1705', 'position': 0, 'trade_model': '', 'total_traded_count': '待', 'commission': '待', 'a_trade_rate': 0.0, 'profit_position': '待', 'order_algorithm': '01', 'position_sell': 0, 'strategy_on_off': 1, 'user_id': '083778', 'profit_close': 0, 'position_buy': 0, 'strategy_id': '01', 'b_trade_rate': 0.0}, {'total_traded_amount': '待', 'trade_instrument': 'rb1710,rb1705', 'position': 0, 'trade_model': '', 'total_traded_count': '待', 'commission': '待', 'a_trade_rate': 0.0, 'profit_position': '待', 'order_algorithm': '01', 'position_sell': 0, 'strategy_on_off': 1, 'user_id': '083778', 'profit_close': 0, 'position_buy': 0, 'strategy_id': '02', 'b_trade_rate': 0.0}, {'total_traded_amount': '待', 'trade_instrument': 'rb1710,rb1705', 'position': 0, 'trade_model': '', 'total_traded_count': '待', 'commission': '待', 'a_trade_rate': 0.0, 'profit_position': '待', 'order_algorithm': '01', 'position_sell': 0, 'strategy_on_off': 1, 'user_id': '078681', 'profit_close': 0, 'position_buy': 0, 'strategy_id': '01', 'b_trade_rate': 0.0}, {'total_traded_amount': '待', 'trade_instrument': 'rb1710,rb1705', 'position': 0, 'trade_model': '', 'total_traded_count': '待', 'commission': '待', 'a_trade_rate': 0.0, 'profit_position': '待', 'order_algorithm': '01', 'position_sell': 0, 'strategy_on_off': 1, 'user_id': '078681', 'profit_close': 0, 'position_buy': 0, 'strategy_id': '02', 'b_trade_rate': 0.0}]

        # 遍历需要更新到界面的数据
        print(">>> QAccountWidget.update_tableWidget_Trade_Args() 界面更新数据list_update_data =", list_update_data)
        for i in range(len(list_update_data)):
            dict_strategy_data = list_update_data[i]
            self.update_tableWidget_Trade_Args_one(i, dict_strategy_data)  # 更新策略列表中的单行，形参：行标、数据

        # 清空多余的行
        if row_count > len(list_update_data):
            for i in range(len(list_update_data), row_count, 1):
                self.clean_tableWidget_Trade_Args_one(i)
                # print(">>> QAccountWidget.update_tableWidget_Trade_Args() 清除行数 =", i)

    # 更新策略列表中的单行，形参：行标、数据
    def update_tableWidget_Trade_Args_one(self, row, data):
        # 开关
        item_on_off = self.tableWidget_Trade_Args.item(row, 0)
        if data['strategy_on_off'] == 0:
            item_on_off.setText("关")
            item_on_off.setCheckState(QtCore.Qt.Unchecked)
        elif data['strategy_on_off'] == 1:
            item_on_off.setText("开")
            item_on_off.setCheckState(QtCore.Qt.Checked)
        else:
            print(">>> QAccountWidget.update_tableWidget_Trade_Args_one() user_id=", data['user_id'], "strategy_id=",
                  data['strategy_id'], "策略参数strategy_on_off值异常", data['strategy_on_off'])
        if self.__item_on_off_status is not None:
            if self.__item_on_off_status['enable'] == 0:
                item_on_off.setFlags(item_on_off.flags() ^ (QtCore.Qt.ItemIsEnabled))  # 激活item
                self.__item_on_off_status['enable'] = 1  # 0禁用、1激活
        # 期货账号
        self.tableWidget_Trade_Args.item(row, 1).setText(data['user_id'])
        # 策略编号
        self.tableWidget_Trade_Args.item(row, 2).setText(data['strategy_id'])
        # 交易合约
        # trade_instrument = ','.join([data['a_instrument_id'], data['a_instrument_id']])
        self.tableWidget_Trade_Args.item(row, 3).setText(data['trade_instrument'])
        # 总持仓
        self.tableWidget_Trade_Args.item(row, 4).setText(str(data['position']))
        # 买持仓
        self.tableWidget_Trade_Args.item(row, 5).setText(str(data['position_buy']))
        # 卖持仓
        self.tableWidget_Trade_Args.item(row, 6).setText(str(data['position_sell']))
        # 持仓盈亏
        self.tableWidget_Trade_Args.item(row, 7).setText(str(data['profit_position']))
        # 平仓盈亏
        self.tableWidget_Trade_Args.item(row, 8).setText(str(data['profit_close']))
        # 手续费
        self.tableWidget_Trade_Args.item(row, 9).setText(str(data['commission']))
        # 净盈亏
        self.tableWidget_Trade_Args.item(row, 10).setText(str(data['profit']))
        # 成交量
        self.tableWidget_Trade_Args.item(row, 11).setText(str(data['total_traded_count']))
        # 成交金额
        self.tableWidget_Trade_Args.item(row, 12).setText(str(data['total_traded_amount']))
        # A成交率
        self.tableWidget_Trade_Args.item(row, 13).setText(str(data['a_trade_rate']))
        # B成交率
        self.tableWidget_Trade_Args.item(row, 14).setText(str(data['b_trade_rate']))
        # 交易模型
        self.tableWidget_Trade_Args.item(row, 15).setText(str(data['trade_model']))
        # 下单算法
        self.tableWidget_Trade_Args.item(row, 16).setText(str(data['order_algorithm']))

    # 清空策略列表中的单行数据
    def clean_tableWidget_Trade_Args_one(self, row):
        # 开关
        self.tableWidget_Trade_Args.setItem(row, 0, QtGui.QTableWidgetItem())  # 开关
        # 期货账号
        self.tableWidget_Trade_Args.item(row, 1).setText('')
        # 策略编号
        self.tableWidget_Trade_Args.item(row, 2).setText('')
        # 交易合约
        self.tableWidget_Trade_Args.item(row, 3).setText('')
        # 总持仓
        self.tableWidget_Trade_Args.item(row, 4).setText('')
        # 买持仓
        self.tableWidget_Trade_Args.item(row, 5).setText('')
        # 卖持仓
        self.tableWidget_Trade_Args.item(row, 6).setText('')
        # 持仓盈亏
        self.tableWidget_Trade_Args.item(row, 7).setText('')
        # 平仓盈亏
        self.tableWidget_Trade_Args.item(row, 8).setText('')
        # 手续费
        self.tableWidget_Trade_Args.item(row, 9).setText('')
        # 净盈亏
        self.tableWidget_Trade_Args.item(row, 10).setText('')
        # 成交量
        self.tableWidget_Trade_Args.item(row, 11).setText('')
        # 成交金额
        self.tableWidget_Trade_Args.item(row, 12).setText('')
        # A成交率
        self.tableWidget_Trade_Args.item(row, 13).setText('')
        # B成交率
        self.tableWidget_Trade_Args.item(row, 14).setText('')
        # 交易模型
        self.tableWidget_Trade_Args.item(row, 15).setText('')
        # 下单算法
        self.tableWidget_Trade_Args.item(row, 16).setText('')

    # 更新单个策略的界面显示，调用情景：鼠标点击tableWidget、发送参数、发送持仓、查询、插入策略
    @QtCore.pyqtSlot(object)
    def slot_update_strategy(self, obj_strategy):
        if self.tableWidget_Trade_Args.rowCount() == 0:
            return
        dict_strategy_args = obj_strategy.get_arguments()  # 策略参数
        dict_strategy_position = obj_strategy.get_position()  # 策略持仓
        dict_strategy_statistics = obj_strategy.get_dict_statistics()  # 交易统计数据
        print(">>> QAccountWidget.slot_update_strategy() "
              "widget_name=", self.__widget_name,
              "user_id=", obj_strategy.get_user_id(),
              "strategy_id=", obj_strategy.get_strategy_id(),
              "self.sender()=", self.sender(),
              "dict_strategy_args=", dict_strategy_args)
        """更新tableWidget"""
        for i_row in range(self.tableWidget_Trade_Args.rowCount()):
            # 在table中找到对应的策略行，更新界面显示，跳出for
            if self.tableWidget_Trade_Args.item(i_row, 2).text() == obj_strategy.get_user_id() and self.tableWidget_Trade_Args.item(i_row, 3).text() == obj_strategy.get_strategy_id():
                # print(">>> QAccountWidget.slot_update_strategy() 更新tableWidget，widget_name=", self.__widget_name, "user_id=", obj_strategy.get_user_id(), "strategy_id=", obj_strategy.get_strategy_id())
                # 开关
                item_on_off = self.tableWidget_Trade_Args.item(i_row, 0)
                if dict_strategy_args['strategy_on_off'] == 0:
                    # print(">>> QAccountWidget.slot_update_strategy() 更新tableWidget，widget_name=", self.__widget_name, "user_id=", obj_strategy.get_user_id(), "strategy_id=", obj_strategy.get_strategy_id(), "策略开关设置：关")
                    item_on_off.setText("关")
                    item_on_off.setCheckState(QtCore.Qt.Unchecked)
                elif dict_strategy_args['strategy_on_off'] == 1:
                    # print(">>> QAccountWidget.slot_update_strategy() 更新tableWidget，widget_name=", self.__widget_name, "user_id=", obj_strategy.get_user_id(), "strategy_id=", obj_strategy.get_strategy_id(), "策略开关设置：开")
                    item_on_off.setText("开")
                    item_on_off.setCheckState(QtCore.Qt.Checked)
                else:
                    print("QAccountWidget.slot_update_strategy() user_id=", obj_strategy.get_user_id(), "strategy_id=", obj_strategy.get_strategy_id(), "策略参数strategy_on_off值异常", dict_strategy_args['strategy_on_off'])
                if self.__item_on_off_status is not None:
                    if self.__item_on_off_status['enable'] == 0:
                        item_on_off.setFlags(item_on_off.flags() ^ (QtCore.Qt.ItemIsEnabled))  # 激活item
                        self.__item_on_off_status['enable'] = 1  # 0禁用、1激活
                # 只平
                # item_only_close = self.tableWidget_Trade_Args.item(i_row, 1)
                # if dict_strategy_args['only_close'] == 0:
                #     item_only_close.setText("关")
                #     item_only_close.setCheckState(QtCore.Qt.Unchecked)
                # elif dict_strategy_args['only_close'] == 1:
                #     item_only_close.setText("开")
                #     item_only_close.setCheckState(QtCore.Qt.Checked)
                # else:
                #     print("QAccountWidget.slot_update_strategy() user_id=", obj_strategy.get_user_id(), "strategy_id=", obj_strategy.get_strategy_id(), "策略参数only_close值异常", dict_strategy_args['only_close'])
                # if self.__item_only_close_status is not None:
                #     if self.__item_only_close_status['enable'] == 0:
                #         item_only_close.setFlags(item_only_close.flags() ^ (QtCore.Qt.ItemIsEnabled))  # 激活item
                #         self.__item_only_close_status['enable'] = 1  # 0禁用、1激活
                # 总持仓
                item_position = self.tableWidget_Trade_Args.item(i_row, 5)
                item_position.setText(
                    str(dict_strategy_position['position_a_buy'] + dict_strategy_position['position_a_sell']))
                # 买持仓
                item_position_buy = self.tableWidget_Trade_Args.item(i_row, 6)
                item_position_buy.setText(
                    str(dict_strategy_position['position_a_buy']))
                # 卖持仓
                item_position_sell = self.tableWidget_Trade_Args.item(i_row, 7)
                item_position_sell.setText(
                    str(dict_strategy_position['position_a_sell']))
                # 持仓盈亏，策略有持仓的时候由行情驱动更新，可以设计为定时任务，待续，2017年2月17日15:29:48
                item_profit_position = self.tableWidget_Trade_Args.item(i_row, 8)
                item_profit_position.setText('-')
                # 平仓盈亏
                item_profit_close = self.tableWidget_Trade_Args.item(i_row, 9)
                item_profit_close.setText(
                    str(int(dict_strategy_statistics['profit_close'])))
                # 手续费
                item_commission = self.tableWidget_Trade_Args.item(i_row, 10)
                item_commission.setText(
                    str(int(dict_strategy_statistics['commission'])))
                # 净盈亏
                item_profit = self.tableWidget_Trade_Args.item(i_row, 11)
                item_profit.setText(
                    str(int(dict_strategy_statistics['profit'])))
                # 成交量
                item_volume = self.tableWidget_Trade_Args.item(i_row, 12)
                item_volume.setText(
                    str(dict_strategy_statistics['volume']))
                # 成交金额
                item_amount = self.tableWidget_Trade_Args.item(i_row, 13)
                item_amount.setText(
                    str(int(dict_strategy_statistics['amount'])))
                # A成交率
                item_A_traded_rate = self.tableWidget_Trade_Args.item(i_row, 14)
                item_A_traded_rate.setText(
                    str(dict_strategy_statistics['A_traded_rate']))
                # B成交率
                item_B_traded_rate = self.tableWidget_Trade_Args.item(i_row, 15)
                item_B_traded_rate.setText(
                    str(dict_strategy_statistics['B_traded_rate']))
                # 交易模型
                item_trade_model = self.tableWidget_Trade_Args.item(i_row, 16)
                item_trade_model.setText(dict_strategy_args['trade_model'])
                # 下单算法
                item_order_algorithm = self.tableWidget_Trade_Args.item(i_row, 17)
                item_order_algorithm.setText(dict_strategy_args['order_algorithm'])

                break  # 在tableWidget中找到对应的策略行，结束for循环
        """更新groupBox"""
        if self.__clicked_strategy == obj_strategy:  # 只更新在当前窗口中被鼠标选中的策略
            # print(">>> QAccountWidget.slot_update_strategy() 更新groupBox，widget_name=", self.__widget_name, "user_id=", obj_strategy.get_user_id(), "strategy_id=", obj_strategy.get_strategy_id())
            # 期货账号
            self.lineEdit_qihuozhanghao.setText(dict_strategy_args['user_id'])
            # 策略编号
            self.lineEdit_celuebianhao.setText(dict_strategy_args['strategy_id'])
            # 交易模型
            index_comboBox = self.comboBox_jiaoyimoxing.findText(dict_strategy_args['trade_model'])
            if index_comboBox != -1:
                self.comboBox_jiaoyimoxing.setCurrentIndex(index_comboBox)
            # 下单算法
            index_comboBox = self.comboBox_xiadansuanfa.findText(dict_strategy_args['order_algorithm'])
            if index_comboBox != -1:
                self.comboBox_xiadansuanfa.setCurrentIndex(index_comboBox)
            # 总手
            self.lineEdit_zongshou.setText(str(dict_strategy_args['lots']))
            # 每份
            self.lineEdit_meifen.setText(str(dict_strategy_args['lots_batch']))
            # 止损
            self.spinBox_zhisun.setValue(dict_strategy_args['stop_loss'])
            # 超价触发
            self.spinBox_rangjia.setValue(dict_strategy_args['spread_shift'])
            # A报价偏移
            self.spinBox_Abaodanpianyi.setValue(dict_strategy_args['a_limit_price_shift'])
            # B报价偏移
            self.spinBox_Bbaodanpianyi.setValue(dict_strategy_args['b_limit_price_shift'])
            # A撤单等待
            self.spinBox_Adengdai.setValue(dict_strategy_args['a_wait_price_tick'])
            # B撤单等待
            self.spinBox_Bdengdai.setValue(dict_strategy_args['b_wait_price_tick'])
            # A限制
            self.lineEdit_Achedanxianzhi.setText(str(dict_strategy_args['a_order_action_limit']))
            # B限制
            self.lineEdit_Bchedanxianzhi.setText(str(dict_strategy_args['b_order_action_limit']))
            # A撤单
            self.lineEdit_Achedan.setText(str(obj_strategy.get_a_action_count()))
            # B撤单
            self.lineEdit_Bchedan.setText(str(obj_strategy.get_b_action_count()))
            # 空头开
            self.doubleSpinBox_kongtoukai.setValue(dict_strategy_args['sell_open'])
            self.doubleSpinBox_kongtoukai.setSingleStep(obj_strategy.get_a_price_tick())
            # 空头平
            self.doubleSpinBox_kongtouping.setValue(dict_strategy_args['buy_close'])
            self.doubleSpinBox_kongtouping.setSingleStep(obj_strategy.get_a_price_tick())
            # 多头开
            self.doubleSpinBox_duotoukai.setValue(dict_strategy_args['buy_open'])
            self.doubleSpinBox_duotoukai.setSingleStep(obj_strategy.get_a_price_tick())
            # 多头平
            self.doubleSpinBox_duotouping.setValue(dict_strategy_args['sell_close'])
            self.doubleSpinBox_duotouping.setSingleStep(obj_strategy.get_a_price_tick())
            # 空头开-开关
            if dict_strategy_args['sell_open_on_off'] == 0:
                self.checkBox_kongtoukai.setCheckState(QtCore.Qt.Unchecked)
            elif dict_strategy_args['sell_open_on_off'] == 1:
                self.checkBox_kongtoukai.setCheckState(QtCore.Qt.Checked)
            # 空头平-开关
            if dict_strategy_args['buy_close_on_off'] == 0:
                self.checkBox_kongtouping.setCheckState(QtCore.Qt.Unchecked)
            elif dict_strategy_args['buy_close_on_off'] == 1:
                self.checkBox_kongtouping.setCheckState(QtCore.Qt.Checked)
            # 多头开-开关
            if dict_strategy_args['buy_open_on_off'] == 0:
                self.checkBox_duotoukai.setCheckState(QtCore.Qt.Unchecked)
            elif dict_strategy_args['buy_open_on_off'] == 1:
                self.checkBox_duotoukai.setCheckState(QtCore.Qt.Checked)
            # 多头平-开关
            if dict_strategy_args['sell_close_on_off'] == 0:
                self.checkBox_duotouping.setCheckState(QtCore.Qt.Unchecked)
            elif dict_strategy_args['sell_close_on_off'] == 1:
                self.checkBox_duotouping.setCheckState(QtCore.Qt.Checked)
            # A总卖
            self.lineEdit_Azongsell.setText(str(dict_strategy_position['position_a_sell']))
            # A昨卖
            self.lineEdit_Azuosell.setText(str(dict_strategy_position['position_a_sell_yesterday']))
            # B总买
            self.lineEdit_Bzongbuy.setText(str(dict_strategy_position['position_b_buy']))
            # B昨买
            self.lineEdit_Bzuobuy.setText(str(dict_strategy_position['position_b_buy_yesterday']))
            # A总买
            self.lineEdit_Azongbuy.setText(str(dict_strategy_position['position_a_buy']))
            # A昨买
            self.lineEdit_Azuobuy.setText(str(dict_strategy_position['position_a_buy_yesterday']))
            # B总卖
            self.lineEdit_Bzongsell.setText(str(dict_strategy_position['position_b_sell']))
            # B昨卖
            self.lineEdit_Bzuosell.setText(str(dict_strategy_position['position_b_sell_yesterday']))
            # A撤单
            self.lineEdit_Achedan.setText(str(obj_strategy.get_a_action_count()))
            # B撤单
            self.lineEdit_Bchedan.setText(str(obj_strategy.get_b_action_count()))

            # 恢复发送和设置持仓按钮状态
            self.slot_restore_groupBox_pushButton()

        # self.slot_update_strategy_position(obj_strategy)  # 调用slot_update_strategy是连带调用slot_update_strategy_position

    # 更新groupBox
    def update_groupBox(self):
        # 鼠标未点击任何策略之前，不更新groupBox
        if len(self.__dict_clicked_info[self.__current_tab_name]) == 0:
            return
        clicked_user_id = self.__dict_clicked_info[self.__current_tab_name]['user_id']
        clicked_strategy_id = self.__dict_clicked_info[self.__current_tab_name]['strategy_id']
        dict_user_data = self.__socket_manager.get_dict_user_process_data()[clicked_user_id]['running']  # 获取被选中的期货账户的所有数据
        print(">>> QAccountWidget.update_groupBox() clicked_user_id =", clicked_user_id, "clicked_strategy_id", clicked_strategy_id, "dict_user_data =", dict_user_data)
        dict_strategy_arguments = dict_user_data['strategy_arguments'][clicked_strategy_id]
        dict_strategy_statistics = dict_user_data['strategy_statistics'][clicked_strategy_id]
        dict_strategy_position = dict_user_data['strategy_position'][clicked_strategy_id]
        dict_instrument_statistics = dict_user_data['instrument_statistics']
        dict_trading_account = dict_user_data['trading_account']  # 期货账户资金情况
        a_instrument_id = dict_strategy_arguments['a_instrument_id']
        b_instrument_id = dict_strategy_arguments['b_instrument_id']
        # a_price_tick = dict_strategy_arguments['a_price_tick']
        # b_price_tick = dict_strategy_arguments['b_price_tick']
        a_action_count = dict_instrument_statistics[a_instrument_id]['action_count']  # A合约撤单次数
        b_action_count = dict_instrument_statistics[b_instrument_id]['action_count']  # B合约撤单次数

        self.lineEdit_qihuozhanghao.setText(clicked_user_id)  # 期货账号
        self.lineEdit_celuebianhao.setText(clicked_strategy_id)  # 策略编号
        index_comboBox = self.comboBox_jiaoyimoxing.findText(dict_strategy_arguments['trade_model'])  # 交易模型
        if index_comboBox != -1:
            self.comboBox_jiaoyimoxing.setCurrentIndex(index_comboBox)
        index_comboBox = self.comboBox_xiadansuanfa.findText(dict_strategy_arguments['order_algorithm'])  # 下单算法
        if index_comboBox != -1:
            self.comboBox_xiadansuanfa.setCurrentIndex(index_comboBox)
        self.lineEdit_zongshou.setText(str(dict_strategy_arguments['lots']))  # 总手
        self.lineEdit_meifen.setText(str(dict_strategy_arguments['lots_batch']))  # 每份
        self.spinBox_zhisun.setValue(dict_strategy_arguments['stop_loss'])  # 止损
        self.spinBox_rangjia.setValue(dict_strategy_arguments['spread_shift'])  # 超价触发
        self.spinBox_Abaodanpianyi.setValue(dict_strategy_arguments['a_limit_price_shift'])  # A报价偏移
        self.spinBox_Bbaodanpianyi.setValue(dict_strategy_arguments['b_limit_price_shift'])  # B报价偏移
        self.spinBox_Adengdai.setValue(dict_strategy_arguments['a_wait_price_tick'])  # A撤单等待
        self.spinBox_Bdengdai.setValue(dict_strategy_arguments['b_wait_price_tick'])  # B撤单等待
        self.lineEdit_Achedanxianzhi.setText(str(dict_strategy_arguments['a_order_action_limit']))  # A限制
        self.lineEdit_Bchedanxianzhi.setText(str(dict_strategy_arguments['b_order_action_limit']))  # B限制
        self.lineEdit_Achedan.setText(str(dict_strategy_statistics['a_action_count']))  # A撤单
        self.lineEdit_Bchedan.setText(str(dict_strategy_statistics['b_action_count']))  # B撤单
        self.doubleSpinBox_kongtoukai.setValue(dict_strategy_arguments['sell_open'])  # 空头开
        # self.doubleSpinBox_kongtoukai.setSingleStep(obj_strategy.get_a_price_tick())  # 设置step
        self.doubleSpinBox_kongtouping.setValue(dict_strategy_arguments['buy_close'])  # 空头平
        # self.doubleSpinBox_kongtouping.setSingleStep(obj_strategy.get_a_price_tick())  # 设置step
        self.doubleSpinBox_duotoukai.setValue(dict_strategy_arguments['buy_open'])  # 多头开
        # self.doubleSpinBox_duotoukai.setSingleStep(obj_strategy.get_a_price_tick())  # 设置step
        self.doubleSpinBox_duotouping.setValue(dict_strategy_arguments['sell_close'])  # 多头平
        # self.doubleSpinBox_duotouping.setSingleStep(obj_strategy.get_a_price_tick())  # 设置step
        # 空头开-开关
        if dict_strategy_arguments['sell_open_on_off'] == 0:
            self.checkBox_kongtoukai.setCheckState(QtCore.Qt.Unchecked)
        elif dict_strategy_arguments['sell_open_on_off'] == 1:
            self.checkBox_kongtoukai.setCheckState(QtCore.Qt.Checked)
        # 空头平-开关
        if dict_strategy_arguments['buy_close_on_off'] == 0:
            self.checkBox_kongtouping.setCheckState(QtCore.Qt.Unchecked)
        elif dict_strategy_arguments['buy_close_on_off'] == 1:
            self.checkBox_kongtouping.setCheckState(QtCore.Qt.Checked)
        # 多头开-开关
        if dict_strategy_arguments['buy_open_on_off'] == 0:
            self.checkBox_duotoukai.setCheckState(QtCore.Qt.Unchecked)
        elif dict_strategy_arguments['buy_open_on_off'] == 1:
            self.checkBox_duotoukai.setCheckState(QtCore.Qt.Checked)
        # 多头平-开关
        if dict_strategy_arguments['sell_close_on_off'] == 0:
            self.checkBox_duotouping.setCheckState(QtCore.Qt.Unchecked)
        elif dict_strategy_arguments['sell_close_on_off'] == 1:
            self.checkBox_duotouping.setCheckState(QtCore.Qt.Checked)
        self.lineEdit_Azongsell.setText(str(dict_strategy_position['position_a_sell']))  # A总卖
        self.lineEdit_Azuosell.setText(str(dict_strategy_position['position_a_sell_yesterday']))  # A昨卖
        self.lineEdit_Bzongbuy.setText(str(dict_strategy_position['position_b_buy']))  # B总买
        self.lineEdit_Bzuobuy.setText(str(dict_strategy_position['position_b_buy_yesterday']))  # B昨买
        self.lineEdit_Azongbuy.setText(str(dict_strategy_position['position_a_buy']))  # A总买
        self.lineEdit_Azuobuy.setText(str(dict_strategy_position['position_a_buy_yesterday']))  # A昨买
        self.lineEdit_Bzongsell.setText(str(dict_strategy_position['position_b_sell']))  # B总卖
        self.lineEdit_Bzuosell.setText(str(dict_strategy_position['position_b_sell_yesterday']))  # B昨卖
        self.lineEdit_Achedan.setText(str(a_action_count))  # A撤单
        self.lineEdit_Bchedan.setText(str(b_action_count))  # B撤单

    # 更新单个策略的界面显示，调用情景：所有调用self.slot_update_strategy()的时候、order回调、trade回调、撤单
    @QtCore.pyqtSlot(object)
    def slot_update_strategy_position(self, obj_strategy):
        dict_strategy_args = obj_strategy.get_arguments()  # 策略参数
        dict_strategy_position = obj_strategy.get_position()  # 策略持仓
        dict_strategy_statistics = obj_strategy.get_dict_statistics()  # 交易统计数据
        print(">>> QAccountWidget.slot_update_strategy_position() "
              "widget_name=", self.__widget_name,
              "user_id=", dict_strategy_args['user_id'],
              "strategy_id=", dict_strategy_args['strategy_id'],
              "self.sender()=", self.sender(),
              "dict_strategy_position=", dict_strategy_position)
        """更新tableWidget"""
        for i_row in range(self.tableWidget_Trade_Args.rowCount()):
            # 在table中找到对应的策略行，更新界面显示，跳出for
            if self.tableWidget_Trade_Args.item(i_row, 2).text() == obj_strategy.get_user_id() and self.tableWidget_Trade_Args.item(i_row, 3).text() == obj_strategy.get_strategy_id():
                # 总持仓
                item_position = self.tableWidget_Trade_Args.item(i_row, 5)
                item_position.setText(
                    str(dict_strategy_position['position_a_buy'] + dict_strategy_position['position_a_sell']))
                # 买持仓
                item_position_buy = self.tableWidget_Trade_Args.item(i_row, 6)
                item_position_buy.setText(
                    str(dict_strategy_position['position_a_buy'] + dict_strategy_position['position_a_buy']))
                # 卖持仓
                item_position_sell = self.tableWidget_Trade_Args.item(i_row, 7)
                item_position_sell.setText(
                    str(dict_strategy_position['position_a_buy'] + dict_strategy_position['position_a_sell']))
                # 持仓盈亏，策略有持仓的时候由行情驱动更新，可以设计为定时任务
                # 平仓盈亏
                item_profit_close = self.tableWidget_Trade_Args.item(i_row, 9)
                item_profit_close.setText(
                    str(dict_strategy_statistics['profit_close']))
                # 手续费
                item_commission = self.tableWidget_Trade_Args.item(i_row, 10)
                item_commission.setText(
                    str(dict_strategy_statistics['commission']))
                # 净盈亏
                item_profit = self.tableWidget_Trade_Args.item(i_row, 11)
                item_profit.setText(
                    str(dict_strategy_statistics['profit']))
                # 成交量
                item_volume = self.tableWidget_Trade_Args.item(i_row, 12)
                item_volume.setText(
                    str(dict_strategy_statistics['volume']))
                # 成交金额
                item_amount = self.tableWidget_Trade_Args.item(i_row, 13)
                item_amount.setText(
                    str(dict_strategy_statistics['amount']))
                # A成交率
                item_A_traded_rate = self.tableWidget_Trade_Args.item(i_row, 14)
                item_A_traded_rate.setText(
                    str(dict_strategy_statistics['A_traded_rate']))
                # B成交率
                item_B_traded_rate = self.tableWidget_Trade_Args.item(i_row, 15)
                item_B_traded_rate.setText(
                    str(dict_strategy_statistics['B_traded_rate']))

            break  # 在tableWidget中找到对应的策略行，结束for循环
        """更新groupBox"""
        if self.__clicked_strategy == obj_strategy:  # 只更新在当前窗口中被鼠标选中的策略
            # print(">>> QAccountWidget.slot_update_strategy() 更新groupBox，widget_name=", self.__widget_name, "user_id=", obj_strategy.get_user_id(), "strategy_id=", obj_strategy.get_strategy_id())
            # A总卖
            self.lineEdit_Azongsell.setText(str(dict_strategy_position['position_a_sell']))
            # A昨卖
            self.lineEdit_Azuosell.setText(str(dict_strategy_position['position_a_sell_yesterday']))
            # B总买
            self.lineEdit_Bzongbuy.setText(str(dict_strategy_position['position_b_buy']))
            # B昨买
            self.lineEdit_Bzuobuy.setText(str(dict_strategy_position['position_b_buy_yesterday']))
            # A总买
            self.lineEdit_Azongbuy.setText(str(dict_strategy_position['position_a_buy']))
            # A昨买
            self.lineEdit_Azuobuy.setText(str(dict_strategy_position['position_a_buy_yesterday']))
            # B总卖
            self.lineEdit_Bzongsell.setText(str(dict_strategy_position['position_b_sell']))
            # B昨卖
            self.lineEdit_Bzuosell.setText(str(dict_strategy_position['position_b_sell_yesterday']))
            # A撤单
            self.lineEdit_Achedan.setText(str(obj_strategy.get_a_action_count()))
            # B撤单
            self.lineEdit_Bchedan.setText(str(obj_strategy.get_b_action_count()))

    # 绑定信号槽：收到服务端的查询策略信息 -> groupBox界面状态还原（激活查询按钮、恢复“设置持仓”按钮）
    @QtCore.pyqtSlot()
    def slot_restore_groupBox_pushButton(self):
        self.pushButton_set_strategy.setEnabled(True)  # 激活按钮
        self.pushButton_query_strategy.setEnabled(True)
        self.pushButton_set_position.setEnabled(True)
        self.lineEdit_Azongsell.setEnabled(False)  # 禁用编辑框
        self.lineEdit_Azuosell.setEnabled(False)
        self.lineEdit_Bzongbuy.setEnabled(False)
        self.lineEdit_Bzuobuy.setEnabled(False)
        self.lineEdit_Azongbuy.setEnabled(False)
        self.lineEdit_Azuobuy.setEnabled(False)
        self.lineEdit_Bzongsell.setEnabled(False)
        self.lineEdit_Bzuosell.setEnabled(False)
        self.pushButton_set_position.setText("设置持仓")

    # 槽函数：维护“开始策略”按钮的状态，分别被一个总账户窗口信号和多个单期货账户窗口信号绑定
    @QtCore.pyqtSlot()
    def slot_update_pushButton_start_strategy(self):
        self.pushButton_start_strategy.setEnabled(True)  # 激活按钮
        # if self.is_single_user_widget():
        #     on_off = self.__user.get_on_off()  # 窗口对应的期货账户的交易开关
        #     if on_off == 1:
        #         self.pushButton_start_strategy.setText("关闭策略")
        #     elif on_off == 0:
        #         self.pushButton_start_strategy.setText("开始策略")
        # else:
        # on_off = self.__ctp_manager.get_on_off()  # 总账户窗口对应的交易员开关
        if self.is_single_user_widget():
            on_off = self.__user.get_on_off()
        else:
            on_off = self.__ctp_manager.get_on_off()
        if on_off == 1:
            self.pushButton_start_strategy.setText("关闭策略")
        elif on_off == 0:
            self.pushButton_start_strategy.setText("开始策略")


    @QtCore.pyqtSlot()
    def slot_pushButton_set_position_setEnabled(self):
        self.pushButton_set_position.setText("设置持仓")
        self.pushButton_set_position.setEnabled(True)  # 设置为可用

    # 初始化界面：策略统计类指标（统计代码在Strategy类中实现，界面层的类仅负责显示）
    def init_table_widget_statistics(self):
        for i_strategy in self.__client_main.get_CTPManager().get_list_strategy():  # 遍历所有策略
            for i_row in range(self.tableWidget_Trade_Args.rowCount()):  # 遍历行
                # 策略与行对应
                if self.tableWidget_Trade_Args.item(i_row, 2).text() == i_strategy.get_user_id() and self.tableWidget_Trade_Args.item(i_row, 3).text() == i_strategy.get_strategy_id():
                    position = i_strategy.get_position()['position_a_buy'] + i_strategy.get_position()['position_a_sell']
                    self.tableWidget_Trade_Args.item(i_row, 7).setText(str(position))

    # 更新界面：价差行情
    @QtCore.pyqtSlot(dict)
    def slot_update_spread(self, dict_input):
        # print(">>> QAccountWidget.slot_update_spread() 更新界面价差行情，widget_name=", self.__widget_name)
        # dict_input = {'spread_long': int, 'spread_short': int}
        # 更新多头价差显示
        if self.__spread_long is None:  # 初始值
            # self.lineEdit_duotoujiacha.setText(("%.2f" % dict_input['spread_long']))
            # self.lineEdit_duotoujiacha.setStyleSheet("color: rgb(0, 0, 0);")
            self.signal_lineEdit_duotoujiacha_setText.emit(("%.2f" % dict_input['spread_long']))
            self.signal_lineEdit_duotoujiacha_setStyleSheet.emit("color: rgb(0, 0, 0);")
        elif dict_input['spread_long'] > self.__spread_long:  # 最新值大于前值
            # self.lineEdit_duotoujiacha.setText(("%.2f" % dict_input['spread_long']))
            # self.lineEdit_duotoujiacha.setStyleSheet("color: rgb(255, 0, 0);font-weight:bold;")
            self.signal_lineEdit_duotoujiacha_setText.emit(("%.2f" % dict_input['spread_long']))
            self.signal_lineEdit_duotoujiacha_setStyleSheet.emit("color: rgb(255, 0, 0);font-weight:bold;")
        elif dict_input['spread_long'] < self.__spread_long:  # 最新值小于前值
            # self.lineEdit_duotoujiacha.setText(("%.2f" % dict_input['spread_long']))
            # self.lineEdit_duotoujiacha.setStyleSheet("color: rgb(0, 170, 0);font-weight:bold;")
            self.signal_lineEdit_duotoujiacha_setText.emit(("%.2f" % dict_input['spread_long']))
            self.signal_lineEdit_duotoujiacha_setStyleSheet.emit("color: rgb(0, 170, 0);font-weight:bold;")
        # 更新空头价差显示
        if self.__spread_short is None:  # 初始值
            # self.lineEdit_kongtoujiacha.setText(("%.2f" % dict_input['spread_short']))
            # self.lineEdit_kongtoujiacha.setStyleSheet("color: rgb(0, 0, 0);")
            self.signal_lineEdit_kongtoujiacha_setText.emit(("%.2f" % dict_input['spread_short']))
            self.signal_lineEdit_kongtoujiacha_setStyleSheet.emit("color: rgb(0, 0, 0);")
        elif dict_input['spread_short'] > self.__spread_short:  # 最新值大于前值
            # self.lineEdit_kongtoujiacha.setText(("%.2f" % dict_input['spread_short']))
            # self.lineEdit_kongtoujiacha.setStyleSheet("color: rgb(255, 0, 0);font-weight:bold;")
            self.signal_lineEdit_kongtoujiacha_setText.emit(("%.2f" % dict_input['spread_short']))
            self.signal_lineEdit_kongtoujiacha_setStyleSheet.emit("color: rgb(255, 0, 0);font-weight:bold;")
        elif dict_input['spread_short'] < self.__spread_short:  # 最新值小于前值
            # self.lineEdit_kongtoujiacha.setText(("%.2f" % dict_input['spread_short']))
            # self.lineEdit_kongtoujiacha.setStyleSheet("color: rgb(0, 170, 0);font-weight:bold;")
            self.signal_lineEdit_kongtoujiacha_setText.emit(("%.2f" % dict_input['spread_short']))
            self.signal_lineEdit_kongtoujiacha_setStyleSheet.emit("color: rgb(0, 170, 0);font-weight:bold;")
        self.__spread_long = dict_input['spread_long']  # 储存最后值，与后来的值比较，如果之变化就刷新界面
        self.__spread_short = dict_input['spread_short']

    # 点击“发送”按钮后的参数更新，要更新的策略为goupBox中显示的user_id、strategy_id对应的
    def update_groupBox_trade_args_for_set(self):
        # 遍历策略列表，找到与界面显示相同的策略对象实例
        for i_strategy in self.__client_main.get_CTPManager().get_list_strategy():
            if i_strategy.get_user_id() == self.comboBox_qihuozhanghao.currentText() and i_strategy.get_strategy_id() == self.comboBox_celuebianhao.currentText():
                dict_args = i_strategy.get_arguments()
                self.lineEdit_zongshou.setText(str(dict_args['lots']))  # 总手
                self.lineEdit_meifen.setText(str(dict_args['lots_batch']))  # 每份
                self.spinBox_zhisun.setValue(dict_args['stop_loss'])  # 止损
                self.spinBox_rangjia.setValue(dict_args['spread_shift'])  # 超价触发
                self.spinBox_Adengdai.setValue(dict_args['a_wait_price_tick'])  # A等待
                self.spinBox_Bdengdai.setValue(dict_args['b_wait_price_tick'])  # B等待
                self.lineEdit_Achedanxianzhi.setText(str(dict_args['a_order_action_limit']))  # A限制（撤单次数）
                self.lineEdit_Bchedanxianzhi.setText(str(dict_args['b_order_action_limit']))  # B限制（撤单次数）
                self.doubleSpinBox_kongtoukai.setValue(dict_args['sell_open'])  # 空头开（卖开价差）
                self.doubleSpinBox_kongtouping.setValue(dict_args['buy_close'])  # 空头平（买平价差）
                self.doubleSpinBox_duotoukai.setValue(dict_args['buy_open'])  # 多头开（买开价差）
                self.doubleSpinBox_duotouping.setValue(dict_args['sell_close'])  # 多头平（卖平价差）
                if dict_args['sell_open_on_off'] == 0:
                    self.checkBox_kongtoukai.setCheckState(QtCore.Qt.Unchecked)  # 空头开-开关
                elif dict_args['sell_open_on_off'] == 1:
                    self.checkBox_kongtoukai.setCheckState(QtCore.Qt.Checked)  # 空头开-开关
                if dict_args['buy_close_on_off'] == 0:
                    self.checkBox_kongtouping.setCheckState(QtCore.Qt.Unchecked)  # 空头平-开关
                elif dict_args['buy_close_on_off'] == 1:
                    self.checkBox_kongtouping.setCheckState(QtCore.Qt.Checked)  # 空头平-开关
                if dict_args['buy_open_on_off'] == 0:
                    self.checkBox_duotoukai.setCheckState(QtCore.Qt.Unchecked)  # 多头开-开关
                elif dict_args['buy_open_on_off'] == 1:
                    self.checkBox_duotoukai.setCheckState(QtCore.Qt.Checked)  # 多头开-开关
                if dict_args['sell_close_on_off'] == 0:
                    self.checkBox_duotouping.setCheckState(QtCore.Qt.Unchecked)  # 多头平-开关
                elif dict_args['sell_close_on_off'] == 1:
                    self.checkBox_duotouping.setCheckState(QtCore.Qt.Checked)  # 多头平-开关
                break

    # 更新界面：“账户资金”框，panel_show_account
    @QtCore.pyqtSlot(dict)
    def slot_update_panel_show_account(self, dict_args):
        print(">>> QAccountWidget.slot_update_panel_show_account() dict_args=", dict_args)
        """
        参数实例
        {
        'Capital': 1760786.59375,
        'PreBalance': 1760668.7,
        'PositionProfit': 200.0,
        'CloseProfit': 0.0,
        'Commission': 82.10625,
        'Available': 1629190.59375,
        'CurrMargin': 131396.0,
        'FrozenMargin': 0.0,
        'Risk': 0.07462346684510018
        'Deposit': 0.0,
        'Withdraw': 0.0,
        }
        """
        self.label_value_dongtaiquanyi.setText(str(int(dict_args['Capital'])))  # 动态权益
        self.label_value_jingtaiquanyi.setText(str(int(dict_args['PreBalance'])))  # 静态权益
        self.label_value_chicangyingkui.setText(str(int(dict_args['PositionProfit'])))  # 持仓盈亏
        self.label_value_pingcangyingkui.setText(str(int(dict_args['CloseProfit'])))  # 平仓盈亏
        self.label_value_shouxufei.setText(str(int(dict_args['Commission'])))  # 手续费
        self.label_value_keyongzijin.setText(str(int(dict_args['Available'])))  # 可用资金
        self.label_value_zhanyongbaozhengjin.setText(str(int(dict_args['CurrMargin'])))  # 占用保证金
        # self.label_value_xiadandongjie.setText(str(int(dict_args['FrozenMargin'])))  # 下单冻结
        self.label_value_fengxiandu.setText(str(int(dict_args['Risk']*100))+'%')  # 风险度
        self.label_value_jinrirujin.setText(str(int(dict_args['Deposit'])))  # 今日入金
        self.label_value_jinrichujin.setText(str(int(dict_args['Withdraw'])))  # 今日出金

    # 鼠标右击弹出菜单中的“添加策略”
    @pyqtSlot()
    def slot_action_add_strategy(self):
        # print(">>> QAccountWidget.slot_action_add_strategy() called")
        self.__client_main.get_QNewStrategy().update_comboBox_user_id_menu()  # 更新新建策略框中的期货账号可选项菜单
        self.__client_main.get_QNewStrategy().show()
        # todo...

    # 鼠标右击弹出菜单中的“删除策略”
    @pyqtSlot()
    def slot_action_del_strategy(self):
        print(">>> QAccountWidget.slot_action_del_strategy() widget_name=", self.__widget_name)
        # 没有任何策略的窗口点击“删除策略”，无任何响应
        if self.tableWidget_Trade_Args.rowCount() == 0:
            return
        # 鼠标点击信息为空，跳过
        if self.__clicked_item is None or self.__clicked_status is None:
            return
        # 找到将要删除的策略对象
        for i_strategy in self.__ctp_manager.get_list_strategy():
            print(">>> QAccountWidget.slot_action_del_strategy() i_strategy.get_user_id()=", i_strategy.get_user_id(), "i_strategy.get_strategy_id()=", i_strategy.get_strategy_id(), "self.__clicked_status['user_id']=", self.__clicked_status['user_id'], "self.__clicked_status['strategy_id']=", self.__clicked_status['strategy_id'])
            if i_strategy.get_user_id() == self.__clicked_status['user_id'] and i_strategy.get_strategy_id() == self.__clicked_status['strategy_id']:
                print(">>> QAccountWidget.slot_action_del_strategy() 找到将要删除的策略，user_id=", i_strategy.get_user_id(), "strategy_id=", i_strategy.get_strategy_id())
                # 判断持仓：有持仓，跳出
                dict_position = i_strategy.get_position()
                for i in dict_position:
                    if dict_position[i] != 0:
                        print("QAccountWidgetslot_action_del_strategy() 不能删除有持仓的策略，user_id=", i_strategy.get_user_id(), "strategy_id=", i_strategy.get_strategy_id())
                        QMessageBox().showMessage("错误", "不能删除有持仓的策略")
                        return
                # 策略开关的状态为开，跳过
                if i_strategy.get_on_off() == 1:
                    print("QAccountWidgetslot_action_del_strategy() 不能删除交易开关为开的策略，user_id=", i_strategy.get_user_id(), "strategy_id=", i_strategy.get_strategy_id())
                    QMessageBox().showMessage("错误", "不能删除交易开关为开的策略")
                    return

                # 向服务端发送删除策略指令
                dict_delete_strategy = {'MsgRef': self.__client_main.get_SocketManager().msg_ref_add(),
                                        'MsgSendFlag': 0,  # 发送标志，客户端发出0，服务端发出1
                                        'MsgSrc': 0,  # 消息源，客户端0，服务端1
                                        'MsgType': 7,  # 删除策略
                                        'TraderID': i_strategy.get_trader_id(),
                                        'UserID': i_strategy.get_user_id(),
                                        'StrategyID': i_strategy.get_strategy_id()
                                        }
                json_delete_strategy = json.dumps(dict_delete_strategy)
                self.signal_send_msg.emit(json_delete_strategy)
                break  # 找到对应的策略对象，跳出for循环
        # todo...

    @pyqtSlot()
    def on_pushButton_query_account_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        # raise NotImplementedError
    
    @pyqtSlot()
    def on_pushButton_only_close_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        # raise NotImplementedError
    
    @pyqtSlot()
    def on_pushButton_start_strategy_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        # raise NotImplementedError
        if self.is_single_user_widget():
            on_off = self.__user.get_on_off()
        else:
            on_off = self.__ctp_manager.get_on_off()
        print(">>> QAccountWidget.on_pushButton_start_strategy_clicked() 按钮状态：", self.pushButton_start_strategy.text(), on_off)
        if self.pushButton_start_strategy.text() == '开始策略' and on_off == 0:
            self.pushButton_start_strategy.setEnabled(False)  # 将按钮禁用
            # 发送开始策略命令：将期货账户开关修改为开，值为1
            if self.is_single_user_widget():
                dict_trade_onoff = {
                    'MsgRef': self.__socket_manager.msg_ref_add(),
                    'MsgSendFlag': 0,  # 发送标志，客户端发出0，服务端发出1
                    'MsgSrc': 0,  # 消息源，客户端0，服务端1
                    'MsgType': 9,  # 单个期货账户交易开关
                    'TraderID': self.__ctp_manager.get_trader_id(),
                    'UserID': self.__widget_name,
                    'OnOff': 1}
            else:
                dict_trade_onoff = {
                    'MsgRef': self.__socket_manager.msg_ref_add(),
                    'MsgSendFlag': 0,  # 发送标志，客户端发出0，服务端发出1
                    'MsgSrc': 0,  # 消息源，客户端0，服务端1
                    'MsgType': 8,  # 交易员交易开关
                    'TraderID': self.__ctp_manager.get_trader_id(),
                    'OnOff': 1}
            json_trade_onoff = json.dumps(dict_trade_onoff)
            self.signal_send_msg.emit(json_trade_onoff)
        elif self.pushButton_start_strategy.text() == '关闭策略' and on_off == 1:
            self.pushButton_start_strategy.setEnabled(False)  # 将按钮禁用
            # 发送关闭策略命令：将期货账户开关修改为关，值为0
            if self.is_single_user_widget():
                dict_trade_onoff = {
                    'MsgRef': self.__socket_manager.msg_ref_add(),
                    'MsgSendFlag': 0,  # 发送标志，客户端发出0，服务端发出1
                    'MsgSrc': 0,  # 消息源，客户端0，服务端1
                    'MsgType': 9,  # 单个期货账户交易开关
                    'TraderID': self.__ctp_manager.get_trader_id(),
                    'UserID': self.__widget_name,
                    'OnOff': 0}
            else:
                dict_trade_onoff = {
                    'MsgRef': self.__socket_manager.msg_ref_add(),
                    'MsgSendFlag': 0,  # 发送标志，客户端发出0，服务端发出1
                    'MsgSrc': 0,  # 消息源，客户端0，服务端1
                    'MsgType': 8,  # 交易员交易开关
                    'TraderID': self.__ctp_manager.get_trader_id(),
                    'OnOff': 0}
            json_trade_onoff = json.dumps(dict_trade_onoff)
            self.signal_send_msg.emit(json_trade_onoff)
        else:
            print("QAccountWidget.on_pushButton_start_strategy_clicked() 按钮显示状态与内核值不一致，不发送指令交易开关指令，widget_name=", self.__widget_name, "按钮显示：", self.pushButton_start_strategy.text(), "内核开关值：", on_off)

    # 联动加
    @pyqtSlot()
    def on_pushButton_liandongjia_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        # raise NotImplementedError
        price_tick = self.__client_main.get_clicked_strategy().get_a_price_tick()  # 最小跳
        value = self.doubleSpinBox_duotoukai.value() + price_tick  # 计算更新值
        self.doubleSpinBox_duotoukai.setValue(value)
        value = self.doubleSpinBox_duotouping.value() + price_tick  # 计算更新值
        self.doubleSpinBox_duotouping.setValue(value)
        value = self.doubleSpinBox_kongtoukai.value() + price_tick  # 计算更新值
        self.doubleSpinBox_kongtoukai.setValue(value)
        value = self.doubleSpinBox_kongtouping.value() + price_tick  # 计算更新值
        self.doubleSpinBox_kongtouping.setValue(value)

    # 联动减
    @pyqtSlot()
    def on_pushButton_liandongjian_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        # raise NotImplementedError
        price_tick = self.__client_main.get_clicked_strategy().get_a_price_tick()  # 最小跳
        value = self.doubleSpinBox_duotoukai.value() - price_tick  # 计算更新值
        self.doubleSpinBox_duotoukai.setValue(value)
        value = self.doubleSpinBox_duotouping.value() - price_tick  # 计算更新值
        self.doubleSpinBox_duotouping.setValue(value)
        value = self.doubleSpinBox_kongtoukai.value() - price_tick  # 计算更新值
        self.doubleSpinBox_kongtoukai.setValue(value)
        value = self.doubleSpinBox_kongtouping.value() - price_tick  # 计算更新值
        self.doubleSpinBox_kongtouping.setValue(value)
    
    @pyqtSlot()
    def on_pushButton_set_strategy_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        # raise NotImplementedError
        # 参数排错处理
        if len(self.lineEdit_zongshou.text()) == 0 or len(self.lineEdit_meifen.text()) == 0:
            self.signal_show_QMessageBox.emit(["错误", "参数错误"])
            return
        if int(self.lineEdit_zongshou.text()) <= 0:  # 正确值：总手大于零的整数
            self.signal_show_QMessageBox.emit(["错误", "‘总手’必须为大于零的整数"])
            return
        elif int(self.lineEdit_meifen.text()) <= 0:  # 正确值：每份大于零的整数
            self.signal_show_QMessageBox.emit(["错误", "‘每份’必须为大于零的整数"])
            return
        elif int(self.lineEdit_zongshou.text()) < int(self.lineEdit_meifen.text()):  # 正确值：每份小于总手
            self.signal_show_QMessageBox.emit(["错误", "‘总手’必须大于‘每份’"])
            return
        elif self.doubleSpinBox_kongtoukai.value() <= self.doubleSpinBox_kongtouping.value():  # 正确值：空头开 > 空头平
            self.signal_show_QMessageBox.emit(["错误", "‘空头开’必须大于‘空头平’"])
            return
        elif self.doubleSpinBox_duotoukai.value() >= self.doubleSpinBox_duotouping.value():  # 正确值：多头开 < 多头平
            self.signal_show_QMessageBox.emit(["警告", "‘多头开’必须小于‘多头平’"])
            return
        dict_args = {
            "MsgRef": self.__socket_manager.msg_ref_add(),
            "MsgSendFlag": 0,  # 发送标志，客户端发出0，服务端发出1
            "MsgType": 5,  # 修改单条策略持仓
            "TraderID": self.__client_main.get_trader_id(),  # trader_id
            "UserID": self.lineEdit_qihuozhanghao.text(),  # user_id
            "StrategyID": self.lineEdit_celuebianhao.text(),  # strategy_id
            "MsgSrc": 0,
            "Info": [{
                "trader_id": self.__client_main.get_trader_id(),  # trader_id
                "user_id": self.lineEdit_qihuozhanghao.text(),  # user_id
                "strategy_id": self.lineEdit_celuebianhao.text(),  # strategy_id
                "trade_model": self.comboBox_jiaoyimoxing.currentText(),  # 交易模型
                "order_algorithm": self.comboBox_xiadansuanfa.currentText(),  # 下单算法
                "lots": int(self.lineEdit_zongshou.text()),  # 总手
                "lots_batch": int(self.lineEdit_meifen.text()),  # 每份
                "stop_loss": float(self.spinBox_zhisun.text()),  # 止损跳数
                "spread_shift": float(self.spinBox_rangjia.text()),  # 超价发单跳数
                "a_limit_price_shift": int(self.spinBox_Abaodanpianyi.text()),  # A报单偏移
                "b_limit_price_shift": int(self.spinBox_Bbaodanpianyi.text()),  # B报单偏移
                "a_wait_price_tick": float(self.spinBox_Adengdai.text()),  # A撤单等待跳数
                "b_wait_price_tick": float(self.spinBox_Bdengdai.text()),  # B撤单等待跳数
                "a_order_action_limit": int(self.lineEdit_Achedanxianzhi.text()),  # A撤单限制
                "b_order_action_limit": int(self.lineEdit_Bchedanxianzhi.text()),  # B撤单限制
                "sell_open": self.doubleSpinBox_kongtoukai.value(),  # 价差卖开触发参数
                "buy_close": self.doubleSpinBox_kongtouping.value(),  # 价差买平触发参数
                "sell_close": self.doubleSpinBox_duotouping.value(),  # 价差卖平触发参数
                "buy_open": self.doubleSpinBox_duotoukai.value(),  # 价差买开触发参数
                "sell_open_on_off": (1 if self.checkBox_kongtoukai.isChecked() else 0),  # 价差卖开触发开关
                "buy_close_on_off": (1 if self.checkBox_kongtouping.isChecked() else 0),  # 价差买平触发开关
                "sell_close_on_off": (1 if self.checkBox_duotouping.isChecked() else 0),  # 价差卖平触发开关
                "buy_open_on_off": (1 if self.checkBox_duotoukai.isChecked() else 0)  # 价差买开触发开关
            }]
        }
        json_StrategyEditWithoutPosition = json.dumps(dict_args)
        # self.__client_main.signal_send_msg.emit(json_StrategyEditWithoutPosition)
        self.signal_send_msg.emit(json_StrategyEditWithoutPosition)  # 发送信号到SocketManager.slot_send_msg

    @pyqtSlot()
    def on_pushButton_set_position_clicked(self):
        # print(">>> QAccountWidget.on_pushButton_set_position_clicked() widget_name=", self.__widget_name, "self.pushButton_set_position.text()=", self.pushButton_set_position.text())
        if self.pushButton_set_position.text() == "设置持仓":
            self.pushButton_set_position.setText("发送持仓")  # 修改按钮显示的字符
            # 解禁仓位显示lineEdit，允许编辑
            self.lineEdit_Azongbuy.setEnabled(True)  # 文本框允许编辑
            self.lineEdit_Azuobuy.setEnabled(True)
            self.lineEdit_Azongsell.setEnabled(True)
            self.lineEdit_Azuosell.setEnabled(True)
            self.lineEdit_Bzongbuy.setEnabled(True)
            self.lineEdit_Bzuobuy.setEnabled(True)
            self.lineEdit_Bzongsell.setEnabled(True)
            self.lineEdit_Bzuosell.setEnabled(True)
        elif self.pushButton_set_position.text() == "发送持仓":
            self.lineEdit_Azongbuy.setEnabled(False)  # 禁用文本框
            self.lineEdit_Azuobuy.setEnabled(False)
            self.lineEdit_Azongsell.setEnabled(False)
            self.lineEdit_Azuosell.setEnabled(False)
            self.lineEdit_Bzongbuy.setEnabled(False)
            self.lineEdit_Bzuobuy.setEnabled(False)
            self.lineEdit_Bzongsell.setEnabled(False)
            self.lineEdit_Bzuosell.setEnabled(False)
            # self.pushButton_set_position.setEnabled(False)  # 禁用按钮
            dict_setPosition = {
                "MsgRef": self.__client_main.get_SocketManager().msg_ref_add(),
                "MsgSendFlag": 0,  # 发送标志，客户端发出0，服务端发出1
                "MsgType": 12,  # 修改单条策略持仓
                "TraderID": self.__client_main.get_trader_id(),  # trader_id
                "UserID": self.lineEdit_qihuozhanghao.text(),  # user_id
                "StrategyID": self.lineEdit_celuebianhao.text(),  # strategy_id
                "MsgSrc": 0,
                "Info": [{
                    "trader_id": self.__client_main.get_trader_id(),  # trader_id
                    "user_id": self.lineEdit_qihuozhanghao.text(),  # user_id
                    "strategy_id": self.lineEdit_celuebianhao.text(),  # strategy_id
                    "position_a_buy": int(self.lineEdit_Azongbuy.text()),  # A总买
                    "position_a_buy_today": int(self.lineEdit_Azongbuy.text()) - int(self.lineEdit_Azuobuy.text()),  # A今买
                    "position_a_buy_yesterday": int(self.lineEdit_Azuobuy.text()),  # A昨买
                    "position_a_sell": int(self.lineEdit_Azongsell.text()),  # A总卖
                    "position_a_sell_today": int(self.lineEdit_Azongsell.text()) - int(self.lineEdit_Azuosell.text()),  # A今卖
                    "position_a_sell_yesterday": int(self.lineEdit_Azuosell.text()),  # A昨卖
                    "position_b_buy": int(self.lineEdit_Bzongbuy.text()),  # B总买
                    "position_b_buy_today": int(self.lineEdit_Bzongbuy.text()) - int(self.lineEdit_Bzuobuy.text()),  # B今买
                    "position_b_buy_yesterday": int(self.lineEdit_Bzuobuy.text()),  # B昨买
                    "position_b_sell": int(self.lineEdit_Bzongsell.text()),  # B总卖
                    "position_b_sell_today": int(self.lineEdit_Bzongsell.text()) - int(self.lineEdit_Bzuosell.text()),  # B今卖
                    "position_b_sell_yesterday": int(self.lineEdit_Bzuosell.text())  # B昨卖
                }]
            }
            json_setPosition = json.dumps(dict_setPosition)
            self.signal_send_msg.emit(json_setPosition)  # 发送信号到SocketManager.slot_send_msg

    # 激活设置持仓按钮，禁用仓位输入框
    @QtCore.pyqtSlot()
    def on_pushButton_set_position_active(self):
        print(">>> QAccountWidget.on_pushButton_set_position_active() called, widget_name=", self.__widget_name)
        self.pushButton_set_position.setText("设置持仓")
        self.pushButton_set_position.setEnabled(True)  # 激活按钮

    @pyqtSlot()
    def on_pushButton_query_strategy_clicked(self):
        """
        Slot documentation goes here.
        """
        # TODO: not implemented yet
        # raise NotImplementedError
        # 获取界面参数框里显示的期货账号的策略编号
        self.pushButton_query_strategy.setEnabled(False)  # 点击按钮之后禁用，等收到消息后激活
        # 单账户窗口中查询单账户的所有策略，总账户窗口中查询所有期货账户策略
        str_user_id = self.__widget_name if self.is_single_user_widget() else ''
        dict_query_strategy = {'MsgRef': self.__socket_manager.msg_ref_add(),
                               'MsgSendFlag': 0,  # 发送标志，客户端发出0，服务端发出1
                               'MsgSrc': 0,  # 消息源，客户端0，服务端1
                               'MsgType': 3,  # 查询策略
                               'TraderID': self.__ctp_manager.get_trader_id(),
                               'UserID': str_user_id,
                               'StrategyID': ''}
        json_query_strategy = json.dumps(dict_query_strategy)
        self.signal_send_msg.emit(json_query_strategy)

        # 测试用：触发保存df_order和df_trade保存到本地
        if self.is_single_user_widget():
            print(">>> QAccountWidget.on_pushButton_query_strategy_clicked() 保存df_order和df_trade到本地, widget_name=", self.__widget_name, "user_id =", self.__user.get_user_id().decode())
            self.__user.save_df_order_trade()

    @pyqtSlot(bool)
    def on_checkBox_kongtoukai_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet
        # raise NotImplementedError
    
    @pyqtSlot(int)
    def on_checkBox_kongtoukai_stateChanged(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        # raise NotImplementedError
    
    @pyqtSlot(bool)
    def on_checkBox_duotouping_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet
        # raise NotImplementedError
    
    @pyqtSlot(int)
    def on_checkBox_duotouping_stateChanged(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        # raise NotImplementedError
    
    @pyqtSlot(bool)
    def on_checkBox_duotoukai_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet
        # raise NotImplementedError
    
    @pyqtSlot(int)
    def on_checkBox_duotoukai_stateChanged(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        # raise NotImplementedError
    
    @pyqtSlot(bool)
    def on_checkBox_kongtouping_clicked(self, checked):
        """
        Slot documentation goes here.
        
        @param checked DESCRIPTION
        @type bool
        """
        # TODO: not implemented yet
        # raise NotImplementedError
    
    @pyqtSlot(int)
    def on_checkBox_kongtouping_stateChanged(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        # raise NotImplementedError
    
    #@pyqtSlot(QPoint)
    #def on_tablewidget_tableWidget_Trade_Args_customContextMenuRequested(self, pos):
        """
        Slot documentation goes here.
        
        @param pos DESCRIPTION
        @type QPoint
        """
        # TODO: not implemented yet
        ## raise NotImplementedError

    
    @pyqtSlot(int)
    def on_comboBox_qihuozhanghao_currentIndexChanged(self, index):
        """
        Slot documentation goes here.
        
        @param index DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        # raise NotImplementedError
        # print(">>> QAccountWidget.on_comboBox_qihuozhanghao_currentIndexChanged()")
    
    @pyqtSlot(str)
    def on_comboBox_qihuozhanghao_currentIndexChanged(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type str
        """
        # TODO: not implemented yet
        # raise NotImplementedError

    @pyqtSlot(int)
    def on_comboBox_jiaoyimoxing_currentIndexChanged(self, index):
        """
        Slot documentation goes here.
        
        @param index DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        # raise NotImplementedError
    
    @pyqtSlot(str)
    def on_comboBox_jiaoyimoxing_currentIndexChanged(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type str
        """
        # TODO: not implemented yet
        print("currentindex string %s" % p0)
    
    @pyqtSlot(int)
    def on_comboBox_celuebianhao_currentIndexChanged(self, index):
        """
        Slot documentation goes here.
        
        @param index DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        print("currentindex %d" % index)
    
    @pyqtSlot(str)
    def on_comboBox_celuebianhao_currentIndexChanged(self, p0):
        """
        Slot documentation goes here.
        
        @param p0 DESCRIPTION
        @type str
        """
        # TODO: not implemented yet
        # raise NotImplementedError

    # 鼠标右击捕获事件
    @pyqtSlot(QPoint)
    def on_tableWidget_Trade_Args_customContextMenuRequested(self, pos):
        print("QAccountWidget.on_tableWidget_Trade_Args_customContextMenuRequested() called 鼠标右击捕获事件")
        """
        Slot documentation goes here.
        
        @param pos DESCRIPTION
        @type QPoint
        """
        # TODO: not implemented yet
        self.popMenu.exec_(QtGui.QCursor.pos())

    # 找出策略所在的行标，如果不存在该窗口则返回None，存在于该窗口中则返回具体行数int值
    def find_strategy(self, obj_strategy):
        if self.tableWidget_Trade_Args.rowCount() == 0:
            return None  # 窗口中无策略，返回None
        for i_row in range(self.tableWidget_Trade_Args.rowCount()):
            if self.tableWidget_Trade_Args.item(i_row, 2).text() == obj_strategy.get_user_id()  \
                    and self.tableWidget_Trade_Args.item( i_row, 3).text() == obj_strategy.get_strategy_id():
                return i_row  # 返回策略在窗口中的函数
        return None  # 策略不属于该窗口，返回None

    # 设置窗口鼠标点击到形参中策略，若窗口中不存在该策略则跳出
    @pyqtSlot(int, int)
    def set_on_tableWidget_Trade_Args_cellClicked(self, i_row, i_column):
        print("QAccountWidget.set_on_tableWidget_Trade_Args_cellClicked() self.sender()=", self.sender(), "widget_name=", self.__widget_name)
        if self.tableWidget_Trade_Args.rowCount() > 0:
            self.on_tableWidget_Trade_Args_cellClicked(i_row, i_column)

    @pyqtSlot(int, int)
    def on_tableWidget_Trade_Args_cellClicked(self, row, column):
        """
        Slot documentation goes here.
        
        @param row DESCRIPTION
        @type int
        @param column DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        # 设置鼠标点击触发的设置属性
        # self.__clicked_item = self.tableWidget_Trade_Args.item(row, column)  # 局部变量，鼠标点击的item设置为QAccountWidget的属性
        # self.__client_main.set_clicked_item(self.__clicked_item)  # 全局变量，鼠标点击的item设置为ClientMain的属性，全局唯一
        # self.__clicked_status = {'row': row, 'column': column, 'widget_name': self.__widget_name, 'user_id': self.tableWidget_Trade_Args.item(row, 1).text(), 'strategy_id': self.tableWidget_Trade_Args.item(row, 2).text()}
        # self.__client_main.set_clicked_status(self.__clicked_status)  # 保存鼠标点击状态到ClientMain的属性，保存全局唯一一个鼠标最后点击位置
        self.__clicked_user_id = self.tableWidget_Trade_Args.item(row, 1).text()
        self.__clicked_strategy_id = self.tableWidget_Trade_Args.item(row, 2).text()
        self.tableWidget_Trade_Args.setCurrentCell(row, column)  # 设置当前Cell
        print(">>> QAccountWidget.on_tableWidget_Trade_Args_cellClicked() self.__clicked_user_id =", self.__clicked_user_id, "self.__clicked_strategy_id =", self.__clicked_strategy_id)
        self.__dict_clicked_info[self.__current_tab_name] = {'user_id': self.__clicked_user_id,
                                                             'strategy_id': self.__clicked_strategy_id,
                                                             'row': row}
        self.update_groupBox()  # 更新界面groupBox

        """
        # 找到鼠标点击的策略对象
        for i_strategy in self.__list_strategy:
            print(">>> i_strategy.get_user_id() == self.__clicked_status['user_id'] and i_strategy.get_strategy_id() == self.__clicked_status['strategy_id'] ", i_strategy.get_user_id(), self.__clicked_status['user_id'], i_strategy.get_strategy_id(), self.__clicked_status['strategy_id'])
            if i_strategy.get_user_id() == self.__clicked_status['user_id'] \
                    and i_strategy.get_strategy_id() == self.__clicked_status['strategy_id']:
                self.__client_main.set_clicked_strategy(i_strategy)  # 全局变量，鼠标点击的策略对象设置为ClientMain属性
                self.__clicked_strategy = i_strategy  # 局部变量，鼠标点击的策略对象设置为QAccountWidget属性
                break
        print("QAccountWidget.on_tableWidget_Trade_Args_cellClicked() widget_name=", self.__widget_name, "鼠标点击位置=row %d, column %d" % (row, column), "值=", self.__clicked_item.text(), "user_id=", self.__clicked_strategy.get_user_id(), "strategy_id=", self.__clicked_strategy.get_strategy_id())

        # 监测交易开关、只平开关变化，并触发修改指令
        if self.__ctp_manager.get_init_UI_finished():
            self.tableWidget_Trade_Args.setCurrentItem(self.__clicked_item)
            # 判断策略开关item的checkState()状态变化
            if column == 0:
                # checkState值与内核值不同，则发送修改指令
                on_off_checkState = 0 if self.__clicked_item.checkState() == 0 else 1
                # print(">>> QAccountWidget.on_tableWidget_Trade_Args_cellClicked()", on_off_checkState, self.__client_main.get_clicked_strategy().get_on_off())
                if on_off_checkState != self.__client_main.get_clicked_strategy().get_on_off():
                    self.__clicked_item.setFlags(self.__clicked_item.flags() & (~QtCore.Qt.ItemIsEnabled))  # 设置当前item的状态属性(与操作)
                    self.__item_on_off_status = {'widget_name': self.__widget_name,
                                                 'user_id': self.tableWidget_Trade_Args.item(row, 2).text(),
                                                 'strategy_id': self.tableWidget_Trade_Args.item(row, 3).text(),
                                                 'enable': 0}  # enable值为1启用、0禁用
                    dict_strategy_onoff = {
                        'MsgRef': self.__socket_manager.msg_ref_add(),
                        'MsgSendFlag': 0,  # 发送标志，客户端发出0，服务端发出1
                        'MsgSrc': 0,  # 消息源，客户端0，服务端1
                        'MsgType': 13,  # 策略交易开关
                        'TraderID': self.__ctp_manager.get_trader_id(),
                        'UserID': self.__clicked_strategy.get_user_id(),
                        'StrategyID': self.__clicked_strategy.get_strategy_id(),
                        'OnOff': on_off_checkState  # 0关、1开
                        }
                    # print(">>> QAccountWidget.on_tableWidget_Trade_Args_cellClicked() 发送“开关”修改指令", dict_strategy_onoff)
                    json_strategy_onoff = json.dumps(dict_strategy_onoff)
                    self.signal_send_msg.emit(json_strategy_onoff)
            # 判断策略只平item的checkState()状态变化
            elif column == 1:
                only_close_checkState = 0 if self.__clicked_item.checkState() == 0 else 1
                if only_close_checkState != self.__client_main.get_clicked_strategy().get_only_close():
                    self.__clicked_item.setFlags(self.__clicked_item.flags() & (~QtCore.Qt.ItemIsEnabled))  # 设置当前item的状态属性(与操作)
                    self.__item_only_close_status = {'widget_name': self.__widget_name,
                                                     'user_id': self.tableWidget_Trade_Args.item(row, 2).text(),
                                                     'strategy_id': self.tableWidget_Trade_Args.item(row, 3).text(),
                                                     'enable': 0}  # enable值为1启用、0禁用
                    dict_strategy_only_close = {
                        'MsgRef': self.__socket_manager.msg_ref_add(),
                        'MsgSendFlag': 0,  # 发送标志，客户端发出0，服务端发出1
                        'MsgSrc': 0,  # 消息源，客户端0，服务端1
                        'MsgType': 14,  # 策略只平开关
                        'TraderID': self.__ctp_manager.get_trader_id(),
                        'UserID': self.__clicked_strategy.get_user_id(),
                        'StrategyID': self.__clicked_strategy.get_strategy_id(),
                        'OnOff': only_close_checkState  # 0关、1开
                        }
                    print(">>> QAccountWidget.on_tableWidget_Trade_Args_cellClicked() 发送“只平”修改指令", dict_strategy_only_close)
                    json_strategy_only_close = json.dumps(dict_strategy_only_close)
                    self.signal_send_msg.emit(json_strategy_only_close)

        # 设置所有策略的属性，策略在当前窗口中是否被选中
        if self.is_single_user_widget():  # 单账户窗口
            # if i_strategy.get_user_id() == self.__clicked_status['user_id'] and i_strategy.get_strategy_id() == self.__clicked_status['strategy_id']:
            #     i_strategy.set_clicked_signal(True)
            #     # print(">>> QAccountWidget.on_tableWidget_Trade_Args_cellClicked() 鼠标点击单账户窗口，user_id=", i_strategy.get_user_id(), "strategy_id=", i_strategy.get_strategy_id())
            # else:
            #     i_strategy.set_clicked_signal(False)
            # if i_strategy == self.__clicked_strategy:
            #     i_strategy.set_clicked_signal(True)
            # else:
            #     i_strategy.set_clicked_signal(False)
            for i_strategy in self.__list_strategy:
                i_strategy.set_clicked_signal(True if i_strategy == self.__clicked_strategy else False)
        else:  # 总账户窗口
            # if i_strategy.get_user_id() == self.__clicked_status['user_id'] and i_strategy.get_strategy_id() == self.__clicked_status['strategy_id']:
            #     i_strategy.set_clicked_total(True)
            #     # print(">>> QAccountWidget.on_tableWidget_Trade_Args_cellClicked() 鼠标点击总账户窗口，user_id=", i_strategy.get_user_id(), "strategy_id=", i_strategy.get_strategy_id())
            # else:
            #     i_strategy.set_clicked_total(False)
            for i_strategy in self.__list_strategy:
                i_strategy.set_clicked_total(True if i_strategy == self.__clicked_strategy else False)

        self.slot_update_strategy(self.__clicked_strategy)  # 更新策略所有变量在界面的显示（包含tableWidget和groupBox）
        # self.slot_update_strategy_position(self.__clicked_strategy)  # 更新策略持仓在界面的显示（包含tableWidget和groupBox）
        """

    @pyqtSlot(int, int)
    def on_tableWidget_Trade_Args_cellDoubleClicked(self, row, column):
        """
        Slot documentation goes here.
        
        @param row DESCRIPTION
        @type int
        @param column DESCRIPTION
        @type int
        """
        # TODO: not implemented yet
        # raise NotImplementedError




# if __name__ == "__main__":
#     import sys
#     app = QtGui.QApplication(sys.argv)
#     Form = QAccountWidget()
#     Form.show()
#
#     #设置tablewidget的行数
#     Form.tableWidget_Trade_Args.setRowCount(5)
#     # print("0 header name %s, %d ttttttttt" % (Form.tableWidget_Trade_Args.horizontalHeaderItem(0).text(), 2))
#
#     #创建QTableWidgetItem
#     for i in range(13):
#         item = QtGui.QTableWidgetItem()
#         item.setText("hello: %d你好" % i)
#         if i == 0:
#             item.setCheckState(False)
#         Form.tableWidget_Trade_Args.setItem(0, i, item)
#
#
#
#     sys.exit(app.exec_())