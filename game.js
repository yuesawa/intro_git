// ゲームの状態定数
const STATE = {
    MAP: 'MAP',
    BATTLE: 'BATTLE',
    MESSAGE: 'MESSAGE'
};

// 定数
const TILE_SIZE = 32;
const CANVAS_WIDTH = 640;
const CANVAS_HEIGHT = 480;
const MAP_COLS = 20;
const MAP_ROWS = 15;

// 色の定義
const COLORS = {
    GRASS: '#4caf50',
    DIRT: '#795548',
    WALL: '#607d8b',
    WATER: '#2196f3',
    PLAYER: '#f44336', // 赤い帽子
    UI_BG: 'rgba(0,0,0,0.8)',
    UI_BORDER: '#fff'
};

// マップデータ (0:土, 1:壁, 2:草むら, 3:水)
// シンプルなマップ生成
const MAP_DATA = [
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,0,0,1,2,2,2,2,1,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,0,1,2,2,2,2,1,0,0,0,0,0,0,0,1],
    [1,0,0,3,3,0,0,0,0,0,0,0,0,0,0,1,1,0,0,1],
    [1,0,0,3,3,0,0,0,0,0,0,0,0,0,0,1,1,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,2,2,2,2,2,2,2,0,0,0,0,0,0,0,1],
    [1,0,0,0,0,2,2,2,2,2,2,2,0,0,0,0,0,0,0,1],
    [1,1,1,0,0,2,2,2,2,2,2,2,0,0,0,0,0,0,0,1],
    [1,2,2,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,2,2,0,0,0,0,0,0,0,0,0,0,1,1,1,1,0,0,1],
    [1,2,2,0,0,1,1,0,0,0,0,0,0,1,2,2,1,0,0,1],
    [1,0,0,0,0,1,1,0,0,0,0,0,0,1,2,2,1,0,0,1],
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1]
];

// ポケモンデータ
const POKEMON_DB = [
    { name: 'ヒトカゲ風', color: '#ff9800', hp: 30, maxHp: 30, attack: 8, type: 'fire' },
    { name: 'フシギダネ風', color: '#8bc34a', hp: 35, maxHp: 35, attack: 6, type: 'grass' },
    { name: 'ゼニガメ風', color: '#03a9f4', hp: 32, maxHp: 32, attack: 7, type: 'water' },
    { name: 'ピカチュウ風', color: '#ffeb3b', hp: 28, maxHp: 28, attack: 9, type: 'electric' }
];

class Game {
    constructor() {
        this.canvas = document.getElementById('gameCanvas');
        this.ctx = this.canvas.getContext('2d');
        this.state = STATE.MAP;
        
        this.player = {
            x: 2, // グリッド座標
            y: 2,
            direction: 'down', // up, down, left, right
            moving: false,
            moveProgress: 0
        };

        this.myPokemon = { ...POKEMON_DB[0] }; // 最初はヒトカゲ風
        this.wildPokemon = null;
        this.battleLog = [];

        this.keys = {};
        
        this.ui = {
            messageBox: document.getElementById('message-box'),
            battleMenu: document.getElementById('battle-menu'),
            btnAttack: document.getElementById('btn-attack'),
            btnRun: document.getElementById('btn-run')
        };

        this.initInput();
        this.lastTime = 0;
        this.loop = this.loop.bind(this);
        requestAnimationFrame(this.loop);

        this.showMessage('冒険の始まりだ！矢印キーで移動しよう。');
    }

    initInput() {
        window.addEventListener('keydown', (e) => {
            this.keys[e.key] = true;
            if (['ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight'].includes(e.key)) {
                e.preventDefault();
            }
            
            // 会話送りなど
            if ((e.key === 'Enter' || e.key === ' ') && this.state === STATE.MESSAGE) {
                this.closeMessage();
            }
        });

        window.addEventListener('keyup', (e) => {
            this.keys[e.key] = false;
        });

        this.ui.btnAttack.addEventListener('click', () => this.battleAction('attack'));
        this.ui.btnRun.addEventListener('click', () => this.battleAction('run'));
    }

    showMessage(text, callback = null) {
        this.previousState = this.state;
        this.state = STATE.MESSAGE;
        this.ui.messageBox.style.display = 'block';
        this.ui.messageBox.textContent = text;
        this.messageCallback = callback;
    }

    closeMessage() {
        this.ui.messageBox.style.display = 'none';
        if (this.messageCallback) {
            const cb = this.messageCallback;
            this.messageCallback = null;
            cb();
        } else {
            // 前の状態に戻す（ただしバトル開始時などは例外処理が必要かも）
            if (this.wildPokemon && this.wildPokemon.hp > 0) {
                 // バトル中ならバトルへ戻る
                 this.state = STATE.BATTLE;
                 this.ui.battleMenu.style.display = 'flex';
            } else {
                this.state = STATE.MAP;
            }
        }
    }

    startBattle() {
        // ランダムなポケモンを選出
        const template = POKEMON_DB[Math.floor(Math.random() * POKEMON_DB.length)];
        this.wildPokemon = JSON.parse(JSON.stringify(template)); // Deep copy
        
        this.state = STATE.BATTLE;
        this.ui.battleMenu.style.display = 'none'; // メッセージ中は非表示
        
        this.showMessage(`あ！　やせいの　${this.wildPokemon.name}が　とびだしてきた！`, () => {
            this.state = STATE.BATTLE;
            this.ui.battleMenu.style.display = 'flex';
            this.showMessage(`ゆけっ！　${this.myPokemon.name}！`, () => {
                this.ui.battleMenu.style.display = 'flex';
                this.state = STATE.BATTLE;
            });
        });
    }

    battleAction(action) {
        if (this.state !== STATE.BATTLE) return;
        
        this.ui.battleMenu.style.display = 'none';

        if (action === 'run') {
            this.showMessage('うまく　にげきれた！', () => {
                this.endBattle();
            });
            return;
        }

        if (action === 'attack') {
            // 自分の攻撃
            const damage = Math.floor(this.myPokemon.attack * (1 + Math.random() * 0.5));
            this.wildPokemon.hp -= damage;
            if (this.wildPokemon.hp < 0) this.wildPokemon.hp = 0;

            this.showMessage(`${this.myPokemon.name}の　こうげき！\n${this.wildPokemon.name}に　${damage}のダメージ！`, () => {
                if (this.wildPokemon.hp <= 0) {
                    this.showMessage(`${this.wildPokemon.name}は　たおれた！\nけいけんちを　かくとくした！`, () => {
                        this.endBattle();
                    });
                } else {
                    // 敵の攻撃
                    setTimeout(() => {
                        const enemyDmg = Math.floor(this.wildPokemon.attack * (0.8 + Math.random() * 0.5));
                        this.myPokemon.hp -= enemyDmg;
                        if (this.myPokemon.hp < 0) this.myPokemon.hp = 0;

                        this.showMessage(`${this.wildPokemon.name}の　こうげき！\n${this.myPokemon.name}に　${enemyDmg}のダメージ！`, () => {
                            if (this.myPokemon.hp <= 0) {
                                this.showMessage(`${this.myPokemon.name}は　たおれてしまった...\nめのまえが　まっくらに　なった！`, () => {
                                    // 全回復してリスタート
                                    this.myPokemon.hp = this.myPokemon.maxHp;
                                    this.player.x = 2;
                                    this.player.y = 2;
                                    this.endBattle();
                                });
                            } else {
                                // ターン継続
                                this.state = STATE.BATTLE;
                                this.ui.battleMenu.style.display = 'flex';
                            }
                        });
                    }, 500);
                }
            });
        }
    }

    endBattle() {
        this.wildPokemon = null;
        this.state = STATE.MAP;
        this.ui.battleMenu.style.display = 'none';
        this.ui.messageBox.style.display = 'none';
    }

    update(dt) {
        if (this.state === STATE.MAP) {
            this.updateMap();
        }
    }

    updateMap() {
        // 移動中でなければ入力受付
        if (!this.player.moving) {
            let dx = 0;
            let dy = 0;

            if (this.keys['ArrowUp']) dy = -1;
            else if (this.keys['ArrowDown']) dy = 1;
            else if (this.keys['ArrowLeft']) dx = -1;
            else if (this.keys['ArrowRight']) dx = 1;

            if (dx !== 0 || dy !== 0) {
                const newX = this.player.x + dx;
                const newY = this.player.y + dy;

                // 壁判定
                if (newX >= 0 && newX < MAP_COLS && newY >= 0 && newY < MAP_ROWS) {
                    const tile = MAP_DATA[newY][newX];
                    if (tile !== 1 && tile !== 3) { // 壁と水以外は通れる
                        this.player.x = newX;
                        this.player.y = newY;
                        
                        // 移動後の処理
                        this.checkEncounter(tile);
                    }
                }
                // 簡易的な移動ウェイト（スムーズな移動アニメーションは省略）
                this.player.moving = true;
                setTimeout(() => { this.player.moving = false; }, 150);
            }
        }
    }

    checkEncounter(tileType) {
        // 草むら(2)ならエンカウント判定
        if (tileType === 2) {
            if (Math.random() < 0.15) { // 15%の確率
                this.player.moving = false; // 移動停止
                this.startBattle();
            }
        }
    }

    draw() {
        this.ctx.clearRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);

        if (this.state === STATE.MAP || this.state === STATE.MESSAGE) {
            this.drawMap();
        } else if (this.state === STATE.BATTLE) {
            this.drawBattle();
        }
    }

    drawMap() {
        for (let y = 0; y < MAP_ROWS; y++) {
            for (let x = 0; x < MAP_COLS; x++) {
                const tile = MAP_DATA[y][x];
                let color = COLORS.DIRT;
                if (tile === 1) color = COLORS.WALL;
                if (tile === 2) color = COLORS.GRASS;
                if (tile === 3) color = COLORS.WATER;

                this.ctx.fillStyle = color;
                this.ctx.fillRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
                
                // グリッド線（薄く）
                this.ctx.strokeStyle = 'rgba(0,0,0,0.1)';
                this.ctx.strokeRect(x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE);
            }
        }

        // プレイヤー描画
        this.ctx.fillStyle = COLORS.PLAYER;
        // 少し小さめに描画してキャラっぽく
        const px = this.player.x * TILE_SIZE + 4;
        const py = this.player.y * TILE_SIZE + 4;
        this.ctx.fillRect(px, py, TILE_SIZE - 8, TILE_SIZE - 8);
        
        // 帽子のような飾り
        this.ctx.fillStyle = '#fff';
        this.ctx.fillRect(px + 4, py + 4, 4, 4);
        this.ctx.fillRect(px + 16, py + 4, 4, 4);
    }

    drawBattle() {
        // 背景
        this.ctx.fillStyle = '#222';
        this.ctx.fillRect(0, 0, CANVAS_WIDTH, CANVAS_HEIGHT);
        
        // バトルフロア
        this.ctx.fillStyle = '#888';
        this.ctx.beginPath();
        this.ctx.ellipse(180, 300, 120, 40, 0, 0, Math.PI * 2); // 味方側
        this.ctx.fill();

        this.ctx.beginPath();
        this.ctx.ellipse(460, 150, 120, 40, 0, 0, Math.PI * 2); // 敵側
        this.ctx.fill();

        // 敵ポケモン
        if (this.wildPokemon) {
            this.drawPokemonSprite(460, 130, this.wildPokemon.color, true);
            this.drawStatusBox(20, 20, this.wildPokemon, false);
        }

        // 味方ポケモン
        this.drawPokemonSprite(180, 280, this.myPokemon.color, false);
        this.drawStatusBox(360, 300, this.myPokemon, true);
    }

    drawPokemonSprite(x, y, color, isEnemy) {
        this.ctx.fillStyle = color;
        const size = 80;
        // シンプルな正方形モンスター
        this.ctx.fillRect(x - size/2, y - size, size, size);
        
        // 目
        this.ctx.fillStyle = 'white';
        if (isEnemy) {
            this.ctx.fillRect(x - 20, y - 60, 15, 15);
            this.ctx.fillRect(x + 5, y - 60, 15, 15);
            this.ctx.fillStyle = 'black';
            this.ctx.fillRect(x - 15, y - 55, 5, 5);
            this.ctx.fillRect(x + 10, y - 55, 5, 5);
        } else {
            // 背中側
            this.ctx.fillRect(x - 20, y - 60, 10, 10);
            this.ctx.fillRect(x + 10, y - 60, 10, 10);
        }
    }

    drawStatusBox(x, y, pokemon, isSelf) {
        const width = 260;
        const height = 80;
        
        // 枠
        this.ctx.fillStyle = 'rgba(255, 255, 255, 0.9)';
        this.ctx.fillRect(x, y, width, height);
        this.ctx.strokeStyle = '#000';
        this.ctx.lineWidth = 3;
        this.ctx.strokeRect(x, y, width, height);

        // 名前
        this.ctx.fillStyle = '#000';
        this.ctx.font = '20px "Courier New"';
        this.ctx.fillText(pokemon.name, x + 15, y + 30);
        
        // HPバー背景
        this.ctx.fillStyle = '#555';
        this.ctx.fillRect(x + 60, y + 45, 180, 15);
        
        // HPバー現在値
        const hpRatio = pokemon.hp / pokemon.maxHp;
        if (hpRatio > 0.5) this.ctx.fillStyle = '#4caf50'; // 緑
        else if (hpRatio > 0.2) this.ctx.fillStyle = '#ffeb3b'; // 黄
        else this.ctx.fillStyle = '#f44336'; // 赤

        this.ctx.fillRect(x + 60, y + 45, 180 * hpRatio, 15);

        // HPテキスト
        this.ctx.font = '16px "Courier New"';
        this.ctx.fillStyle = '#000';
        this.ctx.fillText(`HP:`, x + 15, y + 58);
        if (isSelf) {
            this.ctx.fillText(`${pokemon.hp}/${pokemon.maxHp}`, x + 160, y + 75);
        }
    }

    loop(timestamp) {
        const dt = timestamp - this.lastTime;
        this.lastTime = timestamp;

        this.update(dt);
        this.draw();

        requestAnimationFrame(this.loop);
    }
}

// ゲーム開始
window.onload = () => {
    const game = new Game();
};