import asyncio
from nicegui import ui

async def async_task():
    ui.notify('Asynchronous task started')
    await asyncio.sleep(5)
    ui.notify('Asynchronous task finished')

ui.button('start async task', on_click=async_task)

ui.run(native=True)