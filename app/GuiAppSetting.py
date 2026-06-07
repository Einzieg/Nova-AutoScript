import asyncio
import logging
import os
import subprocess
import sys
import webbrowser
from pathlib import Path

from nicegui import ui, app

from device_operation.check_update import CheckUpdate, GITHUB_RELEASES_URL, ReleaseAsset, UpdateCheckError, UpdateInfo
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
        self.update_checker = CheckUpdate()
        self.latest_update: UpdateInfo | None = None
        self.update_status_label = None
        self.update_check_btn = None
        self.update_download_btn = None
        self.update_release_btn = None
        self.update_progress = None
        self.update_progress_label = None
        self.update_notes_expansion = None
        self.update_notes_markdown = None

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

            self._create_update_settings()

            with ui.row().classes('items-center'):
                ui.label('邮件配置:').classes('text-xl')
                email = ui.input('邮箱地址', placeholder='请输入邮箱地址', value=self.conf.email)
                password = ui.input('邮箱密码/授权码', placeholder='请输入邮箱密码', password=True, value=self.conf.password)
                receiver = ui.input('收件人邮箱', placeholder='请输入收件人邮箱', value=self.conf.receiver)

            with ui.row().classes('items-center'):
                ui.label('操作设置:').classes('text-xl')
                cap_tool = ui.select(label='截图工具', options=['MuMu', 'MiniCap', 'DroidCast', 'ADB'], value=self.conf.cap_tool).classes('w-32')
                touch_tool = ui.select(label='点击工具', options=['MuMu', 'MiniTouch', 'MaaTouch', 'ADB'], value=self.conf.touch_tool).classes('w-32')

            with ui.row().classes('items-center'):
                ui.label('OCR设置:').classes('text-xl')
                ocr_tool = ui.select(label='OCR API', options=['RapidOcr', '腾讯', '百度', '有道', '云析'], value=self.conf.ocr_tool).classes('w-64')

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
                              cap_tool=cap_tool.value,
                              touch_tool=touch_tool.value,
                              ocr_tool=ocr_tool.value,
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

    def _create_update_settings(self):
        """创建应用更新区域"""
        with ui.column().classes('w-full gap-2'):
            with ui.row().classes('items-center'):
                ui.label('应用更新:').classes('text-xl')
                ui.label(f'当前版本: {self.update_checker.current_version}').classes('text-sm')
                self.update_status_label = ui.label('未检查').classes('text-sm')
                self.update_check_btn = ui.button('检查更新', icon='system_update', on_click=lambda: self.check_update())
                self.update_release_btn = ui.button('打开发布页', icon='open_in_new', on_click=self.open_release_page)
                self.update_download_btn = ui.button('下载更新包', icon='download', on_click=self.download_update).props('color=positive')
                self.update_release_btn.visible = False
                self.update_download_btn.visible = False

            with ui.row().classes('items-center'):
                self.update_progress = ui.linear_progress(0, show_value=False).classes('w-64')
                self.update_progress_label = ui.label('').classes('text-sm')
                self.update_progress.visible = False
                self.update_progress_label.visible = False

            self.update_notes_expansion = ui.expansion('更新内容', icon='article').classes('w-full')
            with self.update_notes_expansion:
                self.update_notes_markdown = ui.markdown('').classes('w-full')
            self.update_notes_expansion.visible = False

    async def check_update(self, silent: bool = False):
        """从 GitHub Releases 检查新版本"""
        if self.update_check_btn:
            self.update_check_btn.disable()
        if self.update_status_label:
            self.update_status_label.set_text('正在检查更新...')
        self._set_download_progress(0, 0, visible=False)
        self._set_update_notes()

        try:
            update_info = await asyncio.to_thread(self.update_checker.check_update)
            self.latest_update = update_info
            self._show_update_result(update_info, silent=silent)
        except UpdateCheckError as e:
            if self.update_status_label:
                self.update_status_label.set_text('检查失败')
            if not silent:
                ui.notify(f'检查更新失败: {e}', type='negative', multi_line=True)
            logging.warning(f"检查更新失败: {e}")
        finally:
            if self.update_check_btn:
                self.update_check_btn.enable()

    async def check_update_silently(self):
        await self.check_update(silent=True)

    def _show_update_result(self, update_info: UpdateInfo, *, silent: bool):
        if update_info.is_update_available:
            asset_size = f'，{self._format_size(update_info.asset.size)}' if update_info.asset else ''
            message = f'发现新版本 {update_info.latest_version}{asset_size}'
            if self.update_status_label:
                self.update_status_label.set_text(message)
            if self.update_release_btn:
                self.update_release_btn.visible = True
            if self.update_download_btn:
                self.update_download_btn.visible = bool(update_info.asset)
            self._set_update_notes(update_info)
            ui.notify(f'{message}\n可在设置页下载更新包。', type='positive', multi_line=True)
            return

        if self.update_status_label:
            self.update_status_label.set_text('当前已是最新版本')
        if self.update_release_btn:
            self.update_release_btn.visible = False
        if self.update_download_btn:
            self.update_download_btn.visible = False
        self._set_update_notes()
        if not silent:
            ui.notify('当前已是最新版本', type='positive')

    async def download_update(self):
        if not self.latest_update:
            await self.check_update()
            if not self.latest_update:
                return

        if not self.latest_update.is_update_available:
            ui.notify('当前已是最新版本', type='positive')
            return

        if not self.latest_update.asset:
            ui.notify('该发布版本没有可下载资源，已打开发布页', type='warning')
            self.open_release_page()
            return

        if self.update_download_btn:
            self.update_download_btn.disable()
        if self.update_status_label:
            self.update_status_label.set_text('正在下载更新包...')
        self._set_download_progress(0, self.latest_update.asset.size, visible=True)

        try:
            download_path = await self._download_asset_with_progress(self.latest_update.asset)
            if self.update_status_label:
                self.update_status_label.set_text(f'已下载到: {download_path}')
            self._set_download_finished_progress()
            ui.notify('更新包下载完成', type='positive')
            self._show_download_finished_dialog(download_path)
        except UpdateCheckError as e:
            if self.update_status_label:
                self.update_status_label.set_text('下载失败')
            ui.notify(f'下载更新包失败: {e}', type='negative', multi_line=True)
            logging.warning(f"下载更新包失败: {e}")
        finally:
            if self.update_download_btn:
                self.update_download_btn.enable()

    async def _download_asset_with_progress(self, asset: ReleaseAsset):
        progress_queue: asyncio.Queue[tuple[int, int]] = asyncio.Queue()
        loop = asyncio.get_running_loop()

        def report(downloaded: int, total: int):
            loop.call_soon_threadsafe(progress_queue.put_nowait, (downloaded, total))

        download_task = asyncio.create_task(
            asyncio.to_thread(self.update_checker.download_asset, asset, None, report)
        )

        while not download_task.done():
            try:
                downloaded, total = await asyncio.wait_for(progress_queue.get(), timeout=0.1)
                self._set_download_progress(downloaded, total, visible=True)
            except asyncio.TimeoutError:
                continue

        while not progress_queue.empty():
            downloaded, total = progress_queue.get_nowait()
            self._set_download_progress(downloaded, total, visible=True)

        return await download_task

    def _set_download_progress(self, downloaded: int, total: int, *, visible: bool):
        if self.update_progress is not None:
            progress = min(downloaded / total, 1.0) if total > 0 else 0
            self.update_progress.set_value(progress)
            self.update_progress.visible = visible
        if self.update_progress_label is not None:
            if visible and total > 0:
                percent = min(downloaded / total, 1.0) * 100
                text = f'下载进度: {percent:.1f}% ({self._format_size(downloaded)} / {self._format_size(total)})'
            elif visible:
                text = f'已下载: {self._format_size(downloaded)}'
            else:
                text = ''
            self.update_progress_label.set_text(text)
            self.update_progress_label.visible = visible

    def _set_download_finished_progress(self):
        if self.update_progress is not None:
            self.update_progress.set_value(1)
            self.update_progress.visible = True
        if self.update_progress_label is not None:
            self.update_progress_label.set_text('下载进度: 100%')
            self.update_progress_label.visible = True

    def _set_update_notes(self, update_info: UpdateInfo | None = None):
        if self.update_notes_expansion is None or self.update_notes_markdown is None:
            return

        if not update_info or not update_info.is_update_available:
            self.update_notes_expansion.visible = False
            self.update_notes_expansion.set_value(False)
            self.update_notes_markdown.set_content('')
            return

        body = update_info.body.strip() or '该版本没有填写更新内容。'
        notes = (
            f'### {update_info.release_name}\n\n'
            f'版本: `{update_info.latest_version}`\n\n'
            f'{body}\n\n'
            f'[查看 GitHub Release]({update_info.release_url})'
        )
        self.update_notes_markdown.set_content(notes)
        self.update_notes_expansion.visible = True
        self.update_notes_expansion.set_value(True)

    def open_release_page(self):
        url = self.latest_update.release_url if self.latest_update else GITHUB_RELEASES_URL
        webbrowser.open(url)

    def _show_download_finished_dialog(self, download_path: Path):
        with ui.dialog() as dialog, ui.card():
            with ui.column().classes('gap-2'):
                ui.label('更新包下载完成').classes('text-xl')
                ui.label(str(download_path)).classes('text-sm')
                ui.label('请退出程序后，解压更新包并覆盖旧版本。').classes('text-sm')
                with ui.row().classes('justify-end'):
                    ui.button('打开所在文件夹', icon='folder_open',
                              on_click=lambda: self._open_download_folder(download_path))
                    ui.button('关闭', on_click=dialog.close)
        dialog.open()

    @staticmethod
    def _open_download_folder(download_path: Path):
        folder = download_path.parent
        try:
            if sys.platform.startswith('win'):
                os.startfile(folder)
            elif sys.platform == 'darwin':
                subprocess.Popen(['open', str(folder)])
            else:
                subprocess.Popen(['xdg-open', str(folder)])
        except Exception as e:
            logging.warning(f"打开下载目录失败: {e}")
            webbrowser.open(folder.as_uri())

    @staticmethod
    def _format_size(size: int) -> str:
        if size <= 0:
            return '未知大小'
        units = ['B', 'KB', 'MB', 'GB']
        value = float(size)
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f'{value:.1f} {unit}' if unit != 'B' else f'{int(value)} {unit}'
            value /= 1024
        return f'{size} B'
