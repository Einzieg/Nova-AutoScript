import asyncio
from pathlib import Path

import cv2

from core.task.TaskBase import *
from models.Template import Template

ROOT_DIR = Path(__file__).resolve().parent.parent.parent.parent

IN_GAME = Template(
    name="IN_GAME",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/CARD_GAME/in_game.png"
)
EVENTS_GAME = Template(
    name="EVENTS_GAME",
    threshold=0.85,
    template_path=ROOT_DIR / "static/novaimgs/CARD_GAME/events_game.png"
)
CARDS = [
    Template(
        name="HERO",
        threshold=0.85,
        template_path=ROOT_DIR / "static/novaimgs/CARD_GAME/v1/HERO.png"
    ),
    Template(
        name="PLANET",
        threshold=0.85,
        template_path=ROOT_DIR / "static/novaimgs/CARD_GAME/v1/PLANET.png"
    ),
    Template(
        name="SHIP",
        threshold=0.85,
        template_path=ROOT_DIR / "static/novaimgs/CARD_GAME/v1/SHIP.png"
    ),
    Template(
        name="SPACE_STATION",
        threshold=0.85,
        template_path=ROOT_DIR / "static/novaimgs/CARD_GAME/v1/SPACE_STATION.png"
    ),
    Template(
        name="UNIT",
        threshold=0.85,
        template_path=ROOT_DIR / "static/novaimgs/CARD_GAME/v1/UNIT.png"
    ),
]


class BlessingFlip(TaskBase):

    def __init__(self, target):
        super().__init__(target)
        self.name = '星辰探宝'
        self.target = target

        self.x_start = 670
        self.y_start = 130
        self.card_width = 170
        self.card_height = 200
        self.x_gap = 15
        self.y_gap = 20
        self.card_templates = {}

        for template in CARDS:
            self.card_templates[template.name] = template.cv_tmp

    async def prepare(self):
        await super().prepare()
        self.logging.log('星辰探宝 开始...', self.target)

    async def execute(self):
        self._update_status(RUNNING)
        try:
            await self.play_game()
        except Exception as e:
            self.logging.log('星辰探宝 失败.', self.target)
            self._update_status(FAILED)
            raise e

    def get_card_position(self, row, col):
        x = self.x_start + col * (self.card_width + self.x_gap) + self.card_width // 2
        y = self.y_start + row * (self.card_height + self.y_gap) + self.card_height // 2
        return x, y

    def click_card(self, row, col):
        center = self.get_card_position(row, col)
        self.device.click(center)
        self.logging.log(f"点击卡牌 ({row}, {col})", self.target)

    def recognize_card(self, img, card_templates):
        best_match, best_score = None, 0.0
        for name, template in card_templates.items():
            res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
            _, max_val, _, _ = cv2.minMaxLoc(res)
            if max_val > best_score:
                best_match, best_score = name, max_val
        return best_match if best_score > 0.7 else None

    async def play_game(self):
        opened_cards = []
        flipped_cards = set()
        total_cards = 4 * 5

        while len(flipped_cards) < total_cards:
            opened = 0
            for i in range(4):
                for j in range(5):
                    if (i, j) not in flipped_cards:
                        self.click_card(i, j)

                        await asyncio.sleep(0.4)
                        screenshot_img = self.device.get_screencap()

                        x_start_card = self.x_start + j * (self.card_width + self.x_gap)
                        y_start_card = self.y_start + i * (self.card_height + self.y_gap)
                        x_end_card = x_start_card + self.card_width
                        y_end_card = y_start_card + self.card_height
                        card_region = screenshot_img[y_start_card:y_end_card, x_start_card:x_end_card]

                        card_name = self.recognize_card(card_region, self.card_templates)
                        self.logging.log(f"识别到卡牌 {card_name} ({i}, {j})", self.target)

                        if card_name:
                            found_entry = None
                            opened += 1
                            print(f"当前翻开{opened}张卡牌")
                            for entry in opened_cards:
                                if entry[0] == card_name and (entry[1], entry[2]) != (i, j):
                                    found_entry = entry
                                    break
                            if found_entry:
                                prev_row, prev_col = found_entry[1], found_entry[2]
                                flipped_cards.add((i, j))
                                flipped_cards.add((prev_row, prev_col))
                                opened_cards.remove(found_entry)
                                if opened == 2:
                                    await asyncio.sleep(1.5)
                                    self.click_card(i, j)
                                    await asyncio.sleep(0.4)
                                    self.click_card(prev_row, prev_col)
                                    await asyncio.sleep(1.5)
                                    opened = 0
                                else:
                                    self.click_card(prev_row, prev_col)
                                    await asyncio.sleep(1.5)
                                    opened = 0
                            else:
                                opened_cards.append((card_name, i, j))
                                flipped_cards.add((i, j))
                                await asyncio.sleep(1.2)
                                if opened == 2:
                                    opened = 0
                        else:
                            flipped_cards.add((i, j))
                            await asyncio.sleep(1)
