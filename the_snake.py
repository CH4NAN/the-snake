from random import randint, randrange
from typing import Iterable, Optional

import pygame as pg

# Алиасы аннотаций:
Pointer = tuple[int, int]
Color = tuple[int, int, int]

# Константы для размеров поля и сетки:
SCREEN_WIDTH: int = 640
SCREEN_HEIGHT: int = 480
GRID_SIZE: int = 20
GRID_WIDTH: int = SCREEN_WIDTH // GRID_SIZE
GRID_HEIGHT: int = SCREEN_HEIGHT // GRID_SIZE

# Направления движения:
UP: Pointer = (0, -1)
DOWN: Pointer = (0, 1)
LEFT: Pointer = (-1, 0)
RIGHT: Pointer = (1, 0)
KEY_DIRECTIONS: dict[int, Pointer] = {
    pg.K_UP: UP,
    pg.K_DOWN: DOWN,
    pg.K_LEFT: LEFT,
    pg.K_RIGHT: RIGHT,
}
OPPOSITE: dict[Pointer, Pointer] = {
    UP: DOWN, DOWN: UP, LEFT: RIGHT, RIGHT: LEFT
}

# Параметры игрового поля:
BOARD_BACKGROUND_COLOR: Color = (100, 190, 240)
SCORE_COLOR: Color = (255, 100, 80)

# Цвет яблока
APPLE_COLOR: Color = (240, 70, 70)
APPLE_BORDER_COLOR: Color = (170, 30, 40)

# Параметры змейки
SNAKE_START_LENGTH: int = 3
SNAKE_COLOR: Color = (80, 200, 100)
SNAKE_BORDER_COLOR: Color = (30, 120, 50)
SNAKE_END_RADIUS: int = 6
SNAKE_BODY_RADIUS: int = 4

# Параметры огрызка:
STUB_COLOR: Color = (160, 90, 40)
STUB_BORDER_COLOR: Color = (100, 55, 20)
STUB_STEP: int = 5

# Параметры стен:
WALL_COLOR: Color = (250, 220, 170)
WALL_BORDER_COLOR: Color = (215, 165, 90)
WALL_COUNT: int = 12
WALL_MIN_LENGTH: int = 3
WALL_MAX_LENGTH: int = 6
# Скорость движения змейки:
SPEED: int = 10

# Переменные для подсчета очков:
score: int = 0
high_score: int = 0


# Настройка игрового окна:
screen: pg.Surface = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)

# Заголовок окна игрового поля:
pg.display.set_caption('Змейка')

# Настройка времени:
clock: pg.time.Clock = pg.time.Clock()


class GameObject:
    """Базовый класс для всех игровых объектов."""

    def __init__(self, position: Optional[Pointer] = None,
                 body_color: Optional[Color] = None) -> None:
        self.position: Pointer = position or (SCREEN_WIDTH // 2,
                                              SCREEN_HEIGHT // 2)
        self.body_color: Optional[Color] = body_color

    def draw(self) -> None:
        """Метод для отрисовки объекта на игровом поле."""
        raise NotImplementedError(
            'Метод draw() должен '
            'быть реализован в подклассе.'
        )


class Apple(GameObject):
    """Класс яблока. Содержит методы для управления яблоком и отрисовки."""

    def __init__(self, apple_color: Color = APPLE_COLOR,
                 border_color: Color = APPLE_BORDER_COLOR,
                 occupied_positions: Iterable[Pointer] = ()) -> None:
        super().__init__(position=None, body_color=apple_color)
        self.randomize_position(occupied_positions)
        self.border_color: Color = border_color

    def randomize_position(
            self, occupied_positions: Iterable[Pointer] = ()) -> None:
        """Устанавливает случайную позицию, не занятую другими объектами."""
        occupied: set[Pointer] = set(occupied_positions)
        while True:
            new_position: Pointer = (
                randint(0, GRID_WIDTH - 1) * GRID_SIZE,
                randint(0, GRID_HEIGHT - 1) * GRID_SIZE
            )
            if new_position not in occupied:
                self.position = new_position
                break

    def draw(self) -> None:
        """Метод для отрисовки яблока на игровом поле."""
        circle: pg.Rect = pg.Rect(self.position, (GRID_SIZE, GRID_SIZE))
        pg.draw.circle(screen, self.body_color,
                       circle.center, GRID_SIZE // 2)
        pg.draw.circle(screen, self.border_color,
                       circle.center, GRID_SIZE // 2, 2)


class Stub(Apple):
    """Класс огрызка. Наследуется от класса Apple."""

    def __init__(self, stub_color: Color = STUB_COLOR,
                 stub_border_color: Color = STUB_BORDER_COLOR,
                 occupied_positions: Iterable[Pointer] = ()) -> None:
        super().__init__(apple_color=stub_color,
                         border_color=stub_border_color,
                         occupied_positions=occupied_positions)


class Walls(GameObject):
    """Стены: класс для управления стенами и их отрисовки."""

    def __init__(self, color: Color = WALL_COLOR) -> None:
        super().__init__(body_color=color)
        self.positions: list[Pointer] = []

    def generate(self, forbidden: Iterable[Pointer]) -> None:
        """Расставляет стены, не задевая запрещённые клетки."""
        self.positions = []
        walls_made: int = 0
        while walls_made < WALL_COUNT:
            x: int = randrange(GRID_WIDTH)
            y: int = randrange(GRID_HEIGHT)
            if randrange(2) == 0:
                dx, dy = 1, 0
            else:
                dx, dy = 0, 1

            length: int = randrange(WALL_MIN_LENGTH, WALL_MAX_LENGTH + 1)
            wall: list[Pointer] = []
            for i in range(length):
                cell: Pointer = (((x + dx * i) % GRID_WIDTH) * GRID_SIZE,
                                 ((y + dy * i) % GRID_HEIGHT) * GRID_SIZE)
                wall.append(cell)

            ok: bool = True
            for cell in wall:
                if cell in forbidden or cell in self.positions:
                    ok = False
            if ok:
                self.positions += wall
                walls_made += 1

    def draw(self) -> None:
        """Отрисовывает стены."""
        for position in self.positions:
            rect: pg.Rect = pg.Rect(position, (GRID_SIZE, GRID_SIZE))
            pg.draw.rect(screen, self.body_color, rect)
            pg.draw.rect(screen, WALL_BORDER_COLOR, rect, 1)


class Snake(GameObject):
    """Класс змейки. Содержит методы для управления змейкой и отрисовки."""

    def __init__(self, snake_color: Color = SNAKE_COLOR) -> None:
        super().__init__(position=None, body_color=snake_color)
        self.reset()

    def get_head_position(self) -> Pointer:
        """Метод для получения позиции головы змейки."""
        return self.positions[0]

    def move(self) -> bool:
        """Двигает змейку. Возвращает False, если она врезалась в себя."""
        cur: Pointer = self.get_head_position()
        x, y = self.direction
        new: Pointer = (((cur[0] + (x * GRID_SIZE)) % SCREEN_WIDTH),
                        (cur[1] + (y * GRID_SIZE)) % SCREEN_HEIGHT)

        if new in self.positions[:-1]:
            return False

        self.positions.insert(0, new)
        while len(self.positions) > self.length:
            self.positions.pop()
        return True

    def draw(self) -> None:
        """Метод для отрисовки змейки на игровом поле."""
        last_index: int = len(self.positions) - 1
        for i, position in enumerate(self.positions):
            rect: pg.Rect = pg.Rect(position, (GRID_SIZE, GRID_SIZE))
            if last_index >= 1 and (i == 0 or i == last_index):
                radius: int = SNAKE_END_RADIUS
            else:
                radius = SNAKE_BODY_RADIUS
            pg.draw.rect(screen, self.body_color, rect,
                         border_radius=radius)
            pg.draw.rect(screen, SNAKE_BORDER_COLOR, rect, 1,
                         border_radius=radius)

    def update_direction(self) -> None:
        """Берёт следующее направление из очереди, если оно есть."""
        if self.direction_queue:
            self.direction = self.direction_queue.pop(0)

    def reset(self) -> None:
        """Метод для сброса змейки в начальное состояние."""
        head: Pointer = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        self.positions: list[Pointer] = [
            (head[0] - i * GRID_SIZE, head[1])
            for i in range(SNAKE_START_LENGTH)]
        self.direction: Pointer = RIGHT
        self.direction_queue: list[Pointer] = []
        self.length: int = SNAKE_START_LENGTH


def handle_keys(game_object: Snake) -> None:
    """Функция обработки действий пользователя."""
    for event in pg.event.get():
        if event.type == pg.QUIT:
            pg.quit()
            raise SystemExit
        if event.type != pg.KEYDOWN or event.key not in KEY_DIRECTIONS:
            continue
        new: Pointer = KEY_DIRECTIONS[event.key]
        last: Pointer = (game_object.direction_queue[-1]
                         if game_object.direction_queue
                         else game_object.direction)
        if new not in (last, OPPOSITE[last]) and len(
                game_object.direction_queue) < 2:
            game_object.direction_queue.append(new)


def occupied_cells(walls: Walls, snake: Snake, apple: Apple,
                   stubs: list[Stub]) -> list[Pointer]:
    """Возвращает все занятые клетки поля."""
    return (walls.positions + snake.positions + [apple.position]
            + [stub.position for stub in stubs])


def reset_game(snake: Snake, apple: Apple, stubs: list[Stub],
               walls: Walls) -> None:
    """Сбрасывает змейку и заново расставляет яблоко и огрызки."""
    global score
    snake.reset()
    respawn(apple, walls, snake, apple, stubs)
    for stub in stubs:
        respawn(stub, walls, snake, apple, stubs)
    score = 0


def respawn(obj: Apple, walls: Walls, snake: Snake, apple: Apple,
            stubs: list[Stub]) -> None:
    """Обновляет позицию объекта, избегая занятых ячеек."""
    obj.randomize_position(occupied_cells(walls, snake, apple, stubs))


def draw_score(score: int, high_score: int) -> None:
    """Отображает количество очков и рекорд."""
    font: pg.font.Font = pg.font.SysFont(
        'trebuchetms', 32, bold=True
    )

    score_text: pg.Surface = font.render(
        f'Score: {score}',
        True,
        SCORE_COLOR
    )

    high_score_text: pg.Surface = font.render(
        f'High Score: {high_score}',
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


def eat_apple(snake: Snake, apple: Apple, walls: Walls,
              stubs: list[Stub]) -> None:
    """Обрабатывает съедание яблока."""
    global score, high_score

    snake.length += 1

    current_score: int = snake.length - SNAKE_START_LENGTH

    if current_score > score:
        score = current_score

    if score > high_score:
        high_score = score

    respawn(apple, walls, snake, apple, stubs)


def main() -> None:
    """Инициализация PyGame:"""
    pg.init()
    snake: Snake = Snake()
    walls: Walls = Walls()
    start: Pointer = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    start_zone: list[Pointer] = [
        (start[0] + i * GRID_SIZE, start[1]) for i in range(-4, 6)]
    walls.generate(start_zone)
    apple: Apple = Apple(occupied_positions=walls.positions + snake.positions)
    stubs: list[Stub] = [
        Stub(occupied_positions=occupied_cells(walls, snake, apple, []))]
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

        target: int = 1 + (snake.length - SNAKE_START_LENGTH) // STUB_STEP
        del stubs[max(target, 1):]
        while len(stubs) < target:
            stubs.append(Stub(
                occupied_positions=occupied_cells(walls, snake, apple,
                                                  stubs)))

        handle_keys(snake)
        snake.update_direction()
        alive: bool = snake.move()

        if not alive or snake.get_head_position() in walls.positions:
            reset_game(snake, apple, stubs, walls)

        screen.fill(BOARD_BACKGROUND_COLOR)
        walls.draw()
        snake.draw()
        apple.draw()
        for stub in stubs:
            stub.draw()

        draw_score(score, high_score)
        pg.display.update()


if __name__ == '__main__':
    main()
