import random
import math
from .consts import (CANVAS_WIDTH, CANVAS_HEIGHT, REFLECTION_ANGLE,
                     CORNER_BLOCK_SIZE, CANVAS_WIDTH_MULTI, CANVAS_HEIGHT_MULTI)


def get_ball_direction_and_random_speed(angle_degrees, direction_multiplier):
    angle_radians = angle_degrees * (math.pi / 180)
    cos_value = math.cos(angle_radians)
    sin_value = math.sin(angle_radians)
    speed = random.randint(8, 9)
    return {
        "dx": speed * direction_multiplier * cos_value,
        "dy": speed * -sin_value,
    }


class Paddle:
    def __init__(self, x, y, thickness, length, orientation=None):
        self.x = x
        self.y = y
        self.thickness = thickness
        self.length = length
        self.speed = 0
        self.score = 0
        self.orientation = orientation

    def move(self):
        self.y += self.speed
        if self.y < 0:
            self.y = 0
        elif self.y + self.thickness > CANVAS_HEIGHT:
            self.y = CANVAS_HEIGHT - self.thickness

    def move_for_multiple(self):
        if self.orientation == 'horizontal':
            self.x += self.speed
            if self.x < CORNER_BLOCK_SIZE:
                self.x = CORNER_BLOCK_SIZE
            elif CANVAS_WIDTH_MULTI - CORNER_BLOCK_SIZE < self.x + self.length:
                self.x = CANVAS_WIDTH_MULTI - CORNER_BLOCK_SIZE - self.length
        elif self.orientation == 'vertical':
            self.y += self.speed
            if self.y < CORNER_BLOCK_SIZE:
                self.y = CORNER_BLOCK_SIZE
            elif CANVAS_HEIGHT_MULTI - CORNER_BLOCK_SIZE < self.y + self.thickness:
                self.y = CANVAS_HEIGHT_MULTI - CORNER_BLOCK_SIZE - self.thickness

    def increment_score(self):
        self.score += 1


class Ball:
    def __init__(self, x, y, size):
        tmp = get_ball_direction_and_random_speed(random.randint(30, 45), random.choice((-1, 1)))
        self.x = x
        self.y = y
        self.dx = tmp['dx']
        self.dy = tmp['dy']
        self.size = size
        self.flag = True  # 衝突判定を  True: する   False: しない

    def reset(self, x, y):
        tmp = get_ball_direction_and_random_speed(random.randint(30, 45), random.choice((-1, 1)))
        self.x = x
        self.y = y
        self.dx = tmp['dx']
        self.dy = tmp['dy']
        self.flag = True  # 衝突判定を  True: する   False: しない

    def move(self, paddle1, paddle2):
        # 上下の壁との衝突判定 # if 上 or 下
        if self.y + self.dy < 0 or self.y + self.size + self.dy > CANVAS_HEIGHT:
            self.dy = -self.dy
        # if self.flag:
        #     hit_paddle = collision_detection(self, paddle1, paddle2)
        #     if not hit_paddle:
        #         self.flag = False
        collision_with_paddle1 = False
        collision_with_paddle2 = False
        # 衝突判定
        if 0 < self.dx:
            collision_with_paddle1 = self.collision_detection(paddle1, "RIGHT")
        elif self.dx < 0:
            collision_with_paddle2 = self.collision_detection(paddle2, "LEFT")

        # 左の壁との衝突判定
        if self.x + self.size + self.dx < 0:
            paddle1.increment_score()
            self.reset(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2)
            return paddle1.score < 10
        # 右の壁との衝突判定
        elif self.x + self.dx > CANVAS_WIDTH:
            paddle2.increment_score()
            self.reset(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2)
            return paddle2.score < 10
        # 衝突判定がTrueの場合はpaddleにballを接触させるように
        if collision_with_paddle1:
            self.x = paddle1.x - self.size
        elif collision_with_paddle2:
            self.x = paddle2.x + paddle2.length
        else:
            self.x += self.dx
        self.y += self.dy

        return True

    def collision_detection(self, paddle, paddle_side):
        next_x = self.x + self.dx
        next_y = self.y + self.dy

        if paddle_side == "RIGHT" and paddle.x <= next_x + self.size <= paddle.x + paddle.length:
            if paddle.y <= next_y + self.size and next_y <= paddle.y + paddle.thickness:
                self.reflect_ball(paddle, paddle_side)
                return True
        elif paddle_side == "LEFT" and paddle.x <= next_x <= paddle.x + paddle.length:
            if paddle.y <= next_y + self.size and next_y <= paddle.y + paddle.thickness:
                self.reflect_ball(paddle, paddle_side)
                return True
        return False

    def reflect_ball(self, paddle, paddle_side):
        distance_from_paddle_center = (paddle.y + (paddle.thickness / 2)) - self.y
        # 最大の反射角を45°に設定した場合
        # paddleの大きさに依存した数値(1.2)なので、paddleを修正する場合にはここも修正が必要
        # 角度 / paddleの大きさ で修正
        normalize = REFLECTION_ANGLE / (paddle.thickness / 2)
        angle_degrees = distance_from_paddle_center * normalize
        # 左右で方向を逆に
        ball_direction = 1 if paddle_side == "LEFT" else -1
        new_direction = get_ball_direction_and_random_speed(angle_degrees, ball_direction)
        self.dx = new_direction["dx"]
        self.dy = new_direction["dy"]

