---
name: p5js
description: Create interactive visual sketches and animations using p5.js
version: 1.0.0
tags: [p5js, creative-coding, visualization, animation, canvas]
category: creative
platform: all
triggers: [p5js, p5.js, クリエイティブコーディング, visualization, アニメーション, canvas, インタラクティブ, creative coding]
---

## 使用場面
データビジュアライゼーション、インタラクティブアニメーション、アート生成、教育用デモ。

## p5.js の基本構造
```javascript
// index.html に <script src="https://cdn.jsdelivr.net/npm/p5@1.9.0/lib/p5.min.js"> を追加

function setup() {
    createCanvas(800, 600);
    background(20);  // 背景色
}

function draw() {
    // 毎フレーム実行される（デフォルト 60fps）
    background(20, 20, 20, 10);  // トレイル効果
    
    fill(100, 200, 255);
    noStroke();
    circle(mouseX, mouseY, 20);  // マウス位置に円
}
```

## パーティクルシステム
```javascript
let particles = [];

class Particle {
    constructor(x, y) {
        this.pos = createVector(x, y);
        this.vel = p5.Vector.random2D().mult(random(1, 3));
        this.life = 255;
        this.size = random(4, 12);
    }
    
    update() {
        this.pos.add(this.vel);
        this.vel.y += 0.1;  // 重力
        this.life -= 5;
    }
    
    draw() {
        fill(255, 150, 50, this.life);
        noStroke();
        circle(this.pos.x, this.pos.y, this.size);
    }
    
    isDead() { return this.life <= 0; }
}

function draw() {
    background(0, 0, 0, 30);
    particles.push(new Particle(mouseX, mouseY));
    particles = particles.filter(p => !p.isDead());
    particles.forEach(p => { p.update(); p.draw(); });
}
```

## データビジュアライゼーション
```javascript
let data = [42, 85, 63, 27, 91, 55, 78];

function setup() {
    createCanvas(600, 400);
}

function draw() {
    background(240);
    let barW = width / data.length;
    
    data.forEach((val, i) => {
        let h = map(val, 0, 100, 0, height * 0.8);
        let c = lerpColor(color("#2196F3"), color("#F44336"), val / 100);
        
        fill(c);
        rect(i * barW + 5, height - h, barW - 10, h, 4);
        
        fill(50);
        textAlign(CENTER);
        text(val, i * barW + barW/2, height - h - 10);
    });
}
```

## ノイズを使ったオーガニックアニメーション
```javascript
let t = 0;

function draw() {
    background(10, 10, 30);
    
    stroke(100, 200, 255, 100);
    noFill();
    
    beginShape();
    for (let x = 0; x <= width; x += 5) {
        let n = noise(x * 0.005, t);
        let y = map(n, 0, 1, height * 0.3, height * 0.7);
        vertex(x, y);
    }
    endShape();
    
    t += 0.005;
}
```

## HTML に埋め込む
```html
<!DOCTYPE html>
<html>
<body style="margin:0;background:#000">
<script src="https://cdn.jsdelivr.net/npm/p5@1.9.0/lib/p5.min.js"></script>
<script>
// スケッチコードをここに貼る
</script>
</body>
</html>
```

## 注意事項
- `draw()` は毎フレーム呼ばれる（重い処理は `setup()` に移す）
- `noLoop()` でアニメーションを停止
- モバイル対応は `touchStarted()`, `touchMoved()` を使う

## 検証
ブラウザでスケッチが正常に動作し、インタラクションが機能すれば完了。
