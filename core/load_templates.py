from pathlib import Path

from models.Template import Template

ROOT_DIR = Path(__file__).resolve().parent.parent


class Templates:
    WRECKAGE = [
        Template(
            name="精英残骸",
            threshold=0.75,
            template_path=ROOT_DIR / "static/novaimgs/acquisition/elite_wreckage.png",
            forbidden=True,
        ),
        Template(
            name="小残骸",
            threshold=0.75,
            template_path=ROOT_DIR / "static/novaimgs/acquisition/alloy_wreckage.png",
            forbidden=True,
        ),
    ]

    MONSTER_NORMAL = [
        Template(
            name="2级普通精英",
            threshold=0.75,
            template_path=ROOT_DIR / "static/novaimgs/monsters/normal_lv2.png",
            forbidden=True,
        ),
        Template(
            name="3级普通精英",
            threshold=0.75,
            template_path=ROOT_DIR / "static/novaimgs/monsters/normal_lv3.png",
            forbidden=True,
        ),
        Template(
            name="4级普通精英",
            threshold=0.75,
            template_path=ROOT_DIR / "static/novaimgs/monsters/normal_lv4.png",
            forbidden=True,
        ),
    ]

    MONSTER_ELITE = [
        Template(
            name="6级首领",
            threshold=0.75,
            template_path=ROOT_DIR / "static/novaimgs/monsters/leader_lv6.png",
            forbidden=True,
        ),
        Template(
            name="5级首领",
            threshold=0.75,
            template_path=ROOT_DIR / "static/novaimgs/monsters/leader_lv5.png",
            forbidden=True,
        ),
        Template(
            name="4级首领",
            threshold=0.75,
            template_path=ROOT_DIR / "static/novaimgs/monsters/leader_lv4.png",
            forbidden=True,
        ),
        Template(
            name="6级精英",
            threshold=0.75,
            template_path=ROOT_DIR / "static/novaimgs/monsters/elite_lv6.png",
            forbidden=True,
        ),
        Template(
            name="5级精英",
            threshold=0.75,
            template_path=ROOT_DIR / "static/novaimgs/monsters/elite_lv5.png",
            forbidden=True,
        ),
    ]

    MONSTER_RED = [
        Template(
            name="流浪",
            threshold=0.75,
            template_path=ROOT_DIR / "static/novaimgs/red_invade/wandering.png",
            forbidden=True,
        ),
        Template(
            name="4级运输",
            threshold=0.75,
            template_path=ROOT_DIR / "static/novaimgs/red_invade/lv4_red_transport.png",
            forbidden=True,
        ),
        Template(
            name="6级节点",
            threshold=0.75,
            template_path=ROOT_DIR / "static/novaimgs/red_invade/lv6_node.png",
            forbidden=True,
        ),
    ]

    COLLECT = Template(
        name="采集",
        threshold=0.85,
        template_path=ROOT_DIR / "static/novaimgs/button/button_collect.png",
    )

    IN_BATTLE = Template(
        name="战斗中",
        threshold=0.85,
        template_path=ROOT_DIR / "static/novaimgs/identify_in/in_battle.png",
    )
