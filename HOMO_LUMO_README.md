# HOMO/LUMO エネルギー計算ツール

xTBパッケージを使用して、SDFファイル内の複数分子のHOMO/LUMOエネルギーとそのギャップを計算するPythonスクリプトです。

## 必要な環境

- Python 3.7以上
- RDKit
- xTB (version 6.4以上推奨)

## インストール

### 1. RDKitのインストール

```bash
# pipを使用する場合
pip install rdkit

# condaを使用する場合（推奨）
conda install -c conda-forge rdkit
```

### 2. xTBのインストール

#### Condaを使用する場合（最も簡単）

```bash
conda install -c conda-forge xtb
```

#### ビルド済みバイナリを使用する場合

1. [xTB GitHubリリースページ](https://github.com/grimme-lab/xtb/releases)から最新版をダウンロード

```bash
# Linux x86_64の場合
wget https://github.com/grimme-lab/xtb/releases/download/v6.7.1/xtb-6.7.1-linux-x86_64.tar.xz
tar -xf xtb-6.7.1-linux-x86_64.tar.xz

# バイナリをPATHに追加
export PATH=$PATH:$(pwd)/xtb-6.7.1/bin
```

2. または、スクリプト実行時にパスを指定

```bash
python3 calculate_homo_lumo.py sample_molecules.sdf --xtb-path /path/to/xtb
```

#### ソースからビルドする場合

```bash
git clone https://github.com/grimme-lab/xtb.git
cd xtb
mkdir build && cd build
cmake ..
make
sudo make install
```

## 使用方法

### 基本的な使い方

```bash
python3 calculate_homo_lumo.py sample_molecules.sdf
```

### CSV形式で結果を保存

```bash
python3 calculate_homo_lumo.py sample_molecules.sdf -o results.csv
```

### xTBバイナリのパスを指定

```bash
python3 calculate_homo_lumo.py sample_molecules.sdf --xtb-path /custom/path/to/xtb
```

### 環境変数でxTBのパスを指定

```bash
export XTB_PATH=/custom/path/to/xtb
python3 calculate_homo_lumo.py sample_molecules.sdf
```

## サンプル分子の生成

テスト用のサンプルSDFファイルを生成するには：

```bash
python3 create_sample_molecules.py
```

これにより、ベンゼン、ナフタレン、アントラセンなど10種類の分子を含む `sample_molecules.sdf` が作成されます。

## 出力例

```
Processing molecules from sample_molecules.sdf...
--------------------------------------------------------------------------------

Processing: Benzene (1/10)
  HOMO: -9.2341 eV
  LUMO: -0.5234 eV
  GAP:  8.7107 eV

Processing: Naphthalene (2/10)
  HOMO: -8.1234 eV
  LUMO: -1.2345 eV
  GAP:  6.8889 eV

...

================================================================================
Summary of Results:
================================================================================
Molecule                       HOMO (eV)    LUMO (eV)    GAP (eV)     Status
--------------------------------------------------------------------------------
Benzene                        -9.2341      -0.5234      8.7107       success
Naphthalene                    -8.1234      -1.2345      6.8889       success
...
```

## 計算手法

- **計算レベル**: GFN2-xTB（Geometry, Frequency, Noncovalent interactions 2nd generation xTB）
- **出力**: HOMO/LUMOエネルギー（eV単位）とそのギャップ

## トラブルシューティング

### xTB binary not found

xTBがPATHに含まれていない場合は、以下のいずれかを実行してください：

1. `--xtb-path` オプションでパスを指定
2. `XTB_PATH` 環境変数を設定
3. xTBをシステムのPATHに追加

### 3D coordinate generation failed

入力SDFファイルの分子構造に問題がある可能性があります。分子が適切に読み込めるか確認してください。

### calculation failed - could not parse output

xTBの計算は完了しているが、出力の解析に失敗した場合です。xTBのバージョンによって出力形式が異なる可能性があります。

## ファイル一覧

- `calculate_homo_lumo.py`: メインの計算スクリプト
- `create_sample_molecules.py`: サンプル分子SDFファイル生成スクリプト
- `sample_molecules.sdf`: サンプル分子データ（10分子）
- `HOMO_LUMO_README.md`: このREADMEファイル

## 参考文献

- xTB公式ドキュメント: https://xtb-docs.readthedocs.io/
- xTB GitHub: https://github.com/grimme-lab/xtb
- RDKit: https://www.rdkit.org/

## ライセンス

このスクリプトはMITライセンスの下で公開されています。
xTBパッケージは独自のライセンス（LGPL-3.0）を持っています。
