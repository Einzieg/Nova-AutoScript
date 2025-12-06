import re


class TimeTools:

    def __init__(self):
        pass

    @staticmethod
    def _to_half_width(s: str) -> str:
        # 把全角数字和全角冒号等转换为半角
        def conv(ch):
            code = ord(ch)
            # 全角数字 ０(65296) - ９(65305) 对应 48-57
            if 0xFF10 <= code <= 0xFF19:
                return chr(code - 0xFF10 + 48)
            # 全角冒号
            if ch == '：':
                return ':'
            return ch

        return ''.join(conv(c) for c in s)

    def parse_duration_to_seconds(self, s: str) -> int:
        """
        解析类似 '1天07：32：43' / '1天07:32:43' / '07:32' / '32' 等为秒数。
        返回整数秒数。
        """
        if not s:
            return 0
        s = self._to_half_width(s).strip()
        days = 0
        if '天' in s:
            left, right = s.split('天', 1)
            # 提取数字，避免干扰字符
            m = re.search(r'\d+', left)
            if m:
                days = int(m.group())
            s = right.strip()
        if not s:
            return days * 86400

        # 保留数字和冒号，然后按 ':' 切分
        s = re.sub(r'[^\d:]', '', s)
        parts = s.split(':') if s else []

        # 从右往左解析为 秒/分/时
        sec = 0
        if len(parts) >= 3:
            h = int(parts[-3]) if parts[-3] else 0
            m = int(parts[-2]) if parts[-2] else 0
            sec = int(parts[-1]) if parts[-1] else 0
        elif len(parts) == 2:
            h = 0
            m = int(parts[0]) if parts[0] else 0
            sec = int(parts[1]) if parts[1] else 0
        elif len(parts) == 1 and parts[0] != '':
            # 单数字视为秒
            h = 0
            m = 0
            sec = int(parts[0])
        else:
            h = m = sec = 0

        return days * 86400 + h * 3600 + m * 60 + sec


# 示例
if __name__ == '__main__':
    time_tools = TimeTools()
    print(time_tools.parse_duration_to_seconds('1天07：32：43'))  # 113563
    print(time_tools.parse_duration_to_seconds('1天07:32:43'))  # 113563
    print(time_tools.parse_duration_to_seconds('07:32:43'))  # 27163
    print(time_tools.parse_duration_to_seconds('07:32'))  # 452
    print(time_tools.parse_duration_to_seconds('32'))  # 32
