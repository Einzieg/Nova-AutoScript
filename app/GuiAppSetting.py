import logging
import webbrowser

from nicegui import ui, app

from models import Config

WINDOW_SIZE = {
    0: (1280, 720),
    1: (960, 1040)
}


class GuiAppSetting:

    def __init__(self):
        self.conf = Config.get_or_create(id=1)[0]
        self.dark_mode = ui.dark_mode()
        self.dark_btn = None
        self.light_btn = None

    @staticmethod
    def on_close():
        """关闭应用"""
        app.shutdown()

    def on_startup(self):
        """应用启动时加载主题配置"""
        if bool(self.conf.dark_mode):
            self.dark_mode.enable()
        else:
            self.dark_mode.disable()

    def create_setting_tab_panel(self):
        """创建Setting标签页内容"""
        with ((ui.tab_panel('设置'))):

            # 主题切换按钮
            with ui.row().classes('items-center'):
                ui.label('切换主题:').classes('text-xl')

                self.dark_btn = ui.button('深色模式', icon='dark_mode', on_click=lambda: self.change_theme(True)).props('color=dark text-color=white')
                self.light_btn = ui.button('浅色模式', icon='light_mode', on_click=lambda: self.change_theme(False)).props('color=white text-color=black')

                if bool(self.conf.dark_mode):
                    self.dark_btn.classes(add='hidden')
                else:
                    self.light_btn.classes(add='hidden')
            with ui.row().classes('items-center'):
                ui.label('在线运行:').classes('text-xl')
                on_air = ui.switch(on_change=lambda e: Config.update(on_air=e.value).execute(), value=bool(self.conf.on_air))
                on_air_token = ui.input('密钥(修改后重启生效)', password=True, value=self.conf.on_air_token).classes('w-48')
                ui.link('注册密钥', 'https://on-air.nicegui.io', new_tab=True)

            with ui.row().classes('items-center'):
                ui.label('窗口大小:').classes('text-xl')
                window_size = ui.select(
                    label='窗口大小(修改后重启生效)',
                    options={k: f"{w}x{h}" for k, (w, h) in WINDOW_SIZE.items()},
                    value=self.conf.window_size,
                    on_change=lambda e: Config.update(window_size=e.value).execute()
                ).classes('w-64')

            with ui.row().classes('items-center'):
                ui.label('邮件配置:').classes('text-xl')
                email = ui.input('邮箱地址', placeholder='请输入邮箱地址', value=self.conf.email)
                password = ui.input('邮箱密码/授权码', placeholder='请输入邮箱密码', password=True, value=self.conf.password)
                receiver = ui.input('收件人邮箱', placeholder='请输入收件人邮箱', value=self.conf.receiver)
            # with ui.row().classes('items-center'):
            #     ui.label('模拟器配置:').classes('text-xl')
            #     simulator_path = ui.input(label='MuMu模拟器路径', value=self.conf.simulator_path).style('width: 400px')
            with ui.row().classes('items-center'):
                ui.label('操作设置:').classes('text-xl')
                cap_tool = ui.select(label='截图工具', options=['MuMu', 'MiniCap', 'DroidCast', 'ADB'], value=self.conf.cap_tool).classes('w-32')
                touch_tool = ui.select(label='点击工具', options=['MuMu', 'MiniTouch', 'MaaTouch', 'ADB'], value=self.conf.touch_tool).classes('w-32')

            with ui.row().classes('w-full items-center'):
                ui.button('保存设置', on_click=lambda: _save_settings()).props('color=primary')
                ui.space()
                ui.button('打开操作手册', on_click=lambda: webbrowser.open('https://www.einzieg.site/'))
                ui.button('退出', color='negative', on_click=self.on_close)

        def _save_settings():
            """保存设置"""
            try:
                Config.update(email=email.value,
                              password=password.value,
                              receiver=receiver.value,
                              # simulator_path=simulator_path.value,
                              cap_tool=cap_tool.value,
                              touch_tool=touch_tool.value,
                              window_size=window_size.value,
                              on_air=on_air.value,
                              on_air_token=on_air_token.value,
                              ).execute()
                ui.notify('保存成功', type='positive')
            except Exception as e:
                ui.notify('保存失败', type='negative')
                logging.error(f"保存设置失败: {e}")

    def change_theme(self, is_dark):
        """切换主题并保存配置"""
        if is_dark:
            self.dark_btn.classes(add='hidden')
            self.light_btn.classes(remove='hidden')
            self.dark_mode.enable()
        else:
            self.dark_btn.classes(remove='hidden')
            self.light_btn.classes(add='hidden')
            self.dark_mode.disable()

        Config.update(dark_mode=is_dark).execute()
