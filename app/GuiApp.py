import asyncio
import logging

from nicegui import ui, app

from app.GuiAppConfigurationTabs import GuiAppConfigurationTabs
from app.GuiAppSetting import GuiAppSetting
from core.LogManager import LogManager
from core.MainProcess import MainProcess
from models.Module import Module


class GuiApp:
    def __init__(self):
        self.processes = {}
        self.target_thread = {}
        self.target_running = {}
        self.start_btn = None
        self.splitter_container = ui.column().classes('w-full')
        self.new_tab_input = None
        self.vertical_tabs = None
        self.main_tabs = None
        self.tab_buttons = {}  # 用于存储每个标签页的按钮引用
        self.settings_page = GuiAppSetting()
        self.configuration_tabs = GuiAppConfigurationTabs()
        self.log_manager = LogManager()

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
        self.log_manager.clear()

        tabs_data = Module.select()

        for tab in tabs_data:
            if tab.name not in self.target_thread:
                self.target_running[tab.name] = False

        with self.splitter_container:
            self._create_main_tabs()
            self._create_main_tab_panels(tabs_data)

        if tabs_data:
            self.vertical_tabs.value = tabs_data[0].name

    def _create_main_tabs(self):
        """创建主标签页"""
        with ui.tabs() as self.main_tabs:
            self.start_tab = ui.tab('开始', icon='play_arrow')
            self.setting_tab = ui.tab('设置', icon='settings')

    def _create_main_tab_panels(self, tabs_data):
        """创建主标签页内容面板"""
        with ui.tab_panels(self.main_tabs, value='开始').classes('w-full'):
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
                    ui.tab(tab.name, icon='insert_link')
                self.add_tab = ui.tab('新增', icon='add')

    def _create_configuration_tabs(self, tab_name):
        """创建配置标签页"""
        self.configuration_tabs.create_configuration_tabs(tab_name)

    def _create_vertical_tab_panels(self, tabs_data):
        """创建垂直标签页内容面板"""
        with ui.column().classes('h-full border').style('width:90%'):
            with ui.tab_panels(self.vertical_tabs).props('vertical').classes('w-full h-full'):
                for tab in tabs_data:
                    with ui.tab_panel(tab.name).classes('w-full h-full'):
                        with ui.row().classes('w-full h-full'):
                            with ui.column().classes('h-full').style('width:60%'):
                                with ui.row().classes('w-full h-full items-center'):
                                    # 添加启动和停止按钮
                                    start_btn = ui.button('启动', icon='start', on_click=lambda t=tab.name: self.start(t)).props('color=green')
                                    stop_btn = ui.button('停止', icon='stop', on_click=lambda t=tab.name: self.stop(t)).props('color=red').classes('hidden')
                                    pause_btn = ui.button('暂停', icon='pause', on_click=lambda t=tab.name: self.pause(t)).props('color=orange').classes('hidden')
                                    restore_btn = ui.button('恢复', icon='restore', on_click=lambda t=tab.name: self.restore(t)).props('color=green').classes('hidden')

                                    # 使用默认参数捕获当前 tab 的值
                                    edit_btn = ui.button('修改', icon='edit', on_click=lambda t=tab.name: self.update_tab(t))
                                    del_btn = ui.button('删除', icon='delete_forever', on_click=lambda t=tab.name: self.remove_tab(t))

                                    # 将按钮的引用存储到 self.tab_buttons 中
                                    self.tab_buttons[tab.name] = {
                                        'start_btn': start_btn,
                                        'stop_btn': stop_btn,
                                        'pause_btn': pause_btn,
                                        'restore_btn': restore_btn,
                                        'edit_btn': edit_btn,
                                        'del_btn': del_btn,
                                    }

                                    if self.target_running[tab.name]:
                                        start_btn.classes(add='hidden')
                                        stop_btn.classes(remove='hidden')
                                        pause_btn.classes(remove='hidden')
                                        edit_btn.classes(add='hidden')
                                        del_btn.classes(add='hidden')
                                    ui.space()
                                    ui.select({10: 'DEBUG', 20: 'INFO', 30: 'WARNING', 40: 'ERROR'},
                                              value=20, label='日志级别',
                                              on_change=lambda level, t=tab.name: self.log_manager.set_level(t, level.value)
                                              ).classes('w-20')

                                    self._create_configuration_tabs(tab.name)

                            with ui.column().classes('h-full').style('width:31vw;height:37vw;overflow-y:auto;'):
                                self.log_manager.get_logger(tab.name)

                with ui.tab_panel(self.add_tab):
                    with ui.column().classes('w-full'):
                        self.new_tab_input = ui.input('名称', placeholder='输入名称')
                        ui.button('添加', on_click=self.add_table)

    def start(self, tab_name):
        buttons = self.tab_buttons[tab_name]
        buttons['start_btn'].classes(add='hidden')  # 隐藏启动按钮
        buttons['edit_btn'].classes(add='hidden')
        buttons['del_btn'].classes(add='hidden')
        buttons['stop_btn'].classes(remove='hidden')  # 显示停止按钮
        # buttons['pause_btn'].classes(remove='hidden')

        # 创建 MainProcess 实例并存储
        process = MainProcess(self, tab_name)
        self.target_running[tab_name] = True
        self.target_thread[tab_name] = asyncio.create_task(self.run_script(process))

        # 保存 MainProcess 实例
        if not hasattr(self, 'processes'):
            self.processes = {}
        self.processes[tab_name] = process

    def stop(self, tab_name):
        buttons = self.tab_buttons[tab_name]
        buttons['stop_btn'].classes(add='hidden')  # 隐藏停止按钮
        buttons['start_btn'].classes(remove='hidden')  # 显示启动按钮
        buttons['edit_btn'].classes(remove='hidden')
        buttons['del_btn'].classes(remove='hidden')
        # buttons['pause_btn'].classes(add='hidden')
        # buttons['restore_btn'].classes(add='hidden')

        self.target_running[tab_name] = False

        # 取消对应的异步任务
        if tab_name in self.target_thread:
            self.target_thread[tab_name].cancel()  # 取消任务
            del self.target_thread[tab_name]

    async def run_script(self, process):
        """运行 MainProcess 的异步任务"""
        try:
            await process.run()
        except asyncio.CancelledError:
            # 处理任务取消的情况
            print(f"Task for {process.target} was cancelled.")
        finally:
            self.target_running[process.target] = False

    def pause(self, tab_name):
        """暂停"""
        buttons = self.tab_buttons[tab_name]
        buttons['pause_btn'].classes(add='hidden')
        buttons['restore_btn'].classes(remove='hidden')

        if tab_name in self.processes:
            process = self.processes[tab_name]  # 获取 MainProcess 实例
            process.paused = True  # 设置暂停标志

    def restore(self, tab_name):
        """恢复"""
        buttons = self.tab_buttons[tab_name]
        buttons['restore_btn'].classes(add='hidden')
        buttons['pause_btn'].classes(remove='hidden')

        if tab_name in self.processes:
            process = self.processes[tab_name]  # 获取 MainProcess 实例
            process.paused = False  # 取消暂停标志

    def add_table(self):
        """添加新标签页"""
        new_tab_name = self.new_tab_input.value
        if new_tab_name:
            if Module.get_or_none(Module.name == new_tab_name):
                ui.notify('该名称已存在', color='red')
                return
            Module.create(name=new_tab_name)
            self.new_tab_input.value = ''
            self.load_tabs()
            self.vertical_tabs.value = new_tab_name

    def update_tab(self, tab_name):
        """修改标签页"""
        with ui.dialog() as dialog, ui.card():
            with ui.column().classes('items-center'):
                update_tab_input = ui.input('名称', placeholder='输入名称', value=tab_name)  # 默认显示当前名称
                with ui.row().classes('justify-center'):  # 使按钮水平居中
                    ui.button('确定',
                              on_click=lambda: self._confirm_update_tab(tab_name, update_tab_input.value, dialog))
                    ui.button('取消', on_click=dialog.close)
        dialog.open()  # 手动打开对话框

    def _confirm_update_tab(self, old_name, new_name, dialog):
        """确认修改标签页"""
        if new_name:
            if Module.get_or_none(Module.name == new_name):
                ui.notify('该名称已存在', color='red')
                return
            Module.update(name=new_name).where(Module.name == old_name).execute()
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
        Module.delete().where(Module.name == tab_name).execute()
        self.load_tabs()
        dialog.close()

    def check_update(self):
        # res = requests.get('')
        ui.html('<style>.multi-line-notification { white-space: pre-line; }</style>')
        ui.notify(
            '检查更新\n'
            '无更新',
            multi_line=True,
            classes='multi-line-notification',
        )

    def run(self):
        """启动应用"""
        app.on_startup(self.on_startup)
        app.on_shutdown(self.on_close)
        self.load_tabs()
        self.check_update()
        ui.run(native=True, window_size=(1280, 720), language='zh-CN', title='Nova-AutoScript', favicon='🔧', reload=False)
