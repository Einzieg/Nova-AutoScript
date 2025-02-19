from nicegui import ui, app

from device_operation.SQLiteClient import SQLiteClient


class GuiAppSetting:
    def __init__(self):
        self.db = SQLiteClient()

    @staticmethod
    def on_close():
        """关闭应用"""
        ui.notify('应用已关闭')
        app.shutdown()

    @staticmethod
    def _bool_to_blob(value):
        """将布尔值转换为 BLOB"""
        return bytes([int(value)])

    @staticmethod
    def _blob_to_bool(blob):
        """将 BLOB 转换为布尔值"""
        return bool(blob[0]) if blob else True  # 默认深色模式

    def on_startup(self):
        """应用启动时加载主题配置"""
        result = self.db.fetch_one("SELECT dark_mode FROM config WHERE id = 1")
        if result:
            is_dark = self._blob_to_bool(result['dark_mode'])
            if is_dark:
                ui.dark_mode().enable()
            else:
                ui.dark_mode().disable()

    def create_setting_tab_panel(self):
        """创建Setting标签页内容"""
        with ui.tab_panel('设置'):
            # 主题切换按钮
            with ui.row().classes('items-center'):
                ui.label('切换主题:').classes('text-xl')
                ui.button('深色模式', icon='dark_mode', on_click=lambda: self.change_theme(True)).props('color=dark text-color=white')
                ui.button('浅色模式', icon='light_mode',  on_click=lambda: self.change_theme(False)).props('color=white text-color=black')

            ui.button('关闭', on_click=self.on_close)

    def change_theme(self, is_dark):
        """切换主题并保存配置"""
        if is_dark:
            ui.dark_mode().enable()  # 切换到深色模式
        else:
            ui.dark_mode().disable()  # 切换到浅色模式

        # 保存主题配置到数据库
        self.db.execute_update("UPDATE config SET dark_mode = ? WHERE id = 1", (self._bool_to_blob(is_dark),))
