import json

from nicegui import ui

from core.task.daily_tasks.Order import Order
from core.task.daily_tasks.Radar import Radar
from core.task.outer_tasks.BlessingFlip import BlessingFlip
from core.task.test_tasks.ChangeAlloys import ChangeAlloys
from core.task.test_tasks.ScreenshotTest import ScreenshotTest
from models.Module import Module


class GuiAppConfigurationTabs:

    def __init__(self, app):
        self.app = app

    def create_configuration_tabs(self, tab_name):
        with ui.tabs().classes('w-full') as tabs:
            basic = ui.tab('基础配置')
            daily = ui.tab('日常任务')
            permanent = ui.tab('常驻任务')
            events = ui.tab('活动任务')
            outer = ui.tab('其他任务')
            quick = ui.tab('快速执行')

        with ui.tab_panels(tabs, value=basic).classes('w-full').style('height:26vw;overflow-y:auto;' if self.app.conf.window_size != 1 else 'max-height:40vh;overflow-y:auto;'):
            module = Module.get_or_none(Module.name == tab_name)

            with ui.tab_panel(basic):
                with ui.card().classes('w-full'):
                    with ui.row().classes('w-full items-center'):
                        ui.number(label='模拟器编号/端口',
                                  precision=0,
                                  min=0,
                                  on_change=lambda e: Module.update(simulator_index=e.value).where(Module.name == tab_name).execute(),
                                  value=module.simulator_index,
                                  ).classes('w-30')
                        ui.checkbox(text='启动时打开模拟器(仅支持MuMu)',
                                    on_change=lambda e: Module.update(autostart_simulator=e.value).where(Module.name == tab_name).execute(),
                                    value=bool(module.autostart_simulator)
                                    )
                with ui.card().classes('w-full'):
                    with ui.row().classes('w-full items-center'):
                        ui.switch(text='自动抢登',
                                  on_change=lambda e: Module.update(auto_relogin=e.value).where(Module.name == tab_name).execute(),
                                  value=bool(module.auto_relogin)
                                  )
                        ui.label().classes('w-10')
                        ui.number(label='抢登等待时间(s)',
                                  min=0,
                                  placeholder='默认600秒',
                                  on_change=lambda e: Module.update(relogin_time=e.value).where(Module.name == tab_name).execute(),
                                  value=module.relogin_time
                                  )

                with ui.card().classes('w-full'):
                    with ui.row().classes('w-full items-center'):
                        ui.select(
                            label='出击舰队',
                            options={'all': '全选', 'fleet1': '舰队1', 'fleet2': '舰队2', 'fleet3': '舰队3', 'fleet4': '舰队4', 'fleet5': '舰队5', 'fleet6': '舰队6'},
                            on_change=lambda e: Module.update(attack_fleet=json.dumps(e.value)).where(Module.name == tab_name).execute(),
                            value=json.loads(module.attack_fleet),
                            multiple=True
                        ).classes('w-64').props('use-chips')
                        ui.select(
                            label='执行任务',
                            options={'daily': '日常任务', 'permanent': '常驻任务', 'events': '活动任务', 'outer': '其他任务'},
                            on_change=lambda e: Module.update(task_type=json.dumps(e.value)).where(Module.name == tab_name).execute(),
                            value=json.loads(module.task_type),
                            multiple=True,
                        ).classes('w-64').props('use-chips')

                        with ui.input(label='常驻任务停止时间',
                                      placeholder='默认不停止',
                                      on_change=lambda e: Module.update(stop_time=e.value).where(Module.name == tab_name).execute(),
                                      value=module.stop_time,
                                      ) as time:
                            with ui.menu().props('no-parent-event') as menu:
                                with ui.time().props('landscape').bind_value(time):
                                    with ui.row().classes('justify-end'):
                                        ui.button('Close', on_click=menu.close).props('flat')
                            with time.add_slot('append'):
                                ui.icon('access_time').on('click', menu.open).classes('cursor-pointer')

            with ui.tab_panel(daily):
                with ui.card().classes('w-full'):
                    with ui.row().classes('w-full items-center'):
                        ui.switch(text='完成战斗')
                        ui.select(options=['5', '10', '15'])
                        ui.label('次')
                with ui.card().classes('w-full'):
                    with ui.row().classes('w-full items-center'):
                        ui.switch(text='联盟捐献')
                        ui.number(min=0, max=6).classes('w-36')
                        ui.label('次')
                with ui.card().classes('w-full'):
                    with ui.row().classes('w-full items-center'):
                        ui.switch(text='联盟商店购买')
                        ui.select(options=['神经插入槽', '维修机器人', '舰长经验', '科研加速', '部件加速', '超空间信标', '跃升元件', '合金', '水晶', '订单电路板'],
                                  multiple=True).classes('w-64').props('use-chips')
                with ui.card().classes('w-full'):
                    with ui.row().classes('w-full items-center'):
                        ui.switch(text='完成订单')
                        ui.number(min=0).classes('w-36')
                        ui.label('批次')
                with ui.card().classes('w-full'):
                    with ui.row().classes('w-full items-center'):
                        ui.switch(text='完成深空探索')
                        ui.number(placeholder='默认最大次数').classes('w-36')
                        ui.label('次')
                with ui.card().classes('w-full'):
                    with ui.row().classes('w-full items-center'):
                        ui.switch(text='完成势力任务')
                        ui.number(min=0, max=5).classes('w-36')
                        ui.label('次')
                with ui.card().classes('w-full'):
                    with ui.row().classes('w-full items-center'):
                        ui.switch(text='消耗雷达能量')
                        ui.number(min=0).classes('w-36')
                        ui.label('次')
                with ui.card().classes('w-full'):
                    with ui.row().classes('w-full items-center'):
                        ui.switch(text='完成成员任务')
                        ui.select(options=['采集残骸', '击杀清道夫', '歼灭精英清道夫']).classes('w-36')
                        ui.number(min=0, max=4).classes('w-36')
                        ui.label('次')
                with ui.card().classes('w-full'):
                    with ui.row().classes('w-full items-center'):
                        ui.switch(text='采集残骸')
                        ui.number(min=0).classes('w-36')
                        ui.label('次')

            with ui.tab_panel(permanent):
                with ui.card().classes('w-full h-full'):
                    ui.switch(text='普通清道夫',
                              on_change=lambda e: Module.update(normal_monster=e.value).where(Module.name == tab_name).execute(),
                              value=bool(module.normal_monster)
                              )
                    ui.switch(text='精英清道夫',
                              on_change=lambda e: Module.update(elite_monster=e.value).where(Module.name == tab_name).execute(),
                              value=bool(module.elite_monster)
                              )
                    ui.switch(text='深红入侵',
                              on_change=lambda e: Module.update(red_monster=e.value).where(Module.name == tab_name).execute(),
                              value=bool(module.red_monster)
                              )
                    ui.switch(text='采集残骸',
                              on_change=lambda e: Module.update(wreckage=e.value).where(Module.name == tab_name).execute(),
                              value=bool(module.wreckage)
                              )
            with ui.tab_panel(events):
                ui.label('活动 tab')
            with ui.tab_panel(outer):
                with ui.card().classes('w-full h-full'):
                    ui.switch(text='刷隐秘',
                              on_change=lambda e: Module.update(hidden_switch=e.value).where(Module.name == tab_name).execute(),
                              value=bool(module.hidden_switch)
                              )
                    with ui.row().classes('w-full h-full items-center'):
                        ui.select(label='隐秘策略',
                                  options=['不使用能量道具', '使用能量道具', '使用GEC购买能量'],
                                  on_change=lambda e: Module.update(hidden_policy=e.value).where(Module.name == tab_name).execute(),
                                  value=module.hidden_policy
                                  ).classes('w-48')
                        ui.number(label='隐秘次数',
                                  placeholder='默认不限制次数',
                                  on_change=lambda e: Module.update(hidden_times=e.value).where(Module.name == tab_name).execute(),
                                  value=module.hidden_times
                                  ).classes('w-48')
                        ui.switch(text='采集残骸',
                                  on_change=lambda e: Module.update(hidden_wreckage=e.value).where(Module.name == tab_name).execute(),
                                  value=bool(module.hidden_wreckage)
                                  )
                with ui.card().classes('w-full h-full'):
                    ui.switch(text='做订单',
                              on_change=lambda e: Module.update(order_switch=e.value).where(Module.name == tab_name).execute(),
                              value=bool(module.order_switch)
                              )
                    with ui.row().classes('w-full h-full items-center'):
                        ui.select(label='订单策略',
                                  options=['使用超空间信标', '不使用超空间信标', '使用GEC购买信标'],
                                  on_change=lambda e: Module.update(order_policy=e.value).where(Module.name == tab_name).execute(),
                                  value=module.order_policy
                                  ).classes('w-38')
                        ui.select(label='加速策略',
                                  options=['使用订单电路板', '使用制造加速'],
                                  on_change=lambda e: Module.update(order_hasten_policy=e.value).where(Module.name == tab_name).execute(),
                                  value=module.order_hasten_policy
                                  ).classes('w-38')
                        ui.number(label='订单次数',
                                  placeholder='默认不限制次数',
                                  on_change=lambda e: Module.update(order_times=e.value).where(Module.name == tab_name).execute(),
                                  value=module.order_times
                                  ).classes('w-36')
                with ui.card().classes('w-full h-full'):
                    with ui.row().classes('w-full h-full items-center'):
                        ui.switch(text='制造维修机器人'
                                  )
                        ui.number()
                        ui.label('批次')
            with ui.tab_panel(quick):
                ui.button('星辰探宝', on_click=lambda: self.quick_run(tab_name, BlessingFlip)).props('color=green')
                ui.button('隐秘', on_click=lambda: self.quick_run(tab_name, Radar)).props('color=green')
                ui.button('订单', on_click=lambda: self.quick_run(tab_name, Order)).props('color=green')
                ui.button('截图测试', on_click=lambda: self.quick_run(tab_name, ScreenshotTest)).props('color=green')
                ui.button('换合金', on_click=lambda: self.quick_run(tab_name, ChangeAlloys)).props('color=green')

    def quick_run(self, tab_name, task):
        if self.app.target_running[tab_name]:
            ui.notify('任务正在运行中', color='red')
            return
        self.app.quick_start(tab_name, task)
