import pygame
import sys
import random
import time

# 初始化pygame
pygame.init()
pygame.key.set_repeat(500, 100)  # 设置键盘重复响应

# 游戏常量
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 700  # 增加屏幕高度，避免重叠
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
    medium_font = pygame.font.SysFont(["SimHei", "WenQuanYi Micro Hei", "Heiti TC"], 48)
except:
    # 如果找不到中文字体，使用默认字体
    print("警告: 无法加载中文字体，将使用默认字体")
    font = pygame.font.SysFont(None, 36)
    big_font = pygame.font.SysFont(None, 72)
    small_font = pygame.font.SysFont(None, 24)
    medium_font = pygame.font.SysFont(None, 48)

class Game:
    def __init__(self):
        self.grid = []
        self.selected = None
        self.score = 0
        self.animations = []
        self.game_over = False
        self.victory = False
        self.show_instructions = False  # 控制是否显示游戏说明
        self.paused = False  # 控制游戏是否暂停
        self.pause_start_time = 0  # 暂停开始时间
        self.pause_duration = 0  # 累计暂停时间
        self.initialize_grid()
        self.reset_game()
        
    def reset_game(self):
        # 重置游戏状态
        self.score = 0
        self.game_over = False
        self.victory = False
        self.show_instructions = False
        self.paused = False
        self.pause_start_time = 0
        self.pause_duration = 0
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
        
        # 合并显示分数和目标分数
        score_text = font.render(f"得分/目标: {self.score}/{TARGET_SCORE}", True, (255, 255, 255))
        screen.blit(score_text, (20, 80))
        
        # 绘制游戏倒计时
        remaining_time = max(0, int(self.get_remaining_time()))
        minutes = remaining_time // 60
        seconds = remaining_time % 60
        time_text = font.render(f"剩余时间: {minutes:02d}:{seconds:02d}", True, (255, 255, 255))
        screen.blit(time_text, (20, 130))
        
        # 绘制操作提示
        hint_text = small_font.render("按 I 键查看说明 | 按 P 键暂停游戏", True, (200, 200, 200))
        screen.blit(hint_text, (SCREEN_WIDTH - hint_text.get_width() - 20, 80))
        
        # 绘制网格背景
        grid_rect = pygame.Rect(
            MARGIN - 10, 
            MARGIN + 120,  # 下移网格位置，避免重叠
            GRID_SIZE * CELL_SIZE + 20, 
            GRID_SIZE * CELL_SIZE + 20
        )
        pygame.draw.rect(screen, (50, 50, 70), grid_rect)
        pygame.draw.rect(screen, (100, 100, 150), grid_rect, 3)
        
        # 绘制网格中的方块
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = MARGIN + col * CELL_SIZE
                y = MARGIN + 120 + row * CELL_SIZE  # 下移方块位置
                
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
        
        # 绘制游戏说明弹窗
        if self.show_instructions:
            self.draw_instructions_window()
        
        # 绘制暂停窗口
        if self.paused and not self.show_instructions:
            self.draw_pause_window()
        
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
                message = big_font.render("游戏失败!", True, (255, 0, 0))
            screen.blit(message, (SCREEN_WIDTH // 2 - message.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
            
            # 绘制最终分数
            score_message = font.render(f"最终分数: {self.score}/{TARGET_SCORE}", True, (255, 255, 255))
            screen.blit(score_message, (SCREEN_WIDTH // 2 - score_message.get_width() // 2, SCREEN_HEIGHT // 2))
            
            # 绘制重新开始提示
            restart_message = small_font.render("按 R 键重新开始游戏", True, (200, 200, 200))
            screen.blit(restart_message, (SCREEN_WIDTH // 2 - restart_message.get_width() // 2, SCREEN_HEIGHT // 2 + 60))
    
    def get_remaining_time(self):
        # 计算剩余时间
        if self.paused or self.game_over or self.victory:
            # 如果游戏暂停、结束或通关，返回暂停/结束时的剩余时间
            return self.paused_remaining_time
        else:
            # 如果游戏进行中，返回实际剩余时间
            return max(0, self.end_time - time.time())
    
    def draw_instructions_window(self):
        # 绘制游戏说明弹窗
        window_width = 500
        window_height = 400
        window_x = (SCREEN_WIDTH - window_width) // 2
        window_y = (SCREEN_HEIGHT - window_height) // 2
        
        # 绘制窗口背景
        window = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
        window.fill((0, 0, 0, 220))
        screen.blit(window, (window_x, window_y))
        
        # 绘制窗口边框
        pygame.draw.rect(screen, (255, 215, 0), (window_x, window_y, window_width, window_height), 3)
        
        # 绘制标题
        title = medium_font.render("游戏说明", True, (255, 215, 0))
        screen.blit(title, (window_x + (window_width - title.get_width()) // 2, window_y + 20))
        
        # 绘制说明内容
        instructions = [
            "1. 点击一个方块选中它",
            "2. 点击相邻方块进行交换",
            "3. 三个或更多相同方块连在一起即可消除",
            "4. 消除后上方的方块会下落",
            "5. 游戏时间为60秒，目标分数为1000分",
            "6. 按 I 键显示/隐藏说明",
            "7. 按 P 键暂停/继续游戏",
            "8. 按 R 键重新开始游戏",
            "9. 按 ESC 键退出游戏",
        ]
        
        for i, text in enumerate(instructions):
            instr = font.render(text, True, (255, 255, 255))
            screen.blit(instr, (window_x + 40, window_y + 80 + i * 40))
        
        # 绘制当前状态提示
        status_text = small_font.render(f"游戏已暂停 - 得分: {self.score}/{TARGET_SCORE}", True, (255, 215, 0))
        screen.blit(status_text, (window_x + (window_width - status_text.get_width()) // 2, window_y + window_height - 80))
        
        # 绘制关闭提示
        close_text = small_font.render("按 I 键关闭并继续游戏", True, (200, 200, 200))
        screen.blit(close_text, (window_x + (window_width - close_text.get_width()) // 2, window_y + window_height - 40))
    
    def draw_pause_window(self):
        # 绘制暂停窗口
        window_width = 400
        window_height = 300
        window_x = (SCREEN_WIDTH - window_width) // 2
        window_y = (SCREEN_HEIGHT - window_height) // 2
        
        # 绘制窗口背景
        window = pygame.Surface((window_width, window_height), pygame.SRCALPHA)
        window.fill((0, 0, 0, 220))
        screen.blit(window, (window_x, window_y))
        
        # 绘制窗口边框
        pygame.draw.rect(screen, (255, 215, 0), (window_x, window_y, window_width, window_height), 3)
        
        # 绘制标题
        title = medium_font.render("游戏暂停", True, (255, 215, 0))
        screen.blit(title, (window_x + (window_width - title.get_width()) // 2, window_y + 40))
        
        # 绘制分数和时间
        score_text = font.render(f"得分/目标: {self.score}/{TARGET_SCORE}", True, (255, 255, 255))
        screen.blit(score_text, (window_x + (window_width - score_text.get_width()) // 2, window_y + 100))
        
        remaining_time = max(0, int(self.get_remaining_time()))
        minutes = remaining_time // 60
        seconds = remaining_time % 60
        time_text = font.render(f"剩余时间: {minutes:02d}:{seconds:02d}", True, (255, 255, 255))
        screen.blit(time_text, (window_x + (window_width - time_text.get_width()) // 2, window_y + 150))
        
        # 绘制操作提示
        resume_text = small_font.render("按 P 键继续游戏", True, (200, 200, 200))
        screen.blit(resume_text, (window_x + (window_width - resume_text.get_width()) // 2, window_y + 200))
        
        restart_text = small_font.render("按 R 键重新开始", True, (200, 200, 200))
        screen.blit(restart_text, (window_x + (window_width - restart_text.get_width()) // 2, window_y + 230))
    
    def handle_click(self, pos):
        # 如果游戏已结束或暂停，不处理点击事件
        if self.game_over or self.paused:
            return
            
        # 将屏幕坐标转换为网格坐标
        x, y = pos
        col = (x - MARGIN) // CELL_SIZE
        row = (y - MARGIN - 120) // CELL_SIZE  # 调整计算方式以适应下移的网格
        
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
                # 通关后停止倒计时
                self.paused = True
                self.paused_remaining_time = 0  # 通关后剩余时间为0
            
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
        # 如果游戏已结束或暂停，不更新动画
        if self.game_over or self.paused:
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
        if self.get_remaining_time() <= 0 and not self.victory:
            self.game_over = True
            self.paused = True  # 游戏结束时暂停
    
    def toggle_pause(self):
        # 切换暂停状态
        if self.paused:
            # 恢复游戏
            self.paused = False
            # 计算新的结束时间
            self.end_time = time.time() + self.paused_remaining_time
            print(f"游戏恢复，剩余时间: {self.paused_remaining_time:.2f}秒")
        else:
            # 暂停游戏
            self.paused = True
            # 记录当前剩余时间
            self.paused_remaining_time = max(0, self.end_time - time.time())
            print(f"游戏暂停，剩余时间: {self.paused_remaining_time:.2f}秒")

# 创建游戏实例
game = Game()

# 游戏主循环
clock = pygame.time.Clock()

print("游戏已启动，按 I 键查看说明，按 P 键暂停游戏")

while True:
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
                print("检测到 R 键按下，重置游戏")
                game.initialize_grid()
                game.reset_game()
            elif event.key == pygame.K_ESCAPE:  # 按ESC键退出
                pygame.quit()
                sys.exit()
            elif event.key == pygame.K_i:  # 按I键显示/隐藏游戏说明
                print("检测到 I 键按下，切换说明显示状态")
                game.show_instructions = not game.show_instructions
                if game.show_instructions:
                    # 显示说明时暂停游戏
                    if not game.paused:
                        game.toggle_pause()
                else:
                    # 关闭说明时，直接恢复游戏
                    if game.paused:
                        game.toggle_pause()
            elif event.key == pygame.K_p:  # 按P键暂停/继续游戏
                print("检测到 P 键按下，切换暂停状态")
                game.show_instructions = False  # 暂停时关闭说明窗口
                game.toggle_pause()
    
    # 更新游戏状态
    game.update_animations()
    
    # 绘制游戏
    game.draw()
    
    # 显示帧率
    fps = int(clock.get_fps())
    fps_text = font.render(f"FPS: {fps}", True, (200, 200, 200))
    screen.blit(fps_text, (SCREEN_WIDTH - 120, 180))
    
    # 更新屏幕
    pygame.display.flip()
    
    # 控制帧率
    clock.tick(60)
