import machine
import time
import ustruct
import framebuf

class ST7735:
    def __init__(self, spi, cs, dc, res, width=128, height=160):
        self.spi = spi
        self.cs = cs
        self.dc = dc
        self.res = res
        self.width = width
        self.height = height
        self.init()

    def write_cmd(self, cmd):
        self.dc.value(0)
        self.cs.value(0)
        self.spi.write(bytearray([cmd]))
        self.cs.value(1)

    def write_data(self, data):
        self.dc.value(1)
        self.cs.value(0)
        self.spi.write(data)
        self.cs.value(1)

    def init(self):
        self.res.value(0)
        time.sleep_ms(50)
        self.res.value(1)
        time.sleep_ms(50)
        for cmd, data, delay in [
            (0x01, None, 150), (0x11, None, 500), (0x3A, b'\x05', 10),
            (0x2A, b'\x00\x00\x00\x7F', 10), (0x2B, b'\x00\x00\x00\x9F', 10),
            (0x29, None, 100)]:
            self.write_cmd(cmd)
            if data: self.write_data(data)
            if delay: time.sleep_ms(delay)

    def set_window(self, x0, y0, x1, y1):
        self.write_cmd(0x2A)
        self.write_data(ustruct.pack(">HH", x0, x1))
        self.write_cmd(0x2B)
        self.write_data(ustruct.pack(">HH", y0, y1))
        self.write_cmd(0x2C)

    def fill_rect(self, x, y, w, h, color):
        if x >= self.width or y >= self.height: return
        w = min(w, self.width - x)
        h = min(h, self.height - y)
        self.set_window(x, y, x + w - 1, y + h - 1)
        chunk = ustruct.pack(">H", color) * w
        for _ in range(h):
            self.write_data(chunk)

    def fill(self, color):
        self.fill_rect(0, 0, self.width, self.height, color)

    # 영문/숫자 출력 함수
    def text(self, string, x, y, color):
        text_w = len(string) * 8
        text_h = 8
        # 8x8 폰트 비트맵 버퍼 생성
        buf = bytearray(text_w * text_h // 8)
        fb = framebuf.FrameBuffer(buf, text_w, text_h, framebuf.MONO_VLSB)
        fb.text(string, 0, 0, 1)
        for cy in range(text_h):
            for cx in range(text_w):
                if fb.pixel(cx, cy):
                    # 픽셀이 1인 부분만 화면에 그리기
                    self.fill_rect(x + cx, y + cy, 1, 1, color)
