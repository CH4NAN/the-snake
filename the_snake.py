from random import choice, randrange

import pygame


# Константы для размеров поля и сетки:
SCREEN_WIDTH, SCREEN_HEIGHT = 640, 480
GRID_SIZE = 20
GRID_WIDTH = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT = SCREEN_HEIGHT // GRID_SIZE

# Направления движения:
UP = (0, -1)
DOWN = (0, 1)
LEFT = (-1, 0)
RIGHT = (1, 0)
KEY_DIRECTIONS = {
    pygame.K_UP: UP,
    pygame.K_DOWN: DOWN,
    pygame.K_LEFT: LEFT,
    pygame.K_RIGHT: RIGHT,
}
OPPOSITE = {UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT}

# Параметры игрового поля:
BOARD_BACKGROUND_COLOR = (100, 190, 240)
SCORE_COLOR = (255, 100, 80)

# Цвет яблока
APPLE_COLOR = (240, 70, 70)
APPLE_BORDER_COLOR = (170, 30, 40)

# Параметры змейки
SNAKE_START_LENGTH = 3
SNAKE_COLOR = (80, 200, 100)
SNAKE_BORDER_COLOR = (30, 120, 50)
SNAKE_END_RADIUS = 6
SNAKE_BODY_RADIUS = 4

# Параметры огрызка:
STUB_COLOR = (160, 90, 40)
STUB_BORDER_COLOR = (100, 55, 20)
STUB_STEP = 7

# Параметры стен:
WALL_COLOR = (250, 220, 170)
WALL_BORDER_COLOR = (215, 165, 90)
WALL_COUNT = 12
WALL_MIN_LENGTH = 3
WALL_MAX_LENGTH = 6
# Скорость движения змейки:
SPEED = 10

# Переменные для подсчета очков:
score = 0
high_score = 0


# Настройка игрового окна:
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)

# Заголовок окна игрового поля:
pygame.display.set_caption('Змейка')

# Настройка времени:
clock = pygame.time.Clock()


# Тут опишите все классы игры.
class GameObject:
    """Базовый класс для всех игровых объектов."""

    def __init__(self, position=None, body_color=None):
        self.position = position or (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.body_color = body_color

    def draw(self):
        """Метод для отрисовки объекта на игровом поле."""
        raise NotImplementedError(  # Заменил pass на RaiseImplementedError
            "Метод draw() должен "  # По подсказке ИИ
            "быть реализован в подклассе."
        )


class Apple(GameObject):
    """Класс яблока. Содержит методы для управления яблоком и отрисовки."""

    def __init__(self, apple_color=APPLE_COLOR,
                 border_color=APPLE_BORDER_COLOR, occupied=()):
        super().__init__(position=None, body_color=apple_color)
        position = Apple.randomize_position(occupied)
        self.position = position
        self.border_color = border_color

    @staticmethod
    def randomize_position(occupied=()):
        """Возвращает случайную позицию, не занятую другими объектами."""
        occupied = set(occupied)
        free = [(x * GRID_SIZE, y * GRID_SIZE)
                for x in range(GRID_WIDTH) for y in range(GRID_HEIGHT)
                if (x * GRID_SIZE, y * GRID_SIZE) not in occupied]
        return choice(free)

    def draw(self):
        """Метод для отрисовки яблока на игровом поле."""
        circle = pygame.Rect(self.position, (GRID_SIZE, GRID_SIZE))
        pygame.draw.circle(screen, self.body_color,
                           circle.center, GRID_SIZE // 2)
        pygame.draw.circle(screen, self.border_color,
                           circle.center, GRID_SIZE // 2, 2)


class Stub(Apple):
    """Класс огрызка. Наследуется от класса Apple."""

    def __init__(self, stub_color=STUB_COLOR,
                 stub_border_color=STUB_BORDER_COLOR, occupied=()):
        super().__init__(apple_color=stub_color,
                         border_color=stub_border_color, occupied=occupied)


class Walls(GameObject):  # Этот класс я генерировал с ИИ
    """Стены: класс для управления стенами и их отрисовки."""

    def __init__(self, color=WALL_COLOR):
        super().__init__(body_color=color)
        self.positions = []

    def generate(self, forbidden):
        """Расставляет стены, не задевая запрещённые клетки."""
        self.positions = []
        walls_made = 0
        while walls_made < WALL_COUNT:
            # Случайная начальная клетка (в клетках сетки, не в пикселях)
            x = randrange(GRID_WIDTH)
            y = randrange(GRID_HEIGHT)
            # Случайно выбираем: стена горизонтальная или вертикальная
            if randrange(2) == 0:
                dx, dy = 1, 0
            else:
                dx, dy = 0, 1

            # Собираем клетки одной стены
            length = randrange(WALL_MIN_LENGTH, WALL_MAX_LENGTH + 1)
            wall = []
            for i in range(length):
                cell = (((x + dx * i) % GRID_WIDTH) * GRID_SIZE,
                        ((y + dy * i) % GRID_HEIGHT) * GRID_SIZE)
                wall.append(cell)

            # Стена подходит, если ни одна её клетка не занята
            ok = True
            for cell in wall:
                if cell in forbidden or cell in self.positions:
                    ok = False
            if ok:
                self.positions += wall
                walls_made += 1

    def draw(self):
        """Отрисовывает стены."""
        for position in self.positions:
            rect = pygame.Rect(position, (GRID_SIZE, GRID_SIZE))
            pygame.draw.rect(screen, self.body_color, rect)
            pygame.draw.rect(screen, WALL_BORDER_COLOR, rect, 1)


class Snake(GameObject):
    """Класс змейки. Содержит методы для управления змейкой и отрисовки."""

    def __init__(self, snake_color=SNAKE_COLOR):
        super().__init__(position=None, body_color=snake_color)
        self.reset()

    def get_head_position(self):
        """Метод для получения позиции головы змейки."""
        return self.positions[0]

    def move(self):
        """Двигает змейку. Возвращает False, если она врезалась в себя."""
        cur = self.get_head_position()
        x, y = self.direction
        new = (((cur[0] + (x * GRID_SIZE)) % SCREEN_WIDTH),
               (cur[1] + (y * GRID_SIZE)) % SCREEN_HEIGHT)

        if new in self.positions[:-1]:
            return False

        self.positions.insert(0, new)
        while len(self.positions) > self.length:
            self.positions.pop()
        return True

    def draw(self):
        """Метод для отрисовки змейки на игровом поле."""
        last_index = len(self.positions) - 1
        for i, position in enumerate(self.positions):
            rect = pygame.Rect(position, (GRID_SIZE, GRID_SIZE))
            if last_index >= 1 and (i == 0 or i == last_index):
                radius = SNAKE_END_RADIUS
            else:
                radius = SNAKE_BODY_RADIUS
            pygame.draw.rect(screen, self.body_color, rect,
                             border_radius=radius)
            pygame.draw.rect(screen, SNAKE_BORDER_COLOR, rect, 1,
                             border_radius=radius)

    def update_direction(self):
        """Берёт следующее направление из очереди, если оно есть."""
        if self.direction_queue:
            self.direction = self.direction_queue.pop(0)

    def reset(self):
        """Метод для сброса змейки в начальное состояние."""
        head = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.positions = [(head[0] - i * GRID_SIZE, head[1])
                          for i in range(SNAKE_START_LENGTH)]
        self.direction = RIGHT
        self.direction_queue = []
        self.length = SNAKE_START_LENGTH


def handle_keys(game_object):
    """Функция обработки действий пользователя."""
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            raise SystemExit
        if event.type != pygame.KEYDOWN or event.key not in KEY_DIRECTIONS:
            continue
        new = KEY_DIRECTIONS[event.key]
        last = (game_object.direction_queue[-1]
                if game_object.direction_queue else game_object.direction)
        if new not in (last, OPPOSITE[last]) and len(
                game_object.direction_queue) < 2:
            game_object.direction_queue.append(new)


def occupied_cells(walls, snake, apple, stubs):
    """Возвращает все занятые клетки поля."""
    return (walls.positions + snake.positions + [apple.position]
            + [stub.position for stub in stubs])


def reset_game(snake, apple, stubs, walls):
    """Сбрасывает змейку и заново расставляет яблоко и огрызки."""
    global score
    snake.reset()
    respawn(apple, walls, snake, apple, stubs)
    for stub in stubs:
        respawn(stub, walls, snake, apple, stubs)
    score = 0


def respawn(obj, walls, snake, apple, stubs):
    """Обновляет позицию объекта, избегая занятых ячеек."""
    obj.position = obj.randomize_position(occupied_cells
                                          (walls, snake, apple, stubs))


def draw_score(score, high_score):
    """Отображает количество очков и рекорд."""
    font = pygame.font.SysFont(
        'trebuchetms', 32, bold=True
    )

    score_text = font.render(
        f'Scores: {score}',
        True,
        SCORE_COLOR
    )

    high_score_text = font.render(
        f'Record: {high_score}',
        True,
        SCORE_COLOR
    )

    screen.blit(
        score_text,
        (SCREEN_WIDTH - (score_text.get_width() + 10), 10)
    )

    screen.blit(
        high_score_text,
        (SCREEN_WIDTH - (high_score_text.get_width() + 10), 50)
    )


def eat_apple(snake, apple, walls, stubs):
    """Обрабатывает съедание яблока."""
    global score, high_score

    snake.length += 1

    current_score = snake.length - SNAKE_START_LENGTH

    if current_score > score:
        score = current_score

    if score > high_score:
        high_score = score

    respawn(apple, walls, snake, apple, stubs)


def main():
    """Инициализация PyGame:"""
    pygame.init()
    # Тут нужно создать экземпляры классов.
    snake = Snake()
    walls = Walls()
    start = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    start_zone = [(start[0] + i * GRID_SIZE, start[1]) for i in range(-4, 6)]
    walls.generate(start_zone)
    apple = Apple(occupied=walls.positions + snake.positions)
    stubs = [Stub(occupied=occupied_cells(walls, snake, apple, []))]
    global score, high_score
    score = 0
    high_score = 0

    while True:
        clock.tick(SPEED)

        if snake.get_head_position() == apple.position:
            eat_apple(snake, apple, walls, stubs)

        for stub in stubs:
            if snake.get_head_position() == stub.position:
                snake.length -= 1
                if snake.length < SNAKE_START_LENGTH:
                    reset_game(snake, apple, stubs, walls)
                else:
                    respawn(stub, walls, snake, apple, stubs)
                break

        target = 1 + (snake.length - SNAKE_START_LENGTH) // STUB_STEP
        del stubs[max(target, 1):]
        while len(stubs) < target:
            stubs.append(Stub(
                occupied=occupied_cells(walls, snake, apple, stubs)))

        handle_keys(snake)
        snake.update_direction()
        alive = snake.move()

        if not alive or snake.get_head_position() in walls.positions:
            reset_game(snake, apple, stubs, walls)

        screen.fill(BOARD_BACKGROUND_COLOR)
        walls.draw()
        snake.draw()
        apple.draw()
        for stub in stubs:
            stub.draw()

        draw_score(score, high_score)
        pygame.display.update()


if __name__ == '__main__':
    main()


# Метод draw класса Apple
# def draw(self):
#     rect = pygame.Rect(self.position, (GRID_SIZE, GRID_SIZE))
#     pygame.draw.rect(screen, self.body_color, rect)
#     pygame.draw.rect(screen, BORDER_COLOR, rect, 1)

# # Метод draw класса Snake
# def draw(self):
#     for position in self.positions[:-1]:
#         rect = (pygame.Rect(position, (GRID_SIZE, GRID_SIZE)))
#         pygame.draw.rect(screen, self.body_color, rect)
#         pygame.draw.rect(screen, BORDER_COLOR, rect, 1)

#     # Отрисовка головы змейки
#     head_rect = pygame.Rect(self.positions[0], (GRID_SIZE, GRID_SIZE))
#     pygame.draw.rect(screen, self.body_color, head_rect)
#     pygame.draw.rect(screen, BORDER_COLOR, head_rect, 1)

#     # Затирание последнего сегмента
#     if self.last:
#         last_rect = pygame.Rect(self.last, (GRID_SIZE, GRID_SIZE))
#         pygame.draw.rect(screen, BOARD_BACKGROUND_COLOR, last_rect)

# Функция обработки действий пользователя
# def handle_keys(game_object):
#     for event in pygame.event.get():
#         if event.type == pygame.QUIT:
#             pygame.quit()
#             raise SystemExit
#         elif event.type == pygame.KEYDOWN:
#             if event.key == pygame.K_UP and
#  game_object.direction != DOWN:
#                 game_object.next_direction = UP
#             elif event.key == pygame.K_DOWN and
# game_object.direction != UP:
#                 game_object.next_direction = DOWN
#             elif event.key == pygame.K_LEFT and
# game_object.direction != RIGHT:
#                 game_object.next_direction = LEFT
#             elif event.key == pygame.K_RIGHT and
# game_object.direction != LEFT:
#                 game_object.next_direction = RIGHT

# Метод обновления направления после нажатия на кнопку
# def update_direction(self):
#     if self.next_direction:
#         self.direction = self.next_direction
#         self.next_direction = None
