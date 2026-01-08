import machine
import st7735
import time
import random

# --- 하드웨어 초기화 ---
spi = machine.SPI(2, baudrate=20000000, sck=machine.Pin(18), mosi=machine.Pin(23))
display = st7735.ST7735(spi, cs=machine.Pin(5), dc=machine.Pin(2), res=machine.Pin(4))

joy_x = machine.ADC(machine.Pin(34))
joy_y = machine.ADC(machine.Pin(35))
joy_x.atten(machine.ADC.ATTN_11DB)
joy_y.atten(machine.ADC.ATTN_11DB)

btn_restart = machine.Pin(32, machine.Pin.IN, machine.Pin.PULL_UP)
btn_fire_mode = machine.Pin(33, machine.Pin.IN, machine.Pin.PULL_UP)

BLACK, GREEN, RED, WHITE, YELLOW, CYAN = 0x0000, 0x07E0, 0xF800, 0xFFFF, 0xFFE0, 0x07FF

# --- 실시간 점수 표시 함수 ---
def show_live_score(score):
    # 점수 영역(0~40px)만 검은색으로 지우고 다시 쓰기
    display.fill_rect(5, 5, 40, 10, BLACK)
    display.text(str(score), 5, 5, WHITE)

# --- 게임 1: 장애물 피하기 ---
def play_avoid():
    display.fill(BLACK)
    p_x, p_y = 60, 140
    obs_x, obs_y = random.randint(0, 110), 0
    score, speed = 0, 7
    show_live_score(score)
    while True:
        display.fill_rect(p_x, p_y, 20, 7, BLACK)
        display.fill_rect(obs_x, obs_y, 12, 12, BLACK)
        vx = joy_x.read()
        if vx < 1000: p_x -= 8
        elif vx > 3000: p_x += 8
        p_x = max(0, min(p_x, 108))
        obs_y += speed
        if obs_y > 160:
            obs_y, obs_x = 0, random.randint(0, 110)
            score += 1
            show_live_score(score) # 점수 갱신
            speed = min(15, 7 + (score // 3))
        if (obs_y + 12 >= p_y and obs_x + 12 >= p_x and obs_x <= p_x + 20): return score
        display.fill_rect(p_x, p_y, 20, 7, CYAN)
        display.fill_rect(obs_x, obs_y, 12, 12, RED)
        time.sleep_ms(30)

# --- 게임 2: 스네이크 ---
def play_snake():
    display.fill(BLACK)
    snake = [[60, 80], [60, 90], [60, 100]]
    dx, dy = 0, -10
    food = [random.randrange(0, 120, 10), random.randrange(10, 150, 10)]
    score = 0
    show_live_score(score)
    while True:
        vx, vy = joy_x.read(), joy_y.read()
        if vx < 1000 and dx == 0: dx, dy = -10, 0
        elif vx > 3000 and dx == 0: dx, dy = 10, 0
        elif vy < 1000 and dy == 0: dx, dy = 0, -10
        elif vy > 3000 and dy == 0: dx, dy = 0, 10
        new_head = [snake[0][0] + dx, snake[0][1] + dy]
        if (new_head[0] < 0 or new_head[0] >= 120 or new_head[1] < 10 or new_head[1] >= 160 or new_head in snake):
            return score
        snake.insert(0, new_head)
        if new_head == food:
            score += 1
            show_live_score(score) # 점수 갱신
            food = [random.randrange(0, 120, 10), random.randrange(10, 150, 10)]
        else:
            tail = snake.pop()
            display.fill_rect(tail[0], tail[1], 9, 9, BLACK)
        display.fill_rect(food[0], food[1], 9, 9, RED)
        for p in snake: display.fill_rect(p[0], p[1], 9, 9, GREEN)
        time.sleep_ms(150)

# --- 게임 3: 우주선 ---
def play_space():
    display.fill(BLACK)
    ship_x, score = 60, 0
    enemies = [[random.randint(0, 110), random.randint(-50, 0)] for _ in range(5)]
    bullets = []
    last_fire = 0
    show_live_score(score)
    while True:
        vx = joy_x.read()
        display.fill_rect(ship_x, 140, 15, 10, BLACK)
        if vx < 1000: ship_x -= 8
        elif vx > 3000: ship_x += 8
        ship_x = max(0, min(ship_x, 113))
        if btn_fire_mode.value() == 0 and (time.ticks_ms() - last_fire > 200):
            bullets.append([ship_x + 6, 135])
            last_fire = time.ticks_ms()
        for b in bullets[:]:
            display.fill_rect(b[0], b[1], 3, 6, BLACK)
            b[1] -= 12
            if b[1] < 10: bullets.remove(b) # 점수 영역 보호 위해 10으로 수정
            else: display.fill_rect(b[0], b[1], 3, 6, YELLOW)
        for e in enemies:
            display.fill_rect(e[0], e[1], 10, 10, BLACK)
            e[1] += 4
            if e[1] > 160: e[1], e[0] = -10, random.randint(0, 110)
            for b in bullets[:]:
                if (e[0] - 5 < b[0] < e[0] + 12) and (e[1] - 5 < b[1] < e[1] + 12):
                    display.fill_rect(b[0], b[1], 3, 6, BLACK)
                    if b in bullets: bullets.remove(b)
                    score += 1
                    show_live_score(score) # 점수 갱신
                    e[1], e[0] = -10, random.randint(0, 110)
            if e[1] + 10 > 140 and e[0] + 10 > ship_x and e[0] < ship_x + 15: return score
            display.fill_rect(e[0], e[1], 10, 10, RED)
        display.fill_rect(ship_x, 140, 15, 10, CYAN)
        time.sleep_ms(30)

# --- 메인 루프 ---
game_mode = 0 
while True:
    if game_mode == 0: res = play_avoid()
    elif game_mode == 1: res = play_snake()
    else: res = play_space()

    display.fill(BLACK) 
    display.text("GAME OVER", 30, 55, RED)
    display.text("Score: " + str(res), 35, 75, YELLOW)
    display.text("SW : RESTART", 15, 120, GREEN)
    display.text("BTN: NEXT GAME", 15, 135, GREEN)
    
    while True:
        if btn_restart.value() == 0:
            time.sleep_ms(300)
            break 
        if btn_fire_mode.value() == 0:
            game_mode = (game_mode + 1) % 3
            time.sleep_ms(300)
            break
        time.sleep_ms(20)
