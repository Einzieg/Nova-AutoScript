import logging
from threading import Lock

from nicegui import ui, app

from core.GuiAppSetting import GuiAppSetting
from device_operation.SQLiteClient import SQLiteClient
from core.LogElementHandler import LogElementHandler

class GuiApp:
    def __init__(self):
        self.settings_lock = Lock()
        self.start_btn = None
        self.db = SQLiteClient()
        self.splitter_container = ui.column().classes('w-full')
        self.new_tab_input = None
        self.vertical_tabs = None
        self.main_tabs = None
        self.tab_buttons = {}  # 用于存储每个标签页的按钮引用
        self.device_threads = {}  # 存储每个标签页的设备线程
        self.device_logs = {}  # 存储每个标签页的日志区域
        self.settings_page = GuiAppSetting()

    def on_startup(self):
        """应用启动时加载主题配置"""
        logging.info('on_startup')
        self.settings_page.on_startup()

    @staticmethod
    def on_close():
        logging.info('on_close')
        app.shutdown()

    def _create_setting_tab_panel(self):
        """创建Setting标签页内容"""
        self.settings_page.create_setting_tab_panel()

    def load_tabs(self):
        """从数据库加载标签页"""
        self.splitter_container.clear()

        tabs_data = self.db.fetch_all("SELECT name, text FROM module")

        with self.splitter_container:
            self._create_main_tabs()
            self._create_main_tab_panels(tabs_data)

        if tabs_data:
            self.vertical_tabs.value = tabs_data[0]['name']

    def _create_main_tabs(self):
        """创建主标签页"""
        with ui.tabs() as self.main_tabs:
            self.start_tab = ui.tab('Start', icon='play_arrow')
            self.setting_tab = ui.tab('Setting', icon='settings')

    def _create_main_tab_panels(self, tabs_data):
        """创建主标签页内容面板"""
        with ui.tab_panels(self.main_tabs, value='Start').classes('w-full'):
            self._create_start_tab_panel(tabs_data)
            self._create_setting_tab_panel()

    def _create_start_tab_panel(self, tabs_data):
        """创建Start标签页内容"""
        with ui.tab_panel(self.start_tab):
            with ui.row().classes('w-full h-full'):
                self._create_vertical_tabs(tabs_data)
                self._create_vertical_tab_panels(tabs_data)

    def _create_vertical_tabs(self, tabs_data):
        """创建垂直标签页"""
        with ui.column().classes('w-1/10 h-full fixed-tabs'):
            self.vertical_tabs = ui.tabs().props('vertical').classes('w-full h-full')
            with self.vertical_tabs:
                for tab in tabs_data:
                    ui.tab(tab['name'], icon='insert_link')
                self.add_tab = ui.tab('新增', icon='add')

    def _create_vertical_tab_panels(self, tabs_data):
        """创建垂直标签页内容面板"""
        with ui.column().classes('w-9/10 h-full'):
            with ui.tab_panels(self.vertical_tabs).props('vertical').classes('w-full h-full'):
                for tab in tabs_data:
                    with ui.tab_panel(tab['name']).classes('w-full h-full'):
                        with ui.row().classes('w-full h-full items-center'):
                            # 添加启动和停止按钮
                            start_btn = ui.button('启动', icon='start', on_click=lambda t=tab['name']: self.start(t)).props('color=green')
                            stop_btn = ui.button('停止', icon='stop', on_click=lambda t=tab['name']: self.stop(t)).props('color=red').classes('hidden')

                            # 使用默认参数捕获当前 tab 的值
                            ui.button('修改', icon='edit', on_click=lambda t=tab['name']: self.update_tab(t))
                            ui.button('删除', icon='delete_forever', on_click=lambda t=tab['name']: self.remove_tab(t))

                            # 将按钮的引用存储到 self.tab_buttons 中
                            self.tab_buttons[tab['name']] = {
                                'start_btn': start_btn,
                                'stop_btn': stop_btn,
                            }
                        log = ui.log().classes('w-200 h-80')
                        handler = LogElementHandler(log)
                        logging.getLogger(tab['name']).addHandler(handler)

                with ui.tab_panel(self.add_tab):
                    with ui.column().classes('w-full'):
                        self.new_tab_input = ui.input('名称', placeholder='输入名称')
                        ui.button('添加', on_click=self.add_table)

    def start(self, tab_name):
        """启动设备线程"""
        buttons = self.tab_buttons[tab_name]
        buttons['start_btn'].classes(add='hidden')  # 隐藏启动按钮
        buttons['stop_btn'].classes(remove='hidden')  # 显示停止按钮


    def stop(self, tab_name):
        """停止设备线程"""
        buttons = self.tab_buttons[tab_name]
        buttons['stop_btn'].classes(add='hidden')  # 隐藏停止按钮
        buttons['start_btn'].classes(remove='hidden')  # 显示启动按钮


    def add_table(self):
        """添加新标签页"""
        new_tab_name = self.new_tab_input.value
        if new_tab_name:
            if self.db.fetch_one("SELECT name FROM module WHERE name = ?", (new_tab_name,)):
                ui.notify('该名称已存在', color='red')
                return
            self.db.insert_data("module", ["name", "text"], [new_tab_name, "新标签页内容"])
            self.new_tab_input.value = ''
            self.load_tabs()
            self.vertical_tabs.value = new_tab_name

    def update_tab(self, tab_name):
        """修改标签页"""
        with ui.dialog() as dialog, ui.card():
            with ui.column().classes('items-center'):
                update_tab_input = ui.input('名称', placeholder='输入名称', value=tab_name)  # 默认显示当前名称
                with ui.row().classes('justify-center'):  # 使按钮水平居中
                    ui.button('确定', on_click=lambda: self._confirm_update_tab(tab_name, update_tab_input.value, dialog))
                    ui.button('取消', on_click=dialog.close)
        dialog.open()  # 手动打开对话框

    def _confirm_update_tab(self, old_name, new_name, dialog):
        """确认修改标签页"""
        if new_name:
            if self.db.fetch_one("SELECT name FROM module WHERE name = ?", (new_name,)):
                ui.notify('该名称已存在', color='red')
                return
            self.db.execute_update("UPDATE module SET name = ? WHERE name = ?", (new_name, old_name))
            self.load_tabs()
            self.vertical_tabs.value = new_name
            dialog.close()  # 关闭对话框

    def remove_tab(self, tab_name):
        """删除标签页"""
        with ui.dialog() as dialog, ui.card():
            with ui.column().classes('items-center'):
                ui.label(f'确定要删除 {tab_name} 吗?')
                with ui.row().classes('justify-center'):
                    ui.button('确定', on_click=lambda: self._confirm_remove_tab(tab_name, dialog))
                    ui.button('取消', on_click=dialog.close)
        dialog.open()

    def _confirm_remove_tab(self, tab_name, dialog):
        """确认删除标签页"""
        self.db.execute_update("DELETE FROM module WHERE name = ?", (tab_name,))
        self.load_tabs()
        dialog.close()

    def run(self):
        """启动应用"""
        app.on_startup(self.on_startup)
        app.on_shutdown(self.on_close)
        self.load_tabs()
        ui.run(native=True, window_size=(1280, 720), language='zh-CN', reload=False)
