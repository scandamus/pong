import json
import asyncio

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from datetime import datetime as dt
from .game_logic import Paddle, Ball

import logging
logger = logging.getLogger(__name__)

CANVAS_WIDTH = 600
CANVAS_HEIGHT = 300


class PongConsumer(WebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(args, kwargs)
        self.room_name = None
        self.room_group_name = None
        self.paddle1 = Paddle(CANVAS_WIDTH - 10, (CANVAS_HEIGHT - 75) / 2, 75, 10)
        self.paddle2 = Paddle(0, (CANVAS_HEIGHT - 75) / 2, 75, 10)
        self.ball = Ball(CANVAS_WIDTH / 2, CANVAS_HEIGHT / 2, 10)

    def connect(self):
        try:
            self.room_name = self.scope["url_route"]["kwargs"]["room_name"]
            self.room_group_name = f"pong_{self.room_name}"
            logger.info(f"Room name: {self.room_name}, Room group name: {self.room_group_name}")
            async_to_sync(self.channel_layer.group_add)(
                self.room_group_name, self.channel_name
            )

            self.accept()

            # send init paddle and ball
            self.send_game_data(True)
        except Exception as e:
            logger.error(f"Error connecting: {e}")

        # self.schedule_ball_update()

    def disconnect(self, close_code):
        # Leave room group
        if hasattr(self, 'room_group_name'):
            async_to_sync(self.channel_layer.group_discard)(
                self.room_group_name, self.channel_name
            )
        else:
            logger.warning("Disconnect called without a room_group_name set.")

    # Receive message from WebSocket
    def receive(self, text_data=None, bytes_data=None):
        text_data_json = json.loads(text_data)
        message = text_data_json["message"]
        # ball = text_data_json.get("ball")
        # paddle1 = text_data_json.get("paddle1")
        # paddle2 = text_data_json.get("paddle2")
        key = text_data_json['key']

        if text_data_json.get('message') == 'key_event':
            print(f"Key event received: {key}")  # コンソールにキーイベントを出力

        # キー入力によってパドルを操作
        if message == 'key_event':
            if key == "ArrowUp":
                self.paddle1.move("up", CANVAS_HEIGHT)
            elif key == "ArrowDown":
                self.paddle1.move("down", CANVAS_HEIGHT)
            elif key == "w":
                self.paddle2.move("up", CANVAS_HEIGHT)
            elif key == "s":
                self.paddle2.move("down", CANVAS_HEIGHT)


        # Send message to room group
        async_to_sync(self.channel_layer.group_send)(self.room_group_name, {
            # typeキーはgroup_send メソッド内で指定されるキーで、どのハンドラ関数をトリガするかを指定する
            "type": "pong.message",
            "timestamp": dt.utcnow().isoformat(),
            "message": message,
            "paddle1": self.paddle1,
            "paddle2": self.paddle2,
            "ball": self.ball,
        })

    # Receive message from room group
    def pong_message(self, event):
        timestamp = event["timestamp"]
        message = event["message"]
        # ball = event["ball"]
        # paddle1 = event["paddle1"]
        # paddle2 = event["paddle2"]

        # Send message to WebSocket
        self.send(text_data=json.dumps({
            "message": message + f'\n{timestamp}\n\np2={paddle2}\n\nball={ball}\n\np1={paddle1}',
            "paddle1": {
                "x": self.paddle1.x,
                "y": self.paddle1.y,
                "Height": self.paddle1.height,
                "Width": self.paddle1.width
            },
            "paddle2": {
                "x": self.paddle2.x,
                "y": self.paddle2.y,
                "Height": self.paddle2.height,
                "Width": self.paddle2.width
            },
            "ball": {
                "x": self.ball.x,
                "y": self.ball.y,
                "dx": self.ball.dx,
                "dy": self.ball.dy,
                "radius": self.ball.radius,
            },
            "game_status": True
        }))

    async def schedule_ball_update(self):
        while True:
            await asyncio.sleep(0.05)  # 50ミリ秒ごとに待機
            game_status = await self.update_ball_pos()  # ボールの位置を更新し、ゲーム続行かどうかを判定
            if not game_status:
                break  # ゲームオーバーならループを終了

    async def update_ball_pos(self):
        if not self.ball.move(self.paddle1, self.paddle2, CANVAS_WIDTH, CANVAS_HEIGHT):
            self.send_game_data(game_status=False)
            return False
        else:
            self.send_game_data(game_status=True)
            return True

    def send_game_data(self, game_status):
        self.send(text_data=json.dumps({
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