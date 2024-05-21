import random
import math
from .consts import (CANVAS_WIDTH, CANVAS_HEIGHT, REFLECTION_ANGLE, CORNER_BLOCK_SIZE,
                     CANVAS_WIDTH_MULTI, CANVAS_HEIGHT_MULTI, CORNER_BLOCK_THICKNESS, BALL_SIZE)


def get_ball_direction_and_random_speed(angle_degrees, direction_multiplier, orientation='vertical'):
    angle_radians = angle_degrees * (math.pi / 180)
    speed = random.randint(4, 5)
    if orientation == 'vertical':
        cos_value = math.cos(angle_radians)
        sin_value = math.sin(angle_radians)
        return {
            "dx": speed * direction_multiplier * cos_value,
            "dy": speed * -sin_value,
        }
    elif orientation == 'horizontal':
        cos_value = math.cos(angle_radians)
        sin_value = math.sin(angle_radians)
        return {
            "dx": speed * -sin_value,
            "dy": speed * direction_multiplier * cos_value,
        }


class Paddle:
    # 第三引数:horizontal->横の長さ   第四引数:vertical->縦の長さ   第五引数:orientation->paddleの移動方向
    def __init__(self, x, y, horizontal, vertical, orientation='vertical'):
        self.x = x
        self.y = y
        # 垂直方向のpaddleは厚さが横,長さが縦
        # 垂直方向のpaddleは厚さが縦,長さが横
        # これによって変数名でより視覚的にpaddleを管理できるように(二人対戦のときはデフォルトでvertical)
        if orientation == 'vertical':
            self.thickness = horizontal
            self.length = vertical
        elif orientation == 'horizontal':
            self.thickness = vertical
            self.length = horizontal
        self.speed = 0
        self.score = 0
        self.orientation = orientation

    def move(self):
        self.y += self.speed
        if self.y < 0:
            self.y = 0
        elif self.y + self.length > CANVAS_HEIGHT:
            self.y = CANVAS_HEIGHT - self.length

    def move_for_multiple(self):
        if self.orientation == 'horizontal':
            self.x += self.speed
            if self.x < 0:
                self.x = 0
            elif CANVAS_HEIGHT_MULTI < self.x + self.length:
                self.x = CANVAS_HEIGHT_MULTI - self.length
            # if self.x < CORNER_BLOCK_SIZE:
            #     self.x = CORNER_BLOCK_SIZE
            # elif CANVAS_WIDTH_MULTI - CORNER_BLOCK_SIZE < self.x + self.length:
            #     self.x = CANVAS_WIDTH_MULTI - CORNER_BLOCK_SIZE - self.length
        elif self.orientation == 'vertical':
            self.y += self.speed
            if self.y < 0:
                self.y = 0
            elif self.y + self.length > CANVAS_HEIGHT_MULTI:
                self.y = CANVAS_HEIGHT_MULTI - self.length
            # if self.y < CORNER_BLOCK_SIZE:
            #     self.y = CORNER_BLOCK_SIZE
            # elif CANVAS_HEIGHT_MULTI - CORNER_BLOCK_SIZE < self.y + self.thickness:
            #     self.y = CANVAS_HEIGHT_MULTI - CORNER_BLOCK_SIZE - self.thickness

    def increment_score(self):
        self.score += 1

    def decrement_score(self):
        self.score -= 1


class Ball:
    def __init__(self, x, y, size):
        tmp = get_ball_direction_and_random_speed(random.randint(30, 45), random.choice((-1, 1)))
        self.x = x
        self.y = y
        self.dx = tmp['dx']
        self.dy = tmp['dy']
        self.size = size
        self.flag = True  # 衝突判定を True:する False:しない

    def reset(self, x, y):
        tmp = get_ball_direction_and_random_speed(random.randint(30, 45), random.choice((-1, 1)))
        self.x = x
        self.y = y
        self.dx = tmp['dx']
        self.dy = tmp['dy']
        self.flag = True

    def move(self, paddle1, paddle2):
        # 上下の壁との衝突判定 # if 上 or 下
        if self.y + self.dy < 0 or self.y + self.size + self.dy > CANVAS_HEIGHT:
            self.dy = -self.dy
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
            self.x = paddle2.x + paddle2.thickness
        else:
            self.x += self.dx
        # y座標の操作
        if self.y + self.dy < 0:
            self.y = 0
            self.dy -= self.dy
        elif CANVAS_HEIGHT < self.y + self.size:
            self.y = CANVAS_HEIGHT - self.size
            self.dy -= self.dy
        else:
            self.y += self.dy
        return True

    def move_for_multiple(self, right_paddle, left_paddle, upper_paddle, lower_paddle):
        collision_with_right_paddle = self.collision_detection(right_paddle, "RIGHT")
        collision_with_left_paddle = self.collision_detection(left_paddle, "LEFT")
        collision_with_upper_paddle = self.collision_detection(upper_paddle, "UPPER")
        collision_with_lower_paddle = self.collision_detection(lower_paddle, "LOWER")
        # 壁を超えているか
        if CANVAS_WIDTH_MULTI < self.x + self.dx:
            right_paddle.decrement_score()
            self.reset(CANVAS_WIDTH_MULTI / 2, CANVAS_HEIGHT_MULTI / 2)
            return right_paddle.score > 0
        elif self.x + self.size + self.dx < 0:
            left_paddle.decrement_score()
            self.reset(CANVAS_WIDTH_MULTI / 2, CANVAS_HEIGHT_MULTI / 2)
            return left_paddle.score > 0
        elif self.y + self.size + self.dy < 0:
            upper_paddle.decrement_score()
            self.reset(CANVAS_WIDTH_MULTI / 2, CANVAS_HEIGHT_MULTI / 2)
            return upper_paddle.score > 0
        elif CANVAS_HEIGHT_MULTI < self.y + self.dy:
            lower_paddle.decrement_score()
            self.reset(CANVAS_WIDTH_MULTI / 2, CANVAS_HEIGHT_MULTI / 2)
            return lower_paddle.score > 0
        # y座標の操作
        if collision_with_upper_paddle:
            self.y = upper_paddle.y + upper_paddle.thickness
        elif collision_with_lower_paddle:
            self.y = lower_paddle.y - self.size
        else:
            self.y += self.dy
        # x座標の操作
        if collision_with_right_paddle:
            self.x = right_paddle.x - self.size
        elif collision_with_left_paddle:
            self.x = left_paddle.thickness
        else:
            self.x += self.dx
        return True

    def collision_detection(self, paddle, paddle_side):
        next_x = self.x + self.dx
        next_y = self.y + self.dy

        if paddle_side == "RIGHT" and paddle.x <= next_x + self.size <= paddle.x + paddle.thickness:
            if paddle.y <= next_y + self.size and next_y <= paddle.y + paddle.length:
                self.reflect_ball(paddle, paddle_side)
                return True
        elif paddle_side == "LEFT" and paddle.x <= next_x <= paddle.x + paddle.thickness:
            if paddle.y <= next_y + self.size and next_y <= paddle.y + paddle.length:
                self.reflect_ball(paddle, paddle_side)
                return True
        elif paddle_side == "UPPER" and paddle.y <= next_y <= paddle.y + paddle.thickness:
            if paddle.x <= next_x + self.size and next_x <= paddle.x + paddle.length:
                self.reflect_ball(paddle, paddle_side)
                return True
        elif paddle_side == "LOWER" and paddle.y <= next_y + self.size <= paddle.y + paddle.thickness:
            if paddle.x <= next_x + self.size and next_x <= paddle.x + paddle.length:
                self.reflect_ball(paddle, paddle_side)
                return True
        return False

    def reflect_ball(self, paddle, paddle_side):
        normalize = REFLECTION_ANGLE / (paddle.length / 2)
        if paddle_side == "RIGHT" or paddle_side == "LEFT":
            distance_from_paddle_center = (paddle.y + (paddle.length / 2)) - self.y
            # 最大の反射角を45°に設定した場合
            # paddleの大きさに依存した数値(1.2)なので、paddleを修正する場合にはここも修正が必要
            # 角度 / paddleの大きさ で修正
            angle_degrees = distance_from_paddle_center * normalize
            # 左右で方向を逆に
            ball_direction = 1 if paddle_side == "LEFT" else -1
            new_direction = get_ball_direction_and_random_speed(angle_degrees, ball_direction)
        else:
            distance_from_paddle_center = (paddle.x + (paddle.length / 2)) - self.x
            angle_degrees = distance_from_paddle_center * normalize
            ball_direction = 1 if paddle_side == "UPPER" else -1
            new_direction = get_ball_direction_and_random_speed(angle_degrees, ball_direction, "horizontal")
        self.dx = new_direction["dx"]
        self.dy = new_direction["dy"]
