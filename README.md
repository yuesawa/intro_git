# 🧪 MolPredict Quest - QSAR学習ゲーム

QSAR（Quantitative Structure-Activity Relationship：定量的構造活性相関）解析を楽しく学べるWebアプリケーションゲームです。

## 📋 概要

MolPredict Questは、創薬研究に欠かせないQSAR解析の基礎を、ゲーム形式で習得できる教育ツールです。分子記述子の理解から予測モデルの構築、分子デザインまで、段階的に学習できます。

## 🎮 ゲームモード

### 1. 📚 チュートリアルモード
- 分子記述子（LogP、分子量、水素結合など）についてクイズ形式で学習
- 正解数をトラッキングして学習進捗を確認

### 2. 🤖 モデル構築モード
- 線形回帰とランダムフォレストの2つのモデルを選択可能
- SMILES式を入力して活性値を予測
- モデルの性能指標（R²、RMSE）を確認
- 分子記述子をリアルタイムで計算・表示

### 3. 🎯 分子デザインチャレンジ
- 目標活性値を達成する分子を設計
- 制約条件（分子量、LogP、水素結合供与体数）を満たす必要あり
- リアルタイムで条件達成状況をチェック

### 4. 📊 訓練データビュー
- モデル学習に使用する訓練データセットを確認
- 各化合物の記述子と活性値を一覧表示

## 🛠️ 技術スタック

- **バックエンド**: Flask (Python)
- **フロントエンド**: HTML5, CSS3, Vanilla JavaScript
- **化学計算**: RDKit
- **機械学習**: scikit-learn (線形回帰、ランダムフォレスト)

## 📦 インストール

### 前提条件
- Python 3.8以上
- pip

### セットアップ手順

1. リポジトリをクローン（または既にクローン済み）
```bash
cd intro_git
```

2. 仮想環境の作成（推奨）
```bash
python -m venv venv
source venv/bin/activate  # Windowsの場合: venv\Scripts\activate
```

3. 依存パッケージのインストール
```bash
pip install -r requirements.txt
```

## 🚀 使い方

### アプリケーションの起動

```bash
python app.py
```

ブラウザで以下のURLにアクセス:
```
http://localhost:5000
```

### 各モードの使い方

#### チュートリアルモード
1. 画面上部の「📚 チュートリアル」タブをクリック
2. 表示された問題の選択肢から回答を選択
3. 解説を読んで理解を深める
4. 「次の問題」ボタンで次の問題へ

#### モデル構築モード
1. 「🤖 モデル構築」タブをクリック
2. 予測モデルを選択（線形回帰 or ランダムフォレスト）
3. SMILES式を入力（例: `CCO`, `c1ccccc1O`）
4. 「活性予測」ボタンをクリック
5. 予測結果と分子記述子を確認

#### 分子デザインチャレンジ
1. 「🎯 分子デザイン」タブをクリック
2. 目標活性値と制約条件を確認
3. 条件を満たすSMILES式を入力
4. 「チェック」ボタンで評価
5. すべての条件をクリアすると成功メッセージが表示

#### 訓練データビュー
1. 「📊 訓練データ」タブをクリック
2. モデルの学習に使用されているデータセットを確認

## 📖 SMILES記法の例

以下は使用できるSMILES式の例です：

| SMILES | 化合物名 | 特徴 |
|--------|----------|------|
| `CCO` | エタノール | 簡単なアルコール |
| `c1ccccc1` | ベンゼン | 芳香環 |
| `c1ccccc1O` | フェノール | ベンゼン環+OH基 |
| `CC(C)O` | イソプロパノール | 分岐アルコール |
| `CCOc1ccccc1` | フェネトール | エーテル結合 |
| `Cc1ccccc1` | トルエン | メチル化ベンゼン |

## 🧬 分子記述子の説明

- **MW (Molecular Weight)**: 分子量
- **LogP**: 脂溶性の指標（高いほど親油性）
- **HBD (Hydrogen Bond Donors)**: 水素結合供与体の数
- **HBA (Hydrogen Bond Acceptors)**: 水素結合受容体の数
- **TPSA (Topological Polar Surface Area)**: 極性表面積
- **RotBonds**: 回転可能な結合の数
- **AromaticRings**: 芳香環の数

## 🎓 学習のヒント

1. まずチュートリアルモードで記述子の意味を理解しましょう
2. モデル構築モードで、構造の違いが活性値にどう影響するか試してみましょう
3. 訓練データを参考に、高活性化合物の特徴を見つけましょう
4. 分子デザインチャレンジで、学んだ知識を実践しましょう

## 🔧 カスタマイズ

### 訓練データの変更
`app.py`の`TRAINING_DATA`リストを編集することで、独自のデータセットを使用できます：

```python
TRAINING_DATA = [
    ("SMILES式", 活性値),
    # 追加のデータ...
]
```

### クイズの追加
`app.py`の`get_quiz()`関数内の`quizzes`リストに新しい問題を追加できます。

## 📝 ライセンス

このプロジェクトは教育目的で作成されています。

## 🤝 貢献

バグ報告や機能提案は、GitHubのIssuesでお願いします。

## 📚 参考資料

- [RDKit Documentation](https://www.rdkit.org/docs/)
- [SMILES記法の基礎](https://en.wikipedia.org/wiki/Simplified_molecular-input_line-entry_system)
- [QSAR解析入門](https://en.wikipedia.org/wiki/Quantitative_structure%E2%80%93activity_relationship)

---

楽しく学んで、創薬研究のスキルを身につけましょう！🎉
