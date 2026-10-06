import json
import math
import pygame
import time
from pathlib import Path
from game.maze import generate_maze, find_shortest_path, CELL
from game.player import Player

FPS = 60
BG = (240, 235, 220)
WALL_COLOR = (40, 40, 60)
EXIT_COLOR = (80, 200, 80)
DIFFICULTIES = {
    "Easy": (10, 8),
    "Medium": (15, 13),
    "Hard": (20, 18),
}
MENU_WIDTH = max(cols for cols, _ in DIFFICULTIES.values()) * CELL
MENU_HEIGHT = max(rows for _, rows in DIFFICULTIES.values()) * CELL + 60
FOG_RADIUS = 3 * CELL
LEADERBOARD_PATH = Path(__file__).resolve().parents[1] / "leaderboard.json"

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((MENU_WIDTH, MENU_HEIGHT))
        pygame.display.set_caption("Maze Runner")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 22)
        self.big_font = pygame.font.SysFont("monospace", 36, bold=True)
        self.small_font = pygame.font.SysFont("monospace", 18)
        self.leaderboard_path = LEADERBOARD_PATH
        self.leaderboard = self._load_leaderboard()
        self.difficulty = None
        button_width, button_height, gap = 180, 56, 24
        buttons_width = len(DIFFICULTIES) * button_width + (len(DIFFICULTIES) - 1) * gap
        button_x = (MENU_WIDTH - buttons_width) // 2
        button_y = MENU_HEIGHT // 2
        self.difficulty_buttons = {
            name: pygame.Rect(
                button_x + index * (button_width + gap),
                button_y,
                button_width,
                button_height,
            )
            for index, name in enumerate(DIFFICULTIES)
        }

    def _load_leaderboard(self):
        try:
            with self.leaderboard_path.open(encoding="utf-8") as file:
                entries = json.load(file)
        except FileNotFoundError:
            return []
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Leaderboard file is not valid JSON: {self.leaderboard_path}"
            ) from error

        if not isinstance(entries, list):
            raise ValueError("Leaderboard data must be a JSON list")
        for index, entry in enumerate(entries):
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("time"), (int, float))
                or isinstance(entry["time"], bool)
                or not math.isfinite(entry["time"])
                or entry["time"] < 0
            ):
                raise ValueError(f"Invalid leaderboard entry at index {index}")
        return sorted(entries, key=lambda entry: entry["time"])[:5]

    def _record_completion(self):
        self.leaderboard.append(
            {"time": round(self.elapsed, 2), "difficulty": self.difficulty}
        )
        self.leaderboard.sort(key=lambda entry: entry["time"])
        self.leaderboard = self.leaderboard[:5]
        with self.leaderboard_path.open("w", encoding="utf-8") as file:
            json.dump(self.leaderboard, file, indent=2)
            file.write("\n")

    def start_difficulty(self, difficulty):
        if difficulty not in DIFFICULTIES:
            raise ValueError(f"Unknown maze difficulty: {difficulty}")
        self.difficulty = difficulty
        self.cols, self.rows = DIFFICULTIES[difficulty]
        self.width = self.cols * CELL
        self.maze_height = self.rows * CELL
        self.screen = pygame.display.set_mode((self.width, self.maze_height + 60))
        self.reset()

    def reset(self):
        self.walls = generate_maze(self.cols, self.rows)
        self.player = Player(0, 0)
        self.exit_rect = pygame.Rect(
            (self.cols - 1) * CELL + 5,
            (self.rows - 1) * CELL + 5,
            CELL - 10,
            CELL - 10,
        )
        self.start_time = time.time()
        self.elapsed = 0
        self.won = False
        self.show_path = False
        self.solution_path = []

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if self.difficulty is None:
                if event.type == pygame.KEYDOWN:
                    key_difficulties = {
                        pygame.K_1: "Easy",
                        pygame.K_2: "Medium",
                        pygame.K_3: "Hard",
                    }
                    difficulty = key_difficulties.get(event.key)
                    if difficulty is not None:
                        self.start_difficulty(difficulty)
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    for name, button in self.difficulty_buttons.items():
                        if button.collidepoint(event.pos):
                            self.start_difficulty(name)
                continue
            if event.type == pygame.KEYDOWN and event.key == pygame.K_r:
                self.reset()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
                self.show_path = not self.show_path
                self.solution_path = (
                    find_shortest_path(self.walls) if self.show_path else []
                )
        return True

    def update(self):
        if self.difficulty is None:
            return
        if self.won:
            return
        keys = pygame.key.get_pressed()
        self.player.move(keys, self.walls, self.rows, self.cols)
        self.elapsed = time.time() - self.start_time
        if self.player.rect.colliderect(self.exit_rect) and not self.won:
            self.won = True
            self._record_completion()

    def draw_maze(self):
        wall_w = 3
        for r in range(self.rows):
            for c in range(self.cols):
                x, y = c*CELL, r*CELL
                w = self.walls[r][c]
                if w[0]: pygame.draw.line(self.screen, WALL_COLOR, (x,y), (x+CELL,y), wall_w)
                if w[1]: pygame.draw.line(self.screen, WALL_COLOR, (x,y+CELL), (x+CELL,y+CELL), wall_w)
                if w[2]: pygame.draw.line(self.screen, WALL_COLOR, (x+CELL,y), (x+CELL,y+CELL), wall_w)
                if w[3]: pygame.draw.line(self.screen, WALL_COLOR, (x,y), (x,y+CELL), wall_w)

    def draw_fog(self):
        fog = pygame.Surface((self.width, self.maze_height), pygame.SRCALPHA)
        fog.fill((0, 0, 0, 225))
        pygame.draw.circle(fog, (0, 0, 0, 0), self.player.rect.center, FOG_RADIUS)
        self.screen.blit(fog, (0, 0))

    def draw_difficulty_select(self):
        self.screen.fill(BG)
        title = self.big_font.render("Maze Runner", True, WALL_COLOR)
        subtitle = self.font.render("Choose a difficulty", True, WALL_COLOR)
        self.screen.blit(
            title, (MENU_WIDTH // 2 - title.get_width() // 2, MENU_HEIGHT // 2 - 130)
        )
        self.screen.blit(
            subtitle,
            (MENU_WIDTH // 2 - subtitle.get_width() // 2, MENU_HEIGHT // 2 - 75),
        )
        for index, (name, button) in enumerate(self.difficulty_buttons.items(), start=1):
            pygame.draw.rect(self.screen, WALL_COLOR, button, border_radius=8)
            label = self.font.render(
                f"{index}. {name}", True, (255, 255, 255)
            )
            self.screen.blit(
                label,
                (
                    button.centerx - label.get_width() // 2,
                    button.centery - label.get_height() // 2,
                ),
            )
            cols, rows = DIFFICULTIES[name]
            size = self.small_font.render(f"{cols} x {rows}", True, WALL_COLOR)
            self.screen.blit(size, (button.centerx - size.get_width() // 2, button.bottom + 12))
        pygame.display.flip()

    def draw(self):
        if self.difficulty is None:
            self.draw_difficulty_select()
            return

        self.screen.fill(BG)
        if self.show_path:
            path_color = (250, 210, 90)
            for row, col in self.solution_path:
                path_rect = pygame.Rect(
                    col * CELL + 8, row * CELL + 8, CELL - 16, CELL - 16
                )
                pygame.draw.rect(self.screen, path_color, path_rect, border_radius=4)
        self.draw_maze()
        pygame.draw.rect(self.screen, EXIT_COLOR, self.exit_rect, border_radius=4)
        ex_label = self.font.render("EXIT", True, (20,80,20))
        self.screen.blit(ex_label, (self.exit_rect.x+2, self.exit_rect.y+4))
        self.player.draw(self.screen)
        self.draw_fog()

        hud = pygame.Rect(0, self.maze_height, self.width, 60)
        pygame.draw.rect(self.screen, (30,30,50), hud)
        time_surf = self.font.render(f"Time: {self.elapsed:.1f}s   R = New Maze", True, (200,200,200))
        self.screen.blit(time_surf, (10, self.maze_height + 18))

        if self.won:
            overlay = pygame.Surface((self.width, self.maze_height), pygame.SRCALPHA)
            overlay.fill((0,0,0,120))
            self.screen.blit(overlay, (0,0))
            win_font = pygame.font.SysFont(
                "monospace", min(36, self.width // 14), bold=True
            )
            msg = win_font.render(
                f"Solved in {self.elapsed:.1f}s!", True, (80,240,80)
            )
            sub = self.font.render("Press R for a new maze", True, (200,200,200))
            heading = self.small_font.render("TOP 5 TIMES", True, (255, 220, 100))
            content_height = (
                msg.get_height()
                + 8
                + sub.get_height()
                + 12
                + heading.get_height()
                + 22 * len(self.leaderboard)
            )
            content_y = (self.maze_height - content_height) // 2
            self.screen.blit(
                msg, (self.width // 2 - msg.get_width() // 2, content_y)
            )
            sub_y = content_y + msg.get_height() + 8
            self.screen.blit(sub, (self.width // 2 - sub.get_width() // 2, sub_y))
            leaderboard_y = sub_y + sub.get_height() + 12
            self.screen.blit(
                heading,
                (self.width // 2 - heading.get_width() // 2, leaderboard_y),
            )
            for rank, entry in enumerate(self.leaderboard, start=1):
                row = self.small_font.render(
                    f"{rank}. {entry['time']:.2f}s {entry.get('difficulty', '')}",
                    True,
                    (230, 230, 230),
                )
                self.screen.blit(
                    row,
                    (self.width//2 - row.get_width()//2, leaderboard_y + 22 * rank),
                )
        pygame.display.flip()

    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()
