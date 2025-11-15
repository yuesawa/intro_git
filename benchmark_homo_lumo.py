#!/usr/bin/env python3
"""
HOMO/LUMO計算のベンチマークスクリプト
10万分子の計算時間を推算
"""

import time
import os
import sys
import tempfile
import subprocess
from pathlib import Path

# 分子サイズ別の推定計算時間（xTB GFN2-xTBでの経験値）
# 参考: https://xtb-docs.readthedocs.io/en/latest/
MOLECULE_SIZE_TIMES = {
    "small": {  # 原子数 1-20 (メタノール、ベンゼンなど)
        "atoms": 10,
        "time_seconds": 2.0,  # 1-3秒程度
        "examples": "メタノール、ベンゼン、ピリジン"
    },
    "medium": {  # 原子数 20-50 (ナフタレン、アントラセンなど)
        "atoms": 30,
        "time_seconds": 5.0,  # 3-8秒程度
        "examples": "ナフタレン、アントラセン"
    },
    "large": {  # 原子数 50-100
        "atoms": 70,
        "time_seconds": 15.0,  # 10-20秒程度
        "examples": "フラーレンC60など"
    },
    "very_large": {  # 原子数 100-200
        "atoms": 150,
        "time_seconds": 45.0,  # 30-60秒程度
        "examples": "タンパク質フラグメント、大型多環芳香族"
    }
}

# オーバーヘッド時間（分子あたり）
OVERHEAD_PER_MOLECULE = {
    "rdkit_processing": 0.1,  # RDKitでの読み込み・3D座標生成
    "file_io": 0.05,  # XYZファイルの書き込み・読み込み
    "output_parsing": 0.02,  # xTB出力の解析
}


def estimate_single_molecule_time(num_atoms):
    """
    原子数に基づいて単一分子の計算時間を推定

    Parameters:
    -----------
    num_atoms : int
        分子の原子数

    Returns:
    --------
    float : 推定時間（秒）
    """
    # 線形補間で推定
    if num_atoms <= 20:
        base_time = MOLECULE_SIZE_TIMES["small"]["time_seconds"]
    elif num_atoms <= 50:
        base_time = MOLECULE_SIZE_TIMES["medium"]["time_seconds"]
    elif num_atoms <= 100:
        base_time = MOLECULE_SIZE_TIMES["large"]["time_seconds"]
    else:
        base_time = MOLECULE_SIZE_TIMES["very_large"]["time_seconds"]

    # オーバーヘッド時間を追加
    overhead = sum(OVERHEAD_PER_MOLECULE.values())

    return base_time + overhead


def estimate_batch_time(num_molecules, avg_atoms, parallel_cores=1):
    """
    バッチ計算の総時間を推定

    Parameters:
    -----------
    num_molecules : int
        分子数
    avg_atoms : int
        平均原子数
    parallel_cores : int
        並列計算に使用するコア数

    Returns:
    --------
    dict : 推定結果
    """
    single_mol_time = estimate_single_molecule_time(avg_atoms)

    # 逐次処理の場合
    sequential_time = num_molecules * single_mol_time

    # 並列処理の場合（効率85%と仮定）
    parallel_efficiency = 0.85
    parallel_time = (sequential_time / parallel_cores) / parallel_efficiency

    return {
        "num_molecules": num_molecules,
        "avg_atoms": avg_atoms,
        "single_molecule_time": single_mol_time,
        "sequential_time_seconds": sequential_time,
        "sequential_time_hours": sequential_time / 3600,
        "sequential_time_days": sequential_time / 86400,
        "parallel_cores": parallel_cores,
        "parallel_time_seconds": parallel_time,
        "parallel_time_hours": parallel_time / 3600,
        "parallel_time_days": parallel_time / 86400,
        "speedup": sequential_time / parallel_time,
    }


def print_estimation_report(results):
    """推定結果のレポートを表示"""
    print("\n" + "=" * 80)
    print("HOMO/LUMO計算時間の推定")
    print("=" * 80)
    print(f"\n対象分子数: {results['num_molecules']:,}")
    print(f"平均原子数: {results['avg_atoms']}")
    print(f"1分子あたりの計算時間: {results['single_molecule_time']:.2f} 秒")

    print("\n" + "-" * 80)
    print("【逐次処理の場合】（現在のスクリプト）")
    print("-" * 80)
    print(f"総計算時間: {results['sequential_time_seconds']:,.1f} 秒")
    print(f"           = {results['sequential_time_hours']:,.2f} 時間")
    print(f"           = {results['sequential_time_days']:,.2f} 日")

    if results['parallel_cores'] > 1:
        print("\n" + "-" * 80)
        print(f"【並列処理の場合】（{results['parallel_cores']}コア使用、効率85%）")
        print("-" * 80)
        print(f"総計算時間: {results['parallel_time_seconds']:,.1f} 秒")
        print(f"           = {results['parallel_time_hours']:,.2f} 時間")
        print(f"           = {results['parallel_time_days']:,.2f} 日")
        print(f"スピードアップ: {results['speedup']:.1f}x")

    print("\n" + "=" * 80)


def print_detailed_breakdown():
    """計算時間の詳細な内訳を表示"""
    print("\n分子サイズ別の計算時間（参考値）")
    print("-" * 80)
    print(f"{'カテゴリ':<15} {'原子数':<10} {'計算時間':<15} {'例'}")
    print("-" * 80)

    for category, data in MOLECULE_SIZE_TIMES.items():
        category_jp = {
            "small": "小分子",
            "medium": "中分子",
            "large": "大分子",
            "very_large": "超大分子"
        }[category]

        print(f"{category_jp:<15} {data['atoms']:<10} {data['time_seconds']:>6.1f}秒       {data['examples']}")

    print("\n処理オーバーヘッド（分子あたり）")
    print("-" * 80)
    total_overhead = 0
    for process, time_val in OVERHEAD_PER_MOLECULE.items():
        process_jp = {
            "rdkit_processing": "RDKit処理",
            "file_io": "ファイルI/O",
            "output_parsing": "出力解析"
        }.get(process, process)
        print(f"{process_jp:<20} {time_val:.3f}秒")
        total_overhead += time_val
    print(f"{'合計':<20} {total_overhead:.3f}秒")


def main():
    """メイン関数"""
    import argparse

    parser = argparse.ArgumentParser(
        description='HOMO/LUMO計算の時間推定ツール'
    )
    parser.add_argument('-n', '--num-molecules', type=int, default=100000,
                       help='分子数（デフォルト: 100000）')
    parser.add_argument('-a', '--avg-atoms', type=int, default=30,
                       help='平均原子数（デフォルト: 30）')
    parser.add_argument('-c', '--cores', type=int, default=1,
                       help='並列計算のコア数（デフォルト: 1）')
    parser.add_argument('--show-breakdown', action='store_true',
                       help='詳細な内訳を表示')

    args = parser.parse_args()

    # 時間推定を実行
    results = estimate_batch_time(
        num_molecules=args.num_molecules,
        avg_atoms=args.avg_atoms,
        parallel_cores=args.cores
    )

    # レポート表示
    print_estimation_report(results)

    if args.show_breakdown:
        print_detailed_breakdown()

    # 推奨事項を表示
    print("\n推奨事項")
    print("=" * 80)

    if results['sequential_time_hours'] > 24:
        print("⚠️  逐次処理では24時間以上かかります。以下を検討してください：")
        print()
        print("1. 並列処理の実装")
        print("   - multiprocessingを使用してCPUコアを有効活用")
        print("   - 推奨コア数: 8-16コア")
        print()
        print("2. GPUアクセラレーション")
        print("   - xTBはCPU専用ですが、前処理にGPUを活用可能")
        print()
        print("3. 分散計算")
        print("   - 複数マシンで計算を分散")
        print("   - SlurmやPBSなどのジョブスケジューラを使用")
        print()
        print("4. バッチサイズの最適化")
        print("   - チェックポイント機能を実装して中断・再開可能に")
    else:
        print("✅ 計算時間は実用的な範囲です")

    # 並列処理での推定を追加表示
    if args.cores == 1:
        print("\n" + "=" * 80)
        print("参考: 並列処理を使用した場合の推定時間")
        print("=" * 80)

        for cores in [4, 8, 16, 32]:
            parallel_results = estimate_batch_time(
                num_molecules=args.num_molecules,
                avg_atoms=args.avg_atoms,
                parallel_cores=cores
            )
            print(f"{cores:2}コア: {parallel_results['parallel_time_hours']:8.2f} 時間 "
                  f"({parallel_results['parallel_time_days']:6.2f} 日) "
                  f"[{parallel_results['speedup']:.1f}x高速化]")


if __name__ == '__main__':
    main()
