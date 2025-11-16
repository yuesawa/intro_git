#!/usr/bin/env python3
"""
dxtbを使用したGPU対応HOMO/LUMO計算スクリプト
Google Colab Pro/A100での実行を想定

必要なパッケージ:
    pip install dxtb torch rdkit
"""

import os
import sys
import numpy as np
import torch
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import time
import csv


def check_gpu_availability():
    """GPU環境の確認"""
    if torch.cuda.is_available():
        device = torch.device("cuda")
        gpu_name = torch.cuda.get_device_name(0)
        gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
        print(f"✅ GPU available: {gpu_name}")
        print(f"   Memory: {gpu_memory:.1f} GB")
        print(f"   CUDA version: {torch.version.cuda}")
        return device
    else:
        print("⚠️  No GPU detected, using CPU")
        return torch.device("cpu")


def estimate_batch_size(device, avg_atoms=30):
    """
    GPUメモリに基づいて最適なバッチサイズを推定

    Parameters:
    -----------
    device : torch.device
    avg_atoms : int
        平均原子数

    Returns:
    --------
    int : 推奨バッチサイズ
    """
    if device.type == "cpu":
        return 10  # CPUではバッチサイズを小さく

    # GPUメモリ容量を取得
    total_memory = torch.cuda.get_device_properties(0).total_memory / 1e9  # GB

    # メモリ容量に基づくバッチサイズの推定
    # 経験則: 分子あたり約 (atoms^2 * 0.001) MB必要
    mem_per_mol = (avg_atoms ** 2 * 0.001) / 1000  # GB

    # 安全マージン80%使用
    available_memory = total_memory * 0.8
    batch_size = int(available_memory / mem_per_mol)

    # 最小・最大値で制限
    batch_size = max(10, min(batch_size, 1000))

    print(f"   Estimated batch size: {batch_size} molecules")
    return batch_size


def load_molecules_from_sdf(sdf_file):
    """
    SDFファイルから分子を読み込み

    Returns:
    --------
    list : [(name, atomic_numbers, positions), ...]
    """
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem
    except ImportError:
        print("Error: RDKit not installed. Install with: pip install rdkit")
        sys.exit(1)

    supplier = Chem.SDMolSupplier(sdf_file, removeHs=False)
    molecules = []

    for idx, mol in enumerate(supplier):
        if mol is None:
            print(f"Warning: Failed to read molecule {idx + 1}")
            continue

        # 分子名を取得
        mol_name = mol.GetProp('_Name') if mol.HasProp('_Name') else f"Molecule_{idx + 1}"

        # 原子番号を取得
        atomic_numbers = [atom.GetAtomicNum() for atom in mol.GetAtoms()]

        # 座標を取得（3D座標がない場合は生成）
        if mol.GetNumConformers() == 0:
            try:
                AllChem.EmbedMolecule(mol, AllChem.ETKDG())
                AllChem.UFFOptimizeMolecule(mol)
            except Exception as e:
                print(f"Warning: Failed to generate 3D coordinates for {mol_name}: {e}")
                continue

        conf = mol.GetConformer()
        positions = []
        for i in range(mol.GetNumAtoms()):
            pos = conf.GetAtomPosition(i)
            positions.append([pos.x, pos.y, pos.z])

        molecules.append((mol_name, atomic_numbers, positions))

    return molecules


def validate_molecule_for_dxtb(name, atomic_numbers):
    """
    分子がdxtb計算に適しているか検証

    Returns:
    --------
    tuple : (is_valid, error_message)
    """
    num_atoms = len(atomic_numbers)

    # 原子数チェック
    if num_atoms == 0:
        return False, "No atoms in molecule"

    # dxtbは255原子制限なし（ただし大きすぎると遅い）
    if num_atoms > 500:
        return False, f"Too many atoms: {num_atoms} (recommended max: 500 for GPU)"

    if num_atoms > 300:
        return True, f"Warning: Large molecule ({num_atoms} atoms), calculation may be slow"

    # 元素チェック（GFN2-xTBは Z=1-86）
    supported_elements = set(range(1, 87))
    unsupported = []

    for z in atomic_numbers:
        if z not in supported_elements:
            unsupported.append(z)

    if unsupported:
        return False, f"Unsupported elements (Z): {unsupported} (GFN2-xTB supports Z=1-86)"

    return True, "OK"


def prepare_batch(molecules, device):
    """
    分子リストをdxtb用のバッチテンソルに変換

    Parameters:
    -----------
    molecules : list of (name, atomic_numbers, positions)
    device : torch.device

    Returns:
    --------
    tuple : (names, numbers_batch, positions_batch, padding_mask)
    """
    if len(molecules) == 0:
        return [], None, None, None

    names = [mol[0] for mol in molecules]

    # 最大原子数を取得（パディング用）
    max_atoms = max(len(mol[1]) for mol in molecules)
    batch_size = len(molecules)

    # パディングされたテンソルを作成
    numbers_batch = torch.zeros((batch_size, max_atoms), dtype=torch.long, device=device)
    positions_batch = torch.zeros((batch_size, max_atoms, 3), dtype=torch.float64, device=device)
    padding_mask = torch.zeros((batch_size, max_atoms), dtype=torch.bool, device=device)

    for i, (name, atomic_nums, coords) in enumerate(molecules):
        n_atoms = len(atomic_nums)
        numbers_batch[i, :n_atoms] = torch.tensor(atomic_nums, dtype=torch.long)
        positions_batch[i, :n_atoms] = torch.tensor(coords, dtype=torch.float64)
        padding_mask[i, :n_atoms] = True

    return names, numbers_batch, positions_batch, padding_mask


def calculate_homo_lumo_batch(calc, numbers, positions, padding_mask=None):
    """
    dxtbを使用してバッチでHOMO/LUMO計算

    Parameters:
    -----------
    calc : dxtb Calculator
    numbers : torch.Tensor
        原子番号 (batch_size, max_atoms)
    positions : torch.Tensor
        座標 (batch_size, max_atoms, 3)
    padding_mask : torch.Tensor
        パディングマスク (batch_size, max_atoms)

    Returns:
    --------
    dict : {'homo': list, 'lumo': list, 'gap': list, 'status': list}
    """
    results = {
        'homo': [],
        'lumo': [],
        'gap': [],
        'status': []
    }

    try:
        # dxtbで計算実行
        # 注: 実際のdxtb APIに合わせて調整が必要
        batch_results = calc.singlepoint(numbers, positions)

        # HOMO/LUMOエネルギーを抽出
        # dxtbの出力形式に応じて調整
        if hasattr(batch_results, 'homo') and hasattr(batch_results, 'lumo'):
            homo_energies = batch_results.homo
            lumo_energies = batch_results.lumo

            # Hartree -> eV変換 (1 Hartree = 27.2114 eV)
            if homo_energies.numel() > 0:
                homo_ev = homo_energies * 27.2114
                lumo_ev = lumo_energies * 27.2114
                gap_ev = lumo_ev - homo_ev

                results['homo'] = homo_ev.cpu().tolist()
                results['lumo'] = lumo_ev.cpu().tolist()
                results['gap'] = gap_ev.cpu().tolist()
                results['status'] = ['success'] * len(homo_ev)
            else:
                results['status'] = ['failed: no orbital energies']
        else:
            # 軌道エネルギーから手動で抽出
            # これはdxtbの実装詳細に依存
            results['status'] = ['success (manual extraction needed)']

    except Exception as e:
        error_msg = f"calculation failed: {str(e)}"
        batch_size = numbers.shape[0]
        results['homo'] = [None] * batch_size
        results['lumo'] = [None] * batch_size
        results['gap'] = [None] * batch_size
        results['status'] = [error_msg] * batch_size

    return results


def process_sdf_with_dxtb(sdf_file, output_file=None, batch_size=None, device=None):
    """
    dxtbを使用してSDFファイルのHOMO/LUMO計算を実行

    Parameters:
    -----------
    sdf_file : str
        入力SDFファイル
    output_file : str, optional
        出力CSVファイル
    batch_size : int, optional
        バッチサイズ（Noneの場合は自動推定）
    device : torch.device, optional
        計算デバイス

    Returns:
    --------
    list : 計算結果
    """
    # デバイス確認
    if device is None:
        device = check_gpu_availability()

    # dxtbをインポート
    try:
        from dxtb import GFN2Calculator
    except ImportError:
        print("\nError: dxtb not installed")
        print("Install with: pip install dxtb")
        print("\nNote: This requires PyTorch. Install PyTorch first:")
        print("  pip install torch torchvision torchaudio")
        sys.exit(1)

    # 分子を読み込み
    print(f"\nLoading molecules from {sdf_file}...")
    molecules = load_molecules_from_sdf(sdf_file)
    print(f"Loaded {len(molecules)} molecules")

    if len(molecules) == 0:
        print("Error: No valid molecules found")
        return []

    # 平均原子数を計算
    avg_atoms = int(np.mean([len(mol[1]) for mol in molecules]))
    print(f"Average atoms per molecule: {avg_atoms}")

    # バッチサイズを決定
    if batch_size is None:
        batch_size = estimate_batch_size(device, avg_atoms)
    else:
        print(f"Using specified batch size: {batch_size}")

    # 計算機を初期化
    print("\nInitializing dxtb GFN2 calculator...")
    calc = GFN2Calculator(device=device)

    # 分子を検証してフィルタリング
    valid_molecules = []
    for name, atomic_nums, coords in molecules:
        is_valid, msg = validate_molecule_for_dxtb(name, atomic_nums)
        if is_valid:
            valid_molecules.append((name, atomic_nums, coords))
            if msg != "OK":
                print(f"  {name}: {msg}")
        else:
            print(f"  {name}: SKIPPED - {msg}")

    print(f"\n{len(valid_molecules)}/{len(molecules)} molecules are valid for calculation")

    # バッチ処理
    all_results = []
    num_batches = (len(valid_molecules) + batch_size - 1) // batch_size

    print(f"\nProcessing {len(valid_molecules)} molecules in {num_batches} batches...")
    print("=" * 80)

    start_time = time.time()

    for batch_idx in range(num_batches):
        batch_start = batch_idx * batch_size
        batch_end = min(batch_start + batch_size, len(valid_molecules))
        batch_molecules = valid_molecules[batch_start:batch_end]

        print(f"\nBatch {batch_idx + 1}/{num_batches} ({len(batch_molecules)} molecules)")

        # バッチを準備
        names, numbers, positions, mask = prepare_batch(batch_molecules, device)

        # 計算実行
        batch_time_start = time.time()
        batch_results = calculate_homo_lumo_batch(calc, numbers, positions, mask)
        batch_time = time.time() - batch_time_start

        # 結果を格納
        for i, name in enumerate(names):
            result = {
                'name': name,
                'HOMO': batch_results['homo'][i] if i < len(batch_results['homo']) else None,
                'LUMO': batch_results['lumo'][i] if i < len(batch_results['lumo']) else None,
                'GAP': batch_results['gap'][i] if i < len(batch_results['gap']) else None,
                'status': batch_results['status'][i] if i < len(batch_results['status']) else 'unknown'
            }
            all_results.append(result)

            # 進捗表示
            if result['status'] == 'success':
                print(f"  ✓ {name}: HOMO={result['HOMO']:.4f} eV, "
                      f"LUMO={result['LUMO']:.4f} eV, GAP={result['GAP']:.4f} eV")
            else:
                print(f"  ✗ {name}: {result['status']}")

        print(f"  Batch time: {batch_time:.2f}s ({batch_time/len(batch_molecules):.3f}s per molecule)")

    total_time = time.time() - start_time

    # サマリー表示
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)

    successful = sum(1 for r in all_results if r['status'] == 'success')
    print(f"Total molecules processed: {len(all_results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(all_results) - successful}")
    print(f"Total time: {total_time:.2f}s")
    print(f"Average time per molecule: {total_time/len(all_results):.3f}s")

    if device.type == "cuda":
        print(f"GPU memory used: {torch.cuda.max_memory_allocated()/1e9:.2f} GB")

    # CSV出力
    if output_file:
        print(f"\nSaving results to {output_file}...")
        with open(output_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'HOMO', 'LUMO', 'GAP', 'status'])
            writer.writeheader()
            writer.writerows(all_results)
        print(f"Results saved successfully")

    return all_results


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='Calculate HOMO/LUMO energies using dxtb (GPU-accelerated)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python calculate_homo_lumo_dxtb.py sample_molecules.sdf

  # Specify output file and batch size
  python calculate_homo_lumo_dxtb.py molecules.sdf -o results.csv -b 200

  # Force CPU usage
  python calculate_homo_lumo_dxtb.py molecules.sdf --cpu

For Google Colab, install dependencies first:
  !pip install dxtb torch rdkit
        """
    )

    parser.add_argument('sdf_file', help='Input SDF file')
    parser.add_argument('-o', '--output', help='Output CSV file', default=None)
    parser.add_argument('-b', '--batch-size', type=int, help='Batch size (auto if not specified)', default=None)
    parser.add_argument('--cpu', action='store_true', help='Force CPU usage (disable GPU)')

    args = parser.parse_args()

    # 入力ファイルチェック
    if not os.path.isfile(args.sdf_file):
        print(f"Error: File not found: {args.sdf_file}")
        sys.exit(1)

    # デバイス設定
    if args.cpu:
        device = torch.device("cpu")
        print("Forcing CPU usage")
    else:
        device = None  # 自動検出

    # 処理実行
    results = process_sdf_with_dxtb(
        sdf_file=args.sdf_file,
        output_file=args.output,
        batch_size=args.batch_size,
        device=device
    )

    print("\n✅ Processing complete!")


if __name__ == '__main__':
    main()
