import asyncio
import logging
from pathlib import Path

from nicegui import ui, app
from peewee import fn

from app.GuiAppConfigurationTabs import GuiAppConfigurationTabs
from app.GuiAppSetting import GuiAppSetting, WINDOW_SIZE
from core.LogManager import LogManager
from core.MainProcess import MainProcess
from models import Config, Module


class GuiApp:
    def __init__(self):
        self.conf = Config.get_or_create(id=1)[0]
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
        self.configuration_tabs = GuiAppConfigurationTabs(self)
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
        is_portrait = self.conf.window_size == 1  # 1 对应 960x1040

        with ui.tab_panel(self.start_tab):
            if is_portrait:
                # 竖屏使用列布局
                with ui.column().classes('w-full h-full'):
                    self._create_vertical_tabs(tabs_data)
                    self._create_vertical_tab_panels(tabs_data)
            else:
                # 横屏使用行布局
                with ui.row().classes('w-full h-full'):
                    self._create_vertical_tabs(tabs_data)
                    self._create_vertical_tab_panels(tabs_data)


    def _create_vertical_tabs(self, tabs_data):
        """创建垂直标签页"""
        is_portrait = self.conf.window_size == 1  # 1 对应 960x1040

        if is_portrait:
            # 竖屏时标签页横向排列在顶部
            with ui.column().classes('w-full h-16'):
                self.vertical_tabs = ui.tabs().props('').classes('w-full')
                with self.vertical_tabs:
                    for tab in tabs_data:
                        ui.tab(tab.name, icon='insert_link')
                    self.add_tab = ui.tab('新增', icon='add')
        else:
            # 横屏时保持原有垂直标签页
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
        """创建垂直标签页内容面板 - 响应式适配"""
        # 根据窗口大小判断是否为竖屏模式
        is_portrait = self.conf.window_size == 1  # 1 对应 960x1040

        with ui.column().classes('h-full border').style('width:90%' if not is_portrait else 'width:100%'):
            with ui.tab_panels(self.vertical_tabs).props('vertical' if not is_portrait else '').classes('w-full h-full'):
                for tab in tabs_data:
                    with ui.tab_panel(tab.name).classes('w-full h-full'):
                        # 根据屏幕方向选择布局方式
                        if is_portrait:
                            # 竖屏使用列布局
                            with ui.column().classes('w-full h-full'):
                                # 控制按钮区域
                                with ui.column().classes('w-full'):
                                    with ui.row().classes('w-full items-center flex-wrap'):
                                        start_btn = ui.button('启动', icon='start', on_click=lambda t=tab.name: self.start(t)).props('color=green')
                                        stop_btn = ui.button('停止', icon='stop', on_click=lambda t=tab.name: self.stop(t)).props('color=red').classes('hidden')
                                        pause_btn = ui.button('暂停', icon='pause', on_click=lambda t=tab.name: self.pause(t)).props('color=orange').classes('hidden')
                                        restore_btn = ui.button('恢复', icon='restore', on_click=lambda t=tab.name: self.restore(t)).props('color=green').classes('hidden')
                                        edit_btn = ui.button('修改', icon='edit', on_click=lambda t=tab.name: self.update_tab(t))
                                        del_btn = ui.button('删除', icon='delete_forever', on_click=lambda t=tab.name: self.remove_tab(t))

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
                                                  ).classes('w-32')

                                        self._create_configuration_tabs(tab.name)

                                # 日志区域
                                with ui.column().classes('h-full').style('width:100%;height:37vw;overflow-y:auto;'):
                                    self.log_manager.get_logger(tab.name)
                        else:
                            # 横屏保持原有布局
                            with ui.row().classes('w-full h-full'):
                                with ui.column().classes('h-full').style('width:60%'):
                                    with ui.row().classes('w-full h-full items-center'):
                                        start_btn = ui.button('启动', icon='start', on_click=lambda t=tab.name: self.start(t)).props('color=green')
                                        stop_btn = ui.button('停止', icon='stop', on_click=lambda t=tab.name: self.stop(t)).props('color=red').classes('hidden')
                                        pause_btn = ui.button('暂停', icon='pause', on_click=lambda t=tab.name: self.pause(t)).props('color=orange').classes('hidden')
                                        restore_btn = ui.button('恢复', icon='restore', on_click=lambda t=tab.name: self.restore(t)).props('color=green').classes('hidden')
                                        edit_btn = ui.button('修改', icon='edit', on_click=lambda t=tab.name: self.update_tab(t))
                                        del_btn = ui.button('删除', icon='delete_forever', on_click=lambda t=tab.name: self.remove_tab(t))

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
        if self.target_running[tab_name]:
            ui.notify('任务运行中，请勿重复启动！', color='red')
            return
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

    def quick_start(self, tab_name, task):
        if self.target_running[tab_name]:
            ui.notify('任务运行中，请勿重复启动！', color='red')
            return
        buttons = self.tab_buttons[tab_name]
        buttons['start_btn'].classes(add='hidden')  # 隐藏启动按钮
        buttons['edit_btn'].classes(add='hidden')
        buttons['del_btn'].classes(add='hidden')
        buttons['stop_btn'].classes(remove='hidden')  # 显示停止按钮

        # 创建 MainProcess 实例并存储
        process = MainProcess(self, tab_name)
        self.target_running[tab_name] = True
        self.target_thread[tab_name] = asyncio.create_task(self.quick_run_script(process, task))

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
            logging.info(f"任务 {process.target} 已取消.")
        finally:
            self.target_running[process.target] = False

    async def quick_run_script(self, process, task):
        try:
            await process.quick_run(task)
        except asyncio.CancelledError:
            # 处理任务取消的情况
            logging.info(f"任务 {process.target} 已取消.")
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
            max_simulator = Module.select(fn.MAX(Module.simulator_index)).scalar()
            max_simulator = max_simulator if max_simulator is not None else -1
            Module.create(name=new_tab_name, simulator_index=max_simulator + 1)
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
        ui.timer(1.0, self.settings_page.check_update_silently, once=True)

    def check_path(self):
        root_path = Path(__file__).parent
        path_str = str(root_path)
        if any('\u4e00' <= char <= '\u9fff' for char in path_str):
            with ui.dialog().props('backdrop-filter="blur(8px) brightness(60%)"') as dialog:
                ui.label('检测到软件路径含有中文\n请将软件移动到无中文路径下').classes('text-3xl text-white whitespace-pre-line text-center')

            dialog.on('escape-key', lambda: ui.notify('ESC pressed'))
            dialog.open()

    def run(self):
        """启动应用"""
        app.on_startup(self.on_startup)
        app.on_shutdown(self.on_close)
        app.native.settings['ALLOW_DOWNLOADS'] = True
        self.load_tabs()
        self.check_update()
        self.check_path()
        # on_air="MA6Q0Bb9rAmLQqVX"
        if self.conf.on_air:
            ui.run(native=True, window_size=WINDOW_SIZE[self.conf.window_size], language='zh-CN', title='Nova-AutoScript', favicon='🔧', reload=False, on_air=self.conf.on_air_token)
        else:
            ui.run(native=True, window_size=WINDOW_SIZE[self.conf.window_size], language='zh-CN', title='Nova-AutoScript', favicon='🔧', reload=False)
