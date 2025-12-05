#!/usr/bin/env python3
"""
サンプル分子のSDFファイルを生成するスクリプト
"""

from rdkit import Chem
from rdkit.Chem import AllChem


def create_sample_molecules():
    """複数のサンプル分子を作成"""

    # SMILESから分子を作成
    molecules = [
        ("Benzene", "c1ccccc1"),
        ("Naphthalene", "c1ccc2ccccc2c1"),
        ("Anthracene", "c1ccc2cc3ccccc3cc2c1"),
        ("Pyridine", "c1ccncc1"),
        ("Furan", "c1ccoc1"),
        ("Thiophene", "c1ccsc1"),
        ("Methanol", "CO"),
        ("Ethanol", "CCO"),
        ("Acetone", "CC(=O)C"),
        ("Benzonitrile", "N#Cc1ccccc1"),
    ]

    mol_list = []

    for name, smiles in molecules:
        mol = Chem.MolFromSmiles(smiles)
        if mol is not None:
            # 水素原子を追加
            mol = Chem.AddHs(mol)

            # 3D座標を生成
            AllChem.EmbedMolecule(mol, AllChem.ETKDG())

            # 構造最適化
            AllChem.UFFOptimizeMolecule(mol)

            # 分子名を設定
            mol.SetProp('_Name', name)

            mol_list.append(mol)
            print(f"Created: {name}")

    return mol_list


def save_to_sdf(mol_list, filename):
    """分子リストをSDFファイルに保存"""
    writer = Chem.SDWriter(filename)

    for mol in mol_list:
        writer.write(mol)

    writer.close()
    print(f"\nSaved {len(mol_list)} molecules to {filename}")


if __name__ == '__main__':
    print("Creating sample molecules...")
    molecules = create_sample_molecules()

    print("\nSaving to SDF file...")
    save_to_sdf(molecules, 'sample_molecules.sdf')

    print("\nDone!")
