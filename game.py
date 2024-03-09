import pygame
import sys
import random
import json
from typing import Literal


Active = Literal['game', 'none', 'pause']
SIDE = Literal['left', 'right']


WIDTH = 620
BORDER_HEIGT = 65
GAME_TOP = BORDER_HEIGT
GAME_HEIGHT = 500
HEIGHT = 2 * BORDER_HEIGT + GAME_HEIGHT
SIZE = WIDTH, HEIGHT


# 时间系统
class TimeSys:
    COOL = 20_000  # 20s
    # 这个宽高包含边界
    bar_WIDTH = 450
    bar_HEIGHT = 25
    right_MARGIN = 10
    bar_BORDER = 3
    # 时间条的边框
    rect1 = (
        WIDTH - right_MARGIN - bar_WIDTH,
        (BORDER_HEIGT - bar_HEIGHT) / 2,
        bar_WIDTH,
        bar_HEIGHT
    )
    # 时间条的内部
    rect2 = (
        WIDTH - right_MARGIN - bar_WIDTH + bar_BORDER,
        (BORDER_HEIGT - bar_HEIGHT) / 2 + bar_BORDER,
        bar_WIDTH - 2 * bar_BORDER,
        bar_HEIGHT - 2 * bar_BORDER
    )
    def __init__(self, game: "Game") -> None:
        self._game = game
        # 记录tick
        self.lock_tick = pygame.time.get_ticks()
        # 记录剩余的时间
        self.left_time = self.COOL
        # 转化rect2
        self.rect2 = pygame.Rect(self.rect2)



    def update(self, active: Active):
        current_time = pygame.time.get_ticks()
        delta_time = current_time - self.lock_tick
        self.lock_tick = current_time
        if active == 'game':
            self.left_time -= delta_time
            if self.left_time < 0:
                self._game.shitf('none')

    
    def draw(self, surface: pygame.Surface, active: Active):
        if active != 'game':
            return
        # 背景
        pygame.draw.rect(surface, "#000000", (0, 0, WIDTH, BORDER_HEIGT))
        # 数字
        image = self._game.font.render(f"Time: {int(round(self.left_time / 1000))}", True, "#FFFFFF")
        rect = image.get_rect(midleft=(0, BORDER_HEIGT / 2))
        surface.blit(image, rect)
        # 时间条边框
        pygame.draw.rect(surface, "#6A6A6A", self.rect1, self.bar_BORDER)
        # 时间条内容
        right = self.rect2.right
        width = self.left_time * self.rect2.width / self.COOL
        # 时间多余上限会绘制新的颜色
        for color in ("#00A2E8","#3F48CC","#A349A4"):
            if width > self.rect2.width:
                pygame.draw.rect(surface, color, self.rect2)
                width -= self.rect2.width
            else:
                rect = self.rect2.copy()
                rect.width = width
                rect.right = right
                pygame.draw.rect(surface, color, rect)
                break


    def re_start(self):
        self.left_time = self.COOL
        self.lock_tick = pygame.time.get_ticks()

    
    def add_time(self, time: int):
        self.left_time += time
        

# 分数系统
class ScoreSys:
    def __init__(self ,font: pygame.font.Font) -> None:
        self._font = font
        self.max_score = self.get_max_score()
        self.score = 0
        # 是否是新高分
        self.new_high_score = False


    @staticmethod
    def get_max_score():
        with open(r'data\max_score.json') as file:
            return json.load(file)
        
    
    def save_max_score(self):
        with open(r'data\max_score.json', mode='w') as file:
            json.dump(self.max_score, file)

    
    def add(self ,score: int):
        self.score += score
        if self.max_score < self.score:
            self.max_score = self.score
            self.new_high_score = True

    
    def draw(self, surface: pygame.surface.Surface):
        # 背景
        pygame.draw.rect(surface, "#000000", (0, BORDER_HEIGT + GAME_HEIGHT, WIDTH, BORDER_HEIGT))
        # 得分
        image = self._font.render(f'Score: {self.score}', True, "#FFFFFF")
        rect = image.get_rect(midleft=(0, GAME_HEIGHT + 1.5 * BORDER_HEIGT))
        surface.blit(image, rect)
        # 最高分
        image = self._font.render(f'Max score: {self.max_score}', True, "#FFFFFF")
        rect = image.get_rect(midright=(WIDTH, GAME_HEIGHT + 1.5 * BORDER_HEIGT))
        surface.blit(image, rect)

    
    def re_start(self):
        self.score = 0
        self.new_high_score = False


# 泡泡
class Bubble(pygame.sprite.Sprite):
    # 半径，用于碰撞
    radius = 54
    # 死亡播放动画间隔时间
    die_anim_COOL = 50  # 0.5s

    def __init__(self, sys: "BubbleSys", kind: int, pos: pygame.Vector2, speed: pygame.Vector2) -> None:
        super().__init__(sys)
        self._sys = sys
        # 正在死
        self.dying = False
        # 记录死亡的时刻
        self.die_tick = None
        # 类型
        self.kind = kind
        # 动画
        self.animation = self._sys.images[self.kind]
        # 动画的索引
        self.animation_index = 0
        # 位置，用于移动
        self.pos = pos
        # image
        self.image = self.animation[self.animation_index]
        self.rect = self.image.get_rect(center=self.pos)
        # 速度
        self.speed = speed


    def update(self) -> None:
        if self.dying:
            if pygame.time.get_ticks() - self.die_tick >= self.die_anim_COOL:
                self.die_tick += self.die_anim_COOL
                self.animation_index += 1
                if self.animation_index < 6:
                    self.image = self.animation[self.animation_index]
                else:
                    self.kill()
        else:
            self.pos += self.speed
            self.rect.center = self.pos
            if not self.rect.colliderect(-50, GAME_TOP - 50, WIDTH + 100, GAME_HEIGHT + 100):
                self.kill()


    def die(self):
        self.dying = True
        self.die_tick = pygame.time.get_ticks()

        
# 泡泡管理系统  
class BubbleSys(pygame.sprite.Group):
    # bubble_COOL = 500  # 0.5s

    def __init__(self, game: "Game") -> None:
        super().__init__()
        self._game = game
        # 载入图片
        self.images = [
            [pygame.transform.scale(pygame.image.load(f'image/white/{i}.png'), (120, 120)) for i in range(6)],
            [pygame.transform.scale(pygame.image.load(f'image/green/{i}.png'), (120, 120)) for i in range(6)],
            [pygame.transform.scale(pygame.image.load(f'image/red/{i}.png'), (120, 120)) for i in range(6)],
            [pygame.transform.scale(pygame.image.load(f'image/colorful/{i}.png'), (120, 120)) for i in range(6)],
        ]
        # 速度
        self.speed = [
            (0.6, 2),
            (0.6, 1),
            (1, 2),
            (1.2, 2)
        ]
        # 声音
        self.sound = [
            pygame.mixer.Sound(f"sound/{i}.wav") for i in range(4)
        ]
        # 定时生成泡泡
        self.lock_tick: int = pygame.time.get_ticks()
        self.used_time = 0
    

    def add_bubble(self):
        # kind
        kind = random.randint(0, 9)
        if kind > 3:
            kind = 0
        # 位置
        pos, side = self.get_random_pos_side()
        # 速度
        speed = self.get_random_speed(kind, side)

        self.add(Bubble(self, kind, pos, speed))

    
    def get_random_speed(self, kind:int, side: SIDE) -> pygame.Vector2:
        """获取随机速度"""
        return pygame.Vector2(
            random.uniform(*self.speed[kind]) * 0.5 if side == 'left' else -0.5,
            random.uniform(*self.speed[kind])
        )
    

    def handle_click(self, pos: pygame.Vector2):
        """处理点击"""
        min_bubble: Bubble | None = None
        bubble: Bubble
        min_length = Bubble.radius
        for bubble in self:
            l = (pos - bubble.pos).length()
            if l < min_length:
                min_bubble = bubble
        if min_bubble is not None:
            self.handle_dead_bubble(min_bubble)
            min_bubble.die()
            random.choice(self.sound).play()

    
    def handle_dead_bubble(self, bubble: Bubble):
        """根据bubble种类的不同，有不同作用"""
        self._game.handle_dead_bubble(bubble.kind)


    def update(self, active: Active):
        if active == 'game':
            self.random_add_bubble()
            super().update()


    def re_start(self):
        self.empty()
    
    def random_add_bubble(self):
        """有概率生成泡泡"""
        if not random.randint(0, 2 * len(self)):
            self.add_bubble()

    
    @staticmethod
    def get_random_pos_side() -> tuple[pygame.Vector2, SIDE]:
        """获取随机位置"""
        if random.randint(0, 1):
            # 上部
            x = random.uniform(GAME_TOP - Bubble.radius, WIDTH + Bubble.radius)
            y = GAME_TOP - Bubble.radius
        elif random.randint(0, 1):
            # 左
            x = -Bubble.radius
            y = random.uniform(GAME_TOP - Bubble.radius, GAME_TOP + GAME_HEIGHT / 2)
        else:
            # 右
            x = WIDTH + Bubble.radius
            y = random.uniform(GAME_TOP - Bubble.radius, GAME_TOP + GAME_HEIGHT / 2)
        side = 'left' if x < WIDTH / 2 else 'right'
        return pygame.Vector2(x, y), side


# 菜单
class Menu:
    """
    Press any key to start/continue the game
    Transparent bubble: Score
    Red bubble: Add time
    Green bubble: Don't click
    Colorful bubble: Extra points
    New high score:
    """
    
    def __init__(self, game: "Game") -> None:
        self._game = game
        self.font = pygame.font.Font(r'font\ark-pixel-12px.otf', 25)
        # 第一行
        self.first_text = {
            'none': self._game.font.render(
                'Press any key to start the game',
                True, "#000000"
            ),
            'pause': self._game.font.render(
                'Press any key to resume the game',
                True, "#000000"
            )
        }
        # 中间部分
        info_images = [
            self.font.render("Transparent bubble: Score", True, "#FFFFFF"),
            self.font.render("Red bubble: Add time", True, "#DD0A4C"),
            self.font.render("Green bubble: Don't click", True, "#2F6C32"),
        ]
        self.info = [
            (info, info.get_rect(center=(WIDTH / 2, (BORDER_HEIGT + GAME_HEIGHT) * (2 * i + 5) / 16)))
            for i, info in enumerate(info_images)
        ]
        # 彩虹色
        self.colorful_text = [
            self.font.render("Colorful bubble: Extra scores", True, "#ED1C24"),
            self.font.render("Colorful bubble: Extra scores", True, "#FF7F27"),
            self.font.render("Colorful bubble: Extra scores", True, "#FFF200"),
            self.font.render("Colorful bubble: Extra scores", True, "#22B14C"),
            self.font.render("Colorful bubble: Extra scores", True, "#00A2E8"),
            self.font.render("Colorful bubble: Extra scores", True, "#3F48CC"),
            self.font.render("Colorful bubble: Extra scores", True, "#A349A4"),
        ]
        self.colorful_rect = (
            self.colorful_text[0]
            .get_rect(center=(WIDTH / 2, (BORDER_HEIGT + GAME_HEIGHT) * 11 / 16))
        )
        # 新高分
        self.new_heigh_socre: pygame.Surface | None = None


    
    def draw(self, surface: pygame.Surface, active: Active, new_high_score: bool):
        current_time = pygame.time.get_ticks()
        # 第一行
        first_text = self.first_text[active]
        rect = first_text.get_rect(center=(WIDTH / 2, (BORDER_HEIGT + GAME_HEIGHT) / 8))
        surface.blit(first_text, rect)
        # 中间部分
        surface.blits(self.info)
        surface.blit(
            self.colorful_text[current_time // 1000 % 7],
            self.colorful_rect
        )
        # 新高分
        if new_high_score and active == 'none':
            if self.new_heigh_socre is None:
                self.new_heigh_socre = self._game.font.render(
                    f'New high score: {self._game.score_sys.max_score}', True, "#000000"
                )
            rect = self.new_heigh_socre.get_rect(center=(WIDTH / 2, (BORDER_HEIGT + GAME_HEIGHT) * 7 / 8))
            # 上下起伏
            rect.move_ip(0, abs(current_time // 50 % 40 - 20) - 10)
            surface.blit(self.new_heigh_socre, rect)


    def re_start(self):
        self.new_heigh_socre = None



# 基础game组件
class Windows:
    def __init__(self) -> None:
        pygame.init()
        pygame.mixer.init()
        pygame.font.init()
        self.surface = pygame.display.set_mode(SIZE)
        self.clock = pygame.time.Clock()
        self.quit = False


    def control(self):
        ...


    def update(self):
        ...


    def draw(self):
        pygame.display.flip()


    def run(self):
        while not self.quit:
            self.control()
            self.update()
            self.draw()
            self.clock.tick(60)
        self.safe_quit()


    def safe_quit(self):
        pygame.quit()
        sys.exit()


# 游戏
class Game(Windows):
    def __init__(self) -> None:
        super().__init__()
        pygame.display.set_caption("Bubble Pop")
        pygame.display.set_icon(pygame.image.load("image/colorful/0.png"))
        # 背景颜色
        self.bg_colors = [
            "#7092BE", "#C8BFE7", "#99D9EA", "#EFE4B0", "#8EEB96", "#EDB58B"
        ]
        self.bg_color = random.choice(self.bg_colors)
        # 卡牌系统
        self.cbubble_sys = BubbleSys(self)
        # 背景音乐
        pygame.mixer_music.load('sound//Accomplish.ogg')
        pygame.mixer_music.play(-1)
        # 字体
        self.font = pygame.font.Font(r'font\ark-pixel-12px.otf', 30)
        # 分数
        self.score_sys = ScoreSys(self.font)
        # 时间
        self.time_sys = TimeSys(self)
        # 正在运行的
        self.active: Active = 'none'
        # 菜单
        self.menu = Menu(self)

    
    def control(self):
        event: pygame.event.Event
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.quit = True
                continue
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1 and self.active == 'game':
                    self.cbubble_sys.handle_click(pygame.Vector2(event.pos))
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if self.active == 'game':
                    self.shitf('pause')
                else:
                    self.shitf('game')


    def update(self):
        self.time_sys.update(self.active)
        self.cbubble_sys.update(self.active)
        return super().update()
    

    def draw(self):
        # 游戏和菜单
        if self.active == 'game':
            self.surface.fill(self.bg_color, (0, GAME_TOP, WIDTH, GAME_HEIGHT))
            self.cbubble_sys.draw(self.surface)
        else:
            self.surface.fill(self.bg_color, (0, 0, WIDTH, BORDER_HEIGT + GAME_HEIGHT))
            self.menu.draw(self.surface, self.active, self.score_sys.new_high_score)
        # 时间
        self.time_sys.draw(self.surface, self.active)
        # 分数
        self.score_sys.draw(self.surface)
        return super().draw()
    

    def safe_quit(self):
        # 保存最高分
        self.score_sys.save_max_score()
        return super().safe_quit()
    

    def shitf(self, active: Active):
        """切换运行状态"""
        if active == "game":
            if self.active == 'none':
                self.bg_color = random.choice(self.bg_colors)
                self.time_sys.re_start()
                self.cbubble_sys.re_start()
                self.score_sys.re_start()
        self.active = active


    def handle_dead_bubble(self, kind: int):
        if kind == 0:  # 常
            self.score_sys.add(2)
        elif kind == 1:  # 毒
            self.time_sys.add_time(-1000)
            self.score_sys.add(-3)
        elif kind == 2:  # 红
            self.time_sys.add_time(1500)
            self.score_sys.add(1)
        elif kind == 3:  # 彩
            self.score_sys.add(10)


if __name__ == '__main__':
    game = Game()
    game.run()
