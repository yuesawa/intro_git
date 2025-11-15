#!/usr/bin/env python3
"""
HOMO/LUMO エネルギーとギャップ計算スクリプト
xTBパッケージを使用してSDFファイル内の複数分子を処理
"""

import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path
from rdkit import Chem
import re


def find_xtb_binary():
    """xTBバイナリのパスを探す"""
    # 環境変数から取得
    xtb_path = os.environ.get('XTB_PATH', 'xtb')

    # which コマンドで確認
    try:
        result = subprocess.run(['which', xtb_path],
                              capture_output=True,
                              text=True,
                              check=False)
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass

    # ローカルディレクトリをチェック
    local_paths = [
        './xtb',
        './xtb-6.7.1/bin/xtb',
        '../xtb',
        os.path.expanduser('~/xtb/bin/xtb'),
    ]

    for path in local_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    return 'xtb'  # デフォルトでPATHから探す


def parse_xtb_output(output_text):
    """
    xTBの出力からHOMO/LUMOエネルギーを抽出
    """
    homo_energy = None
    lumo_energy = None
    gap = None

    lines = output_text.split('\n')

    for i, line in enumerate(lines):
        # HOMO/LUMO情報を含む行を探す
        if '(HOMO)' in line or 'HOMO' in line:
            # パターン例: "   21   -0.285    2.00   (HOMO)"
            match = re.search(r'([-\d.]+)\s+\d+\.\d+\s+\(HOMO\)', line)
            if match:
                homo_energy = float(match.group(1))

        if '(LUMO)' in line or 'LUMO' in line:
            match = re.search(r'([-\d.]+)\s+\d+\.\d+\s+\(LUMO\)', line)
            if match:
                lumo_energy = float(match.group(1))

        # HOMO-LUMO Gapの直接記載を探す
        if 'HOMO-LUMO GAP' in line or 'HL-Gap' in line:
            match = re.search(r'([-\d.]+)\s+eV', line)
            if match:
                gap = float(match.group(1))

    # Gapが見つからない場合は計算
    if gap is None and homo_energy is not None and lumo_energy is not None:
        gap = lumo_energy - homo_energy

    return homo_energy, lumo_energy, gap


def calculate_homo_lumo_xtb(mol, mol_name, xtb_binary):
    """
    単一分子のHOMO/LUMOをxTBで計算

    Parameters:
    -----------
    mol : RDKit molecule object
    mol_name : str
        分子の名前
    xtb_binary : str
        xTBバイナリのパス

    Returns:
    --------
    dict : HOMO, LUMO, GAP の値
    """
    result = {
        'name': mol_name,
        'HOMO': None,
        'LUMO': None,
        'GAP': None,
        'status': 'failed'
    }

    # 一時ディレクトリを作成
    with tempfile.TemporaryDirectory() as tmpdir:
        # XYZ形式で分子を保存
        xyz_file = os.path.join(tmpdir, 'molecule.xyz')

        try:
            # RDKitで3D座標を生成（存在しない場合）
            if mol.GetNumConformers() == 0:
                from rdkit.Chem import AllChem
                AllChem.EmbedMolecule(mol, AllChem.ETKDG())

            # XYZ形式で書き出し
            writer = Chem.rdmolfiles.MolToXYZFile(mol, xyz_file)

        except Exception as e:
            result['status'] = f'3D coordinate generation failed: {str(e)}'
            return result

        # xTB計算を実行
        try:
            cmd = [
                xtb_binary,
                xyz_file,
                '--gfn', '2',  # GFN2-xTB method
                '--norestart'
            ]

            process = subprocess.run(
                cmd,
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=300  # 5分のタイムアウト
            )

            # 出力を解析
            output = process.stdout + process.stderr

            homo, lumo, gap = parse_xtb_output(output)

            if homo is not None:
                result['HOMO'] = homo
                result['LUMO'] = lumo
                result['GAP'] = gap
                result['status'] = 'success'
            else:
                result['status'] = 'calculation failed - could not parse output'

        except subprocess.TimeoutExpired:
            result['status'] = 'timeout'
        except FileNotFoundError:
            result['status'] = f'xTB binary not found: {xtb_binary}'
        except Exception as e:
            result['status'] = f'error: {str(e)}'

    return result


def process_sdf_file(sdf_file, output_file=None):
    """
    SDFファイルから複数分子を読み込み、HOMO/LUMO計算を実行

    Parameters:
    -----------
    sdf_file : str
        入力SDFファイルのパス
    output_file : str, optional
        結果を保存するCSVファイルのパス
    """
    # xTBバイナリを探す
    xtb_binary = find_xtb_binary()
    print(f"Using xTB binary: {xtb_binary}")

    # SDFファイルを読み込み
    supplier = Chem.SDMolSupplier(sdf_file, removeHs=False)

    if supplier is None:
        print(f"Error: Could not read SDF file: {sdf_file}")
        return

    results = []

    print(f"\nProcessing molecules from {sdf_file}...")
    print("-" * 80)

    for idx, mol in enumerate(supplier):
        if mol is None:
            print(f"Molecule {idx + 1}: Failed to read")
            continue

        # 分子名を取得（存在しない場合はインデックスを使用）
        mol_name = mol.GetProp('_Name') if mol.HasProp('_Name') else f"Molecule_{idx + 1}"

        print(f"\nProcessing: {mol_name} ({idx + 1}/{len(supplier)})")

        # HOMO/LUMO計算
        result = calculate_homo_lumo_xtb(mol, mol_name, xtb_binary)
        results.append(result)

        # 結果を表示
        if result['status'] == 'success':
            print(f"  HOMO: {result['HOMO']:.4f} eV")
            print(f"  LUMO: {result['LUMO']:.4f} eV")
            print(f"  GAP:  {result['GAP']:.4f} eV")
        else:
            print(f"  Status: {result['status']}")

    print("\n" + "=" * 80)
    print("Summary of Results:")
    print("=" * 80)
    print(f"{'Molecule':<30} {'HOMO (eV)':<12} {'LUMO (eV)':<12} {'GAP (eV)':<12} {'Status':<15}")
    print("-" * 80)

    for result in results:
        homo_str = f"{result['HOMO']:.4f}" if result['HOMO'] is not None else "N/A"
        lumo_str = f"{result['LUMO']:.4f}" if result['LUMO'] is not None else "N/A"
        gap_str = f"{result['GAP']:.4f}" if result['GAP'] is not None else "N/A"

        print(f"{result['name']:<30} {homo_str:<12} {lumo_str:<12} {gap_str:<12} {result['status']:<15}")

    # CSV出力
    if output_file:
        with open(output_file, 'w') as f:
            f.write("Molecule,HOMO_eV,LUMO_eV,GAP_eV,Status\n")
            for result in results:
                f.write(f"{result['name']},{result['HOMO']},{result['LUMO']},{result['GAP']},{result['status']}\n")
        print(f"\nResults saved to: {output_file}")

    return results


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Calculate HOMO/LUMO energies and gap for molecules in SDF file using xTB'
    )
    parser.add_argument('sdf_file', help='Input SDF file')
    parser.add_argument('-o', '--output', help='Output CSV file', default=None)
    parser.add_argument('--xtb-path', help='Path to xTB binary', default=None)

    args = parser.parse_args()

    # xTBパスを環境変数に設定
    if args.xtb_path:
        os.environ['XTB_PATH'] = args.xtb_path

    # 入力ファイルの存在確認
    if not os.path.isfile(args.sdf_file):
        print(f"Error: File not found: {args.sdf_file}")
        sys.exit(1)

    # 処理を実行
    process_sdf_file(args.sdf_file, args.output)


if __name__ == '__main__':
    main()
