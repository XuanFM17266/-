import pygame
import sys
import random
import time

# 初始化pygame
pygame.init()

# 游戏常量
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GRID_SIZE = 8
CELL_SIZE = 60
MARGIN = 50
ANIMATION_SPEED = 10
COLORS = [
    (255, 0, 0),    # 红色
    (0, 255, 0),    # 绿色
    (0, 0, 255),    # 蓝色
    (255, 255, 0),  # 黄色
    (255, 0, 255),  # 紫色
    (0, 255, 255),  # 青色
]
GAME_TIME = 60  # 游戏时间（秒）
TARGET_SCORE = 1000  # 通关目标分数

# 创建游戏窗口
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("开心消消乐")

# 加载字体 - 使用支持中文的字体
try:
    # 尝试加载系统中常见的中文字体
    font = pygame.font.SysFont(["SimHei", "WenQuanYi Micro Hei", "Heiti TC"], 36)
    big_font = pygame.font.SysFont(["SimHei", "WenQuanYi Micro Hei", "Heiti TC"], 72)
    small_font = pygame.font.SysFont(["SimHei", "WenQuanYi Micro Hei", "Heiti TC"], 24)
except:
    # 如果找不到中文字体，使用默认字体
    print("警告: 无法加载中文字体，将使用默认字体")
    font = pygame.font.SysFont(None, 36)
    big_font = pygame.font.SysFont(None, 72)
    small_font = pygame.font.SysFont(None, 24)

class Game:
    def __init__(self):
        self.grid = []
        self.selected = None
        self.score = 0
        self.animations = []
        self.game_over = False
        self.victory = False
        self.initialize_grid()
        self.reset_game()
        
    def reset_game(self):
        # 重置游戏状态
        self.score = 0
        self.game_over = False
        self.victory = False
        self.start_time = time.time()
        self.end_time = self.start_time + GAME_TIME  # 设置结束时间
        
    def initialize_grid(self):
        # 创建初始网格
        self.grid = []
        for _ in range(GRID_SIZE):
            row = []
            for _ in range(GRID_SIZE):
                row.append(random.choice(range(len(COLORS))))
            self.grid.append(row)
        
        # 确保初始网格没有可消除的组合
        while self.find_matches():
            self.remove_matches()
            self.fill_empty_cells()
    
    def draw(self):
        # 绘制背景
        screen.fill((30, 30, 50))
        
        # 绘制标题
        title = big_font.render("开心消消乐", True, (255, 215, 0))
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 10))
        
        # 绘制分数
        score_text = font.render(f"分数: {self.score}", True, (255, 255, 255))
        screen.blit(score_text, (20, 20))
        
        # 绘制游戏倒计时
        remaining_time = max(0, int(self.end_time - time.time()))
        minutes = remaining_time // 60
        seconds = remaining_time % 60
        time_text = font.render(f"剩余时间: {minutes:02d}:{seconds:02d}", True, (255, 255, 255))
        screen.blit(time_text, (20, 60))
        
        # 绘制目标分数
        target_text = font.render(f"目标: {TARGET_SCORE}分", True, (255, 255, 255))
        screen.blit(target_text, (20, 100))
        
        # 绘制网格背景
        grid_rect = pygame.Rect(
            MARGIN - 10, 
            MARGIN + 40, 
            GRID_SIZE * CELL_SIZE + 20, 
            GRID_SIZE * CELL_SIZE + 20
        )
        pygame.draw.rect(screen, (50, 50, 70), grid_rect)
        pygame.draw.rect(screen, (100, 100, 150), grid_rect, 3)
        
        # 绘制网格中的方块
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = MARGIN + col * CELL_SIZE
                y = MARGIN + 40 + row * CELL_SIZE
                
                # 检查是否有动画
                animating = False
                for anim in self.animations:
                    if anim[0] == row and anim[1] == col:
                        x += anim[4][0]
                        y += anim[4][1]
                        animating = True
                        break
                
                # 绘制方块
                color_idx = self.grid[row][col]
                if color_idx >= 0:  # 确保是有效颜色
                    color = COLORS[color_idx]
                    pygame.draw.rect(screen, color, (x, y, CELL_SIZE - 4, CELL_SIZE - 4), 0, 10)
                    pygame.draw.rect(screen, (200, 200, 200), (x, y, CELL_SIZE - 4, CELL_SIZE - 4), 2, 10)
                
                # 如果被选中，绘制边框
                if self.selected and self.selected[0] == row and self.selected[1] == col:
                    pygame.draw.rect(screen, (255, 255, 255), (x-4, y-4, CELL_SIZE+4, CELL_SIZE+4), 3, 12)
        
        # 绘制操作说明
        instructions = [
            "游戏说明:",
            "1. 点击一个方块选中它",
            "2. 点击相邻方块进行交换",
            "3. 三个或更多相同方块连在一起即可消除",
            "4. 消除后上方的方块会下落",
            "5. 按 R 键重新开始游戏"
        ]
        
        for i, text in enumerate(instructions):
            instr = font.render(text, True, (200, 200, 200))
            screen.blit(instr, (SCREEN_WIDTH - 350, 100 + i * 40))
        
        # 检查游戏是否结束
        if self.game_over or self.victory:
            # 绘制半透明背景
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))
            
            # 绘制游戏结束消息
            if self.victory:
                message = big_font.render("恭喜通关!", True, (255, 215, 0))
            else:
                message = big_font.render("游戏结束!", True, (255, 0, 0))
            screen.blit(message, (SCREEN_WIDTH // 2 - message.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
            
            # 绘制最终分数
            score_message = font.render(f"最终分数: {self.score}", True, (255, 255, 255))
            screen.blit(score_message, (SCREEN_WIDTH // 2 - score_message.get_width() // 2, SCREEN_HEIGHT // 2))
            
            # 绘制重新开始提示
            restart_message = small_font.render("按 R 键重新开始游戏", True, (200, 200, 200))
            screen.blit(restart_message, (SCREEN_WIDTH // 2 - restart_message.get_width() // 2, SCREEN_HEIGHT // 2 + 60))
    
    def handle_click(self, pos):
        # 如果游戏已结束，不处理点击事件
        if self.game_over or self.victory:
            return
            
        # 将屏幕坐标转换为网格坐标
        x, y = pos
        col = (x - MARGIN) // CELL_SIZE
        row = (y - MARGIN - 40) // CELL_SIZE
        
        # 检查是否在网格范围内
        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
            if self.selected is None:
                # 第一次选择
                self.selected = (row, col)
            else:
                # 第二次选择 - 尝试交换
                row1, col1 = self.selected
                
                # 检查是否相邻
                if (abs(row - row1) == 1 and col == col1) or (abs(col - col1) == 1 and row == row1):
                    # 交换方块
                    self.swap((row1, col1), (row, col))
                    
                    # 检查是否有匹配
                    if not self.find_matches():
                        # 如果没有匹配，交换回来
                        self.swap((row, col), (row1, col1))
                
                # 重置选择
                self.selected = None
    
    def swap(self, pos1, pos2):
        # 交换两个位置的方块
        row1, col1 = pos1
        row2, col2 = pos2
        self.grid[row1][col1], self.grid[row2][col2] = self.grid[row2][col2], self.grid[row1][col1]
        
        # 添加交换动画
        self.animations.append((
            row1, col1, 
            row2, col2,
            ((col2 - col1) * CELL_SIZE // 2, (row2 - row1) * CELL_SIZE // 2),
            "swap"
        ))
    
    def find_matches(self):
        # 查找所有匹配项（水平或垂直三个或更多相同方块）
        matches = []
        
        # 检查水平匹配
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE - 2):
                if (self.grid[row][col] == self.grid[row][col+1] == self.grid[row][col+2] >= 0):
                    # 查找匹配的长度
                    match_length = 3
                    while col + match_length < GRID_SIZE and self.grid[row][col] == self.grid[row][col+match_length]:
                        match_length += 1
                    
                    # 添加到匹配列表
                    for i in range(match_length):
                        matches.append((row, col+i))
        
        # 检查垂直匹配
        for col in range(GRID_SIZE):
            for row in range(GRID_SIZE - 2):
                if (self.grid[row][col] == self.grid[row+1][col] == self.grid[row+2][col] >= 0):
                    # 查找匹配的长度
                    match_length = 3
                    while row + match_length < GRID_SIZE and self.grid[row][col] == self.grid[row+match_length][col]:
                        match_length += 1
                    
                    # 添加到匹配列表
                    for i in range(match_length):
                        matches.append((row+i, col))
        
        # 去重
        return list(set(matches))
    
    def remove_matches(self):
        # 移除所有匹配的方块并更新分数
        matches = self.find_matches()
        
        if matches:
            # 添加消除动画
            for row, col in matches:
                self.animations.append((row, col, -1, -1, (0, 0), "remove"))
            
            # 更新分数
            self.score += len(matches) * 10
            
            # 检查是否达到通关条件
            if self.score >= TARGET_SCORE:
                self.victory = True
            
            # 移除方块（设置为-1表示空）
            for row, col in matches:
                self.grid[row][col] = -1
            
            return True
        return False
    
    def fill_empty_cells(self):
        # 让上方的方块下落填补空格
        for col in range(GRID_SIZE):
            # 从底部向上移动方块
            empty_row = GRID_SIZE - 1
            for row in range(GRID_SIZE - 1, -1, -1):
                if self.grid[row][col] >= 0:
                    if empty_row != row:
                        # 移动方块
                        self.grid[empty_row][col] = self.grid[row][col]
                        self.grid[row][col] = -1
                        
                        # 添加下落动画
                        self.animations.append((
                            row, col,
                            empty_row, col,
                            (0, (empty_row - row) * CELL_SIZE),
                            "fall"
                        ))
                    empty_row -= 1
        
        # 在顶部生成新方块
        for col in range(GRID_SIZE):
            for row in range(GRID_SIZE):
                if self.grid[row][col] == -1:
                    self.grid[row][col] = random.choice(range(len(COLORS)))
                    
                    # 添加新方块动画
                    self.animations.append((
                        row, col,
                        row, col,
                        (0, -CELL_SIZE),
                        "new"
                    ))
    
    def update_animations(self):
        # 如果游戏已结束，不更新动画
        if self.game_over or self.victory:
            return
            
        # 更新所有动画
        completed_animations = []
        
        for i, anim in enumerate(self.animations):
            row, col, target_row, target_col, (dx, dy), anim_type = anim
            
            # 根据动画类型更新位置
            if anim_type == "swap":
                if abs(dx) > 0 or abs(dy) > 0:
                    # 更新位置
                    sign_x = -1 if dx > 0 else 1
                    sign_y = -1 if dy > 0 else 1
                    new_dx = dx - sign_x * ANIMATION_SPEED
                    new_dy = dy - sign_y * ANIMATION_SPEED
                    
                    # 确保不会过冲
                    if (sign_x == 1 and new_dx < 0) or (sign_x == -1 and new_dx > 0):
                        new_dx = 0
                    if (sign_y == 1 and new_dy < 0) or (sign_y == -1 and new_dy > 0):
                        new_dy = 0
                    
                    self.animations[i] = (row, col, target_row, target_col, (new_dx, new_dy), anim_type)
                else:
                    completed_animations.append(i)
            
            elif anim_type == "remove":
                # 移除动画已完成
                completed_animations.append(i)
            
            elif anim_type == "fall" or anim_type == "new":
                if dy != 0:
                    # 更新位置
                    sign_y = 1 if dy > 0 else -1
                    new_dy = dy - sign_y * ANIMATION_SPEED
                    
                    # 确保不会过冲
                    if (sign_y == 1 and new_dy < 0) or (sign_y == -1 and new_dy > 0):
                        new_dy = 0
                    
                    self.animations[i] = (row, col, target_row, target_col, (dx, new_dy), anim_type)
                else:
                    completed_animations.append(i)
        
        # 移除已完成的动画
        for idx in sorted(completed_animations, reverse=True):
            self.animations.pop(idx)
        
        # 如果没有动画且存在匹配，继续消除
        if not self.animations and self.find_matches():
            self.remove_matches()
            self.fill_empty_cells()
        
        # 检查时间是否用完
        if time.time() >= self.end_time and not self.victory:
            self.game_over = True

# 创建游戏实例
game = Game()

# 游戏主循环
clock = pygame.time.Clock()
last_time = time.time()

while True:
    current_time = time.time()
    dt = current_time - last_time
    last_time = current_time
    
    # 处理事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键点击
                game.handle_click(event.pos)
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r:  # 按R键重置游戏
                game.initialize_grid()
                game.reset_game()
            elif event.key == pygame.K_ESCAPE:  # 按ESC键退出
                pygame.quit()
                sys.exit()
    
    # 更新游戏状态
    game.update_animations()
    
    # 绘制游戏
    game.draw()
    
    # 显示帧率
    fps = int(clock.get_fps())
    fps_text = font.render(f"FPS: {fps}", True, (200, 200, 200))
    screen.blit(fps_text, (SCREEN_WIDTH - 120, 20))
    
    # 更新屏幕
    pygame.display.flip()
    
    # 控制帧率
    clock.tick(60)
