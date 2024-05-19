import json
import asyncio

from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime as dt
from .game_logic import Paddle, Ball
from .consts import (CANVAS_WIDTH, CANVAS_HEIGHT, PADDLE_LENGTH, PADDLE_THICKNESS, PADDING,
                     BALL_SIZE, CANVAS_WIDTH_MULTI, CANVAS_HEIGHT_MULTI)

import logging

logger = logging.getLogger(__name__)


# 非同期通信を実現したいのでAsyncWebsocketConsumerクラスを継承
class PongConsumer(AsyncWebsocketConsumer):
    scheduled_task = None
    right_paddle = Paddle(CANVAS_WIDTH - PADDLE_THICKNESS - PADDING, (CANVAS_HEIGHT - PADDLE_LENGTH) / 2,
                          PADDLE_LENGTH, PADDLE_THICKNESS)
    left_paddle = Paddle(PADDING, (CANVAS_HEIGHT - PADDLE_LENGTH) / 2, PADDLE_LENGTH, PADDLE_THICKNESS)
    ball = Ball(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2, BALL_SIZE)
    ready = False
    game_continue = False

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None

    async def connect(self):
        try:
            self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
            self.room_group_name = f"pong_{self.room_name}"
            logger.info(f"Room name: {self.room_name}, Room group name: {self.room_group_name}")
            await self.channel_layer.group_add(
                self.room_group_name, self.channel_name
            )

            await self.accept()

            # クライアント側でonopenが発火したらループを開始する
            if not self.ready:
                self.ready = True
                self.scheduled_task = asyncio.create_task(self.schedule_ball_update())

        except Exception as e:
            logger.error(f"Error connecting: {e}")

    async def disconnect(self, close_code):
        # Leave room group
        self.game_continue = False
        if self.scheduled_task:
            self.scheduled_task.cancel()
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        if message == 'key_event':
            key = text_data_json['key']
            is_pressed = text_data_json['is_pressed']
            print(f"Key event received: {key}" f"\tis_pressed: {is_pressed}")  # コンソールにキーイベントを出力

            # Send message to room group
            await self.channel_layer.group_send(self.room_group_name, {
                # typeキーはgroup_send メソッド内で指定されるキーで、どのハンドラ関数をトリガするかを指定する
                "type": "pong.message",
                # ここで二つのキーを渡すことでpong_message内で辞書としてアクセスできる
                "timestamp": dt.utcnow().isoformat(),
                "message": message,
                "key": key,
                "is_pressed": is_pressed,
            })

    # Receive message from room group
    async def pong_message(self, data):
        timestamp = data["timestamp"]
        message = data["message"]
        key = data.get('key')
        is_pressed = data.get('is_pressed', False)

        # キー入力によってパドルを操作
        if key and is_pressed:
            if key == "ArrowUp":
                self.right_paddle.speed = -10
            elif key == "ArrowDown":
                self.right_paddle.speed = 10
            elif key == "w":
                self.left_paddle.speed = -10
            elif key == "s":
                self.left_paddle.speed = 10
        else:
            if key == "ArrowUp":
                self.right_paddle.speed = 0
            elif key == "ArrowDown":
                self.right_paddle.speed = 0
            elif key == "w":
                self.left_paddle.speed = 0
            elif key == "s":
                self.left_paddle.speed = 0

        # Send message to WebSocket
        # await self.send_game_data(True, message=message, timestamp=timestamp)

    async def schedule_ball_update(self):
        self.game_continue = True
        try:
            while self.game_continue:
                #                await asyncio.sleep(0.05)  # 50ミリ秒待機
                await asyncio.sleep(1/60)  # 60Hz
                self.game_continue = await self.update_ball_and_send_data()
                if not self.game_continue:
                    await self.channel_layer.group_send(self.room_group_name, {
                        "type": "send_game_over_message",
                        "message": "GameOver",
                    })

        except asyncio.CancelledError:
            # タスクがキャンセルされたときのエラーハンドリング
            # 今は特に書いていないのでpass
            pass

    async def update_ball_and_send_data(self):
        self.right_paddle.move()
        self.left_paddle.move()
        game_continue = self.ball.move(self.right_paddle, self.left_paddle)
        await self.channel_layer.group_send(self.room_group_name, {
            "type": "ball.message",
            "message": "update_ball_pos",
            "timestamp": dt.utcnow().isoformat(),
        })
        return game_continue

    async def ball_message(self, data):
        message = data["message"]
        timestamp = data["timestamp"]
        await self.send_game_data(game_status=True, message=message, timestamp=timestamp)

    async def send_game_data(self, game_status, message, timestamp):
        await self.send(text_data=json.dumps({
            "message": message + f'\n{timestamp}\n\n',
            "game_status": game_status,
            "ball": {
                "x": self.ball.x,
                "y": self.ball.y,
                "dx": self.ball.dx,
                "dy": self.ball.dy,
                "size": self.ball.size,
            },
            "right_paddle": {
                "x": self.right_paddle.x,
                "y": self.right_paddle.y,
                "length": self.right_paddle.length,
                "thickness": self.right_paddle.thickness,
                "score": self.right_paddle.score,
            },
            "left_paddle": {
                "x": self.left_paddle.x,
                "y": self.left_paddle.y,
                "length": self.left_paddle.length,
                "thickness": self.left_paddle.thickness,
                "score": self.left_paddle.score,
            },
        }))

    async def send_game_over_message(self, event):
        message = event["message"]
        timestamp = dt.utcnow().isoformat()
        await self.send_game_data(game_status=False, message=message, timestamp=timestamp)


class MultiPongConsumer(AsyncWebsocketConsumer):
    scheduled_task = None
    right_paddle = Paddle(CANVAS_WIDTH_MULTI - PADDLE_THICKNESS, (CANVAS_HEIGHT_MULTI / 2) - (PADDLE_LENGTH / 2),
                          PADDLE_LENGTH, PADDLE_THICKNESS, 'vertical')
    left_paddle = Paddle(0, (CANVAS_HEIGHT_MULTI / 2) - (PADDLE_LENGTH / 2), PADDLE_LENGTH,
                         PADDLE_THICKNESS, 'vertical')
    upper_paddle = Paddle((CANVAS_WIDTH_MULTI / 2) - (PADDLE_LENGTH / 2), 0, PADDLE_THICKNESS,
                          PADDLE_LENGTH, 'horizontal')
    lower_paddle = Paddle((CANVAS_WIDTH_MULTI / 2) - (PADDLE_LENGTH / 2), CANVAS_HEIGHT_MULTI - PADDLE_THICKNESS,
                          PADDLE_THICKNESS, PADDLE_LENGTH, 'horizontal')
    ball = Ball(CANVAS_WIDTH_MULTI / 2, CANVAS_HEIGHT_MULTI / 2, BALL_SIZE)
    ready = False
    game_continue = False

    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None

    async def connect(self):
        try:
            self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
            self.room_group_name = f"pong_{self.room_name}"
            logger.info(f"Room name: {self.room_name}, Room group name: {self.room_group_name}")
            await self.channel_layer.group_add(
                self.room_group_name, self.channel_name
            )

            await self.accept()

            # クライアント側でonopenが発火したらループを開始する
            if not self.ready:
                self.ready = True
                self.scheduled_task = asyncio.create_task(self.schedule_ball_update())

        except Exception as e:
            logger.error(f"Error connecting: {e}")

    async def disconnect(self, close_code):
        # Leave room group
        self.game_continue = False
        if self.scheduled_task:
            self.scheduled_task.cancel()
        await self.channel_layer.group_discard(
            self.room_group_name, self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        if message == 'key_event':
            key = text_data_json['key']
            is_pressed = text_data_json['is_pressed']
            print(f"Key event received: {key}" f"\tis_pressed: {is_pressed}")  # コンソールにキーイベントを出力

            # Send message to room group
            await self.channel_layer.group_send(self.room_group_name, {
                # typeキーはgroup_send メソッド内で指定されるキーで、どのハンドラ関数をトリガするかを指定する
                "type": "pong.message",
                # ここで二つのキーを渡すことでpong_message内で辞書としてアクセスできる
                "timestamp": dt.utcnow().isoformat(),
                "message": message,
                "key": key,
                "is_pressed": is_pressed,
            })

    # Receive message from room group
    async def pong_message(self, data):
        timestamp = data["timestamp"]
        message = data["message"]
        key = data.get('key')
        is_pressed = data.get('is_pressed', False)

        # キー入力によってパドルを操作
        if key and is_pressed:
            if key == "ArrowUp":
                self.right_paddle.speed = -10
            elif key == "ArrowDown":
                self.right_paddle.speed = 10
            elif key == "ArrowLeft":
                self.upper_paddle.speed = -10
            elif key == "ArrowRight":
                self.upper_paddle.speed = 10
            elif key == "w":
                self.left_paddle.speed = -10
            elif key == "s":
                self.left_paddle.speed = 10
            elif key == "a":
                self.lower_paddle.speed = -10
            elif key == "d":
                self.lower_paddle.speed = 10
        else:
            if key == "ArrowUp":
                self.right_paddle.speed = 0
            elif key == "ArrowDown":
                self.right_paddle.speed = 0
            elif key == "ArrowLeft":
                self.upper_paddle.speed = 0
            elif key == "ArrowRight":
                self.upper_paddle.speed = 0
            elif key == "w":
                self.left_paddle.speed = 0
            elif key == "s":
                self.left_paddle.speed = 0
            elif key == "a":
                self.lower_paddle.speed = 0
            elif key == "d":
                self.lower_paddle.speed = 0

    async def schedule_ball_update(self):
        self.game_continue = True
        try:
            while self.game_continue:
                #                await asyncio.sleep(0.05)  # 50ミリ秒待機
                await asyncio.sleep(1/60)  # 60Hz
                self.game_continue = await self.update_ball_and_send_data()
                if not self.game_continue:
                    await self.channel_layer.group_send(self.room_group_name, {
                        "type": "send_game_over_message",
                        "message": "GameOver",
                    })

        except asyncio.CancelledError:
            # タスクがキャンセルされたときのエラーハンドリング
            # 今は特に書いていないのでpass
            pass

    async def update_ball_and_send_data(self):
        self.right_paddle.move_for_multiple()
        self.left_paddle.move_for_multiple()
        self.upper_paddle.move_for_multiple()
        self.lower_paddle.move_for_multiple()
        game_continue = self.ball.move(self.right_paddle, self.left_paddle)
        # game_continue = False
        await self.channel_layer.group_send(self.room_group_name, {
            "type": "ball.message",
            "message": "update_ball_pos",
            "timestamp": dt.utcnow().isoformat(),
        })
        return game_continue

    async def ball_message(self, data):
        message = data["message"]
        timestamp = data["timestamp"]
        await self.send_game_data(game_status=True, message=message, timestamp=timestamp)

    async def send_game_data(self, game_status, message, timestamp):
        await self.send(text_data=json.dumps({
            "message": message + f'\n{timestamp}\n\n',
            "game_status": game_status,
            "ball": {
                "x": self.ball.x,
                "y": self.ball.y,
                "dx": self.ball.dx,
                "dy": self.ball.dy,
                "size": self.ball.size,
            },
            "right_paddle": {
                "x": self.right_paddle.x,
                "y": self.right_paddle.y,
                "length": self.right_paddle.length,
                "thickness": self.right_paddle.thickness,
                "score": self.right_paddle.score,
            },
            "left_paddle": {
                "x": self.left_paddle.x,
                "y": self.left_paddle.y,
                "length": self.left_paddle.length,
                "thickness": self.left_paddle.thickness,
                "score": self.left_paddle.score,
            },
            "upper_paddle": {
                "x": self.upper_paddle.x,
                "y": self.upper_paddle.y,
                "length": self.upper_paddle.length,
                "thickness": self.upper_paddle.thickness,
                "score": self.upper_paddle.score,
            },
            "lower_paddle": {
                "x": self.lower_paddle.x,
                "y": self.lower_paddle.y,
                "length": self.lower_paddle.length,
                "thickness": self.lower_paddle.thickness,
                "score": self.lower_paddle.score,
            },
        }))

    async def send_game_over_message(self, event):
        message = event["message"]
        timestamp = dt.utcnow().isoformat()
        await self.send_game_data(game_status=False, message=message, timestamp=timestamp)
