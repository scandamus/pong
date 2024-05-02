// ノードを取得
const canvas = document.getElementById("pongcanvas");
// 2dの描画コンテキストにアクセスできるように
// キャンバスに描画するために使うツール
const ctx = canvas.getContext("2d");
let state = 1;
const startBallDirection = getBallDirectionAndRandomSpeed(getRandomInt(45, 90), choose([-1, 1]));
let ball = {
    x: canvas.width / 2,
    y: canvas.height / 2,
    dx: startBallDirection.dx,
    dy: startBallDirection.dy,
    // dx: 1,
    // dy: 1,
    Radius: 10,
};
//右
let paddle1 = {
    x: (canvas.width - 10),
    y: (canvas.height - 75) / 2,
    Height: 75,
    Width: 10,
};
// 左
let paddle2 = {
    x: 0,
    y: (canvas.height - 75) / 2,
    Height: 75,
    Width: 10,
};
function drawBall(obj) {
    ctx.beginPath();
    ctx.arc(obj.x, obj.y, obj.Radius, 0, Math.PI * 2);
    ctx.fillStyle = '#0095DD';
    ctx.fill();
    ctx.closePath();
}
function drawPaddle(obj) {
    ctx.beginPath();
    ctx.rect(obj.x, obj.y, obj.Width, obj.Height);
    ctx.fillStyle = '#0095DD';
    ctx.fill();
    ctx.closePath();
}
function getRandomArbitrary(min, max) {
    return Math.random() * (max - min) + min;
}
function getRandomInt(min, max) {
    // ceil()は引数以上の最大の整数を返す
    min = Math.ceil(min);
    // floor()は引数以下の最大の整数を返す
    max = Math.floor(max);
    return Math.floor(getRandomArbitrary(min, max)); //The maximum is exclusive and the minimum is inclusive
}
function choose(choices) {
    let index = Math.floor(Math.random() * choices.length);
    return choices[index];
}
function getBallDirectionAndRandomSpeed(angleDegrees, directionMultiplier) {
    // π/180(ラジアン単位の1度)で割ることで変換
    let angleRadians = angleDegrees * (Math.PI / 180);
    let cosValue = Math.cos(angleRadians);
    let sinValue = Math.sin(angleRadians);
    // 適当にスピードを決めてるが、これを変更できるようにすれば難易度調整できそう
    let speed = getRandomArbitrary(3, 6);
    return {
        dx: speed * directionMultiplier * cosValue,
        dy: speed * -sinValue,
    }
}
function handlePaddleCollision(paddle, paddleSide) {
    if (ball.y > paddle.y && ball.y < paddle.y + paddle.Height) {
        let distanceFromPaddleCenter = paddle.y + (paddle.Height / 2) - ball.y;
        // 最大の反射角を45°に設定した場合
        // paddleの大きさに依存した数値(1.2)なので、paddleを修正する場合にはここも修正が必要
        // 角度 / paddleの大きさ で修正
        let angleDegrees = distanceFromPaddleCenter * 1.2;
        // 左右で方向を逆に
        let ballDirection = (paddleSide === "RIGHT") ? -1 : 1;
        ballDirection = getBallDirectionAndRandomSpeed(angleDegrees, ballDirection);
        ball.dx = ballDirection.dx;
        ball.dy = ballDirection.dy;
    } else {
        state = 0;
    }
}
function collisionDetection() {
    // この関数をpaddleに当たったかを判定する関数に修正する
    // canvasの左半分か右半分かで処理を分岐する
    // 左
    if (ball.x - ball.Radius < paddle2.Width) {
        // paddle2の幅の範囲内にballがあるかを確認する
        handlePaddleCollision(paddle2, "LEFT");
    }
    // 右
    else if (ball.x + ball.Radius > canvas.width - paddle1.Width) {
        handlePaddleCollision(paddle1, "RIGHT");
    }
}
function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    drawBall(ball);
    drawPaddle(paddle1);
    drawPaddle(paddle2);
    if (state === 1) {
        collisionDetection();
    }
    if (ball.y + ball.dy > canvas.height - ball.Radius ||
        ball.y + ball.dy < ball.Radius) {
        ball.dy = -ball.dy;
    }
    if (paddle1UpPressed) {
        paddle1.y -= 7;
        if (paddle1.y < 0) {
            paddle1.y = 0;
        }
    }
    if (paddle1DownPressed) {
        paddle1.y += 7;
        if (paddle1.y + paddle1.Height > canvas.height) {
            paddle1.y = canvas.height - paddle1.Height;
        }
    }
    if (paddle2UpPressed) {
        paddle2.y -= 7;
        if (paddle2.y < 0) {
            paddle2.y = 0;
        }
    }
    if (paddle2DownPressed) {
        paddle2.y += 7;
        if (paddle2.y + paddle2.Height > canvas.height) {
            paddle2.y = canvas.height - paddle2.Height;
        }
    }
    if (ball.x < ball.Radius || ball.x > canvas.width - ball.Radius) {
        alert('GAME OVER');
        document.location.reload();
        clearInterval(interval);
    }
    // ballの動きを変えるために修正
    ball.x += ball.dx;
    ball.y += ball.dy;
}
// 押されたとき
document.addEventListener("keydown", keyDownHandler, false);
// 離れたとき
document.addEventListener("keyup", keyUpHandler, false);
// 右
let paddle1UpPressed = false;
let paddle1DownPressed = false;
// 左
let paddle2UpPressed = false;
let paddle2DownPressed = false;
function keyDownHandler (e) {
    if (e.key === "ArrowUp") {
        paddle1UpPressed = true;
    } else if (e.key === "ArrowDown") {
        paddle1DownPressed = true;
    } else if (e.key === "w") {
        paddle2UpPressed = true;
    } else if (e.key === "s") {
        paddle2DownPressed = true;
    }
}
function keyUpHandler (e) {
    if (e.key === "ArrowUp") {
        paddle1UpPressed = false;
    } else if (e.key === "ArrowDown") {
        paddle1DownPressed = false;
    } else if (e.key === "w") {
        paddle2UpPressed = false;
    } else if (e.key === "s") {
        paddle2DownPressed = false;
    }
}
let interval = setInterval(draw, 10);
