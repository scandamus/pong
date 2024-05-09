import json
import asyncio

from asgiref.sync import async_to_sync
from channels.generic.websocket import AsyncWebsocketConsumer
from datetime import datetime as dt
from .game_logic import Paddle, Ball

import logging

logger = logging.getLogger(__name__)

CANVAS_WIDTH = 600
CANVAS_HEIGHT = 300


# 非同期通信を実現したいのでAsyncWebsocketConsumerクラスを継承
class PongConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.paddle1 = Paddle(CANVAS_WIDTH - 10, (CANVAS_HEIGHT - 75) / 2, 75, 10)
        self.paddle2 = Paddle(0, (CANVAS_HEIGHT - 75) / 2, 75, 10)
        self.ball = Ball(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2, 10)
        self.is_active = False
        self.scheduled_task = None

    async def connect(self):
        try:
            self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
            self.room_group_name = f"pong_{self.room_name}"
            logger.info(f"Room name: {self.room_name}, Room group name: {self.room_group_name}")
            await self.channel_layer.group_add(
                self.room_group_name, self.channel_name
            )

            await self.accept()

            # send updated ball pos until game end
            # クライアント側でonopenが発火したらループを開始する
            self.is_active = True
            # await self.schedule_ball_update()
            self.scheduled_task = asyncio.create_task(self.schedule_ball_update())

        except Exception as e:
            logger.error(f"Error connecting: {e}")

    async def disconnect(self, close_code):
        # Leave room group
        self.is_active = False
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
    async def pong_message(self, event):
        timestamp = event["timestamp"]
        message = event["message"]
        key = event.get('key')
        is_pressed = event.get('is_pressed', False)

        # キー入力によってパドルを操作
        if key and is_pressed:
            if key == "ArrowUp":
                self.paddle1.move("up", CANVAS_HEIGHT)
            elif key == "ArrowDown":
                self.paddle1.move("down", CANVAS_HEIGHT)
            elif key == "w":
                self.paddle2.move("up", CANVAS_HEIGHT)
            elif key == "s":
                self.paddle2.move("down", CANVAS_HEIGHT)

        # Send message to WebSocket
        await self.send_game_data(True, message=message, timestamp=timestamp)

    async def schedule_ball_update(self):
        try:
            while self.is_active:
                await asyncio.sleep(0.05)  # 50ミリ秒待機
                await self.update_ball_and_send_data()
        except asyncio.CancelledError:
            # タスクがキャンセルされたときのエラーハンドリング
            pass

    async def update_ball_and_send_data(self):
        self.is_active = self.ball.move(self.paddle1, self.paddle2, CANVAS_WIDTH, CANVAS_HEIGHT)
        timestamp = dt.utcnow().isoformat()
        await self.send_game_data(game_status=self.is_active, message="update_ball_pos", timestamp=timestamp)

    async def send_game_data(self, game_status, message, timestamp):
        await self.send(text_data=json.dumps({
            "message": message + f'\n{timestamp}\n\n',
            "game_status": game_status,
            "ball": {
                "x": self.ball.x,
                "y": self.ball.y,
                "dx": self.ball.dx,
                "dy": self.ball.dy,
                "radius": self.ball.radius,
            },
            "paddle1": {
                "x": self.paddle1.x,
                "y": self.paddle1.y,
                "width": self.paddle1.width,
                "height": self.paddle1.height
            },
            "paddle2": {
                "x": self.paddle2.x,
                "y": self.paddle2.y,
                "width": self.paddle2.width,
                "height": self.paddle2.height
            },
        }))
