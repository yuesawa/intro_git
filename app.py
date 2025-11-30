from flask import Flask, render_template, request, jsonify
from rdkit import Chem
from rdkit.Chem import Descriptors, Lipinski
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score, mean_squared_error
import random

app = Flask(__name__)

# Sample training dataset (SMILES, Activity)
TRAINING_DATA = [
    ("CCO", 2.3),  # Ethanol
    ("CC(C)O", 3.1),  # Isopropanol
    ("CCCC", 4.5),  # Butane
    ("c1ccccc1", 5.2),  # Benzene
    ("CC(=O)O", 2.8),  # Acetic acid
    ("CCN", 3.5),  # Ethylamine
    ("c1ccccc1O", 4.9),  # Phenol
    ("CC(C)CC(C)(C)O", 5.8),  # tert-Amyl alcohol
    ("CCOc1ccccc1", 6.2),  # Phenetole
    ("c1ccc2ccccc2c1", 7.1),  # Naphthalene
    ("Cc1ccccc1", 5.9),  # Toluene
    ("CCCCl", 4.2),  # Butyl chloride
    ("c1ccccc1N", 4.7),  # Aniline
    ("CC(C)(C)O", 4.1),  # tert-Butanol
    ("CCCCO", 3.8),  # Butanol
]

def calculate_descriptors(smiles):
    """Calculate molecular descriptors from SMILES"""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None

    descriptors = {
        'MW': Descriptors.MolWt(mol),
        'LogP': Descriptors.MolLogP(mol),
        'HBD': Descriptors.NumHDonors(mol),
        'HBA': Descriptors.NumHAcceptors(mol),
        'TPSA': Descriptors.TPSA(mol),
        'RotBonds': Descriptors.NumRotatableBonds(mol),
        'AromaticRings': Descriptors.NumAromaticRings(mol),
    }
    return descriptors

def get_training_features():
    """Get descriptor matrix for training data"""
    features = []
    activities = []

    for smiles, activity in TRAINING_DATA:
        desc = calculate_descriptors(smiles)
        if desc:
            features.append([desc['MW'], desc['LogP'], desc['HBD'], desc['HBA'],
                           desc['TPSA'], desc['RotBonds'], desc['AromaticRings']])
            activities.append(activity)

    return np.array(features), np.array(activities)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/descriptors', methods=['POST'])
def get_descriptors():
    """Calculate descriptors for a given SMILES"""
    data = request.json
    smiles = data.get('smiles', '')

    descriptors = calculate_descriptors(smiles)
    if descriptors is None:
        return jsonify({'error': 'Invalid SMILES string'}), 400

    return jsonify(descriptors)

@app.route('/api/predict', methods=['POST'])
def predict_activity():
    """Predict activity for a given SMILES using trained model"""
    data = request.json
    smiles = data.get('smiles', '')
    model_type = data.get('model', 'rf')  # 'rf' or 'linear'

    descriptors = calculate_descriptors(smiles)
    if descriptors is None:
        return jsonify({'error': 'Invalid SMILES string'}), 400

    # Train model
    X_train, y_train = get_training_features()

    if model_type == 'rf':
        model = RandomForestRegressor(n_estimators=100, random_state=42)
    else:
        model = LinearRegression()

    model.fit(X_train, y_train)

    # Predict
    X_pred = np.array([[descriptors['MW'], descriptors['LogP'], descriptors['HBD'],
                       descriptors['HBA'], descriptors['TPSA'], descriptors['RotBonds'],
                       descriptors['AromaticRings']]])

    prediction = model.predict(X_pred)[0]

    # Calculate model performance
    y_pred_train = model.predict(X_train)
    r2 = r2_score(y_train, y_pred_train)
    rmse = np.sqrt(mean_squared_error(y_train, y_pred_train))

    return jsonify({
        'prediction': float(prediction),
        'descriptors': descriptors,
        'model_r2': float(r2),
        'model_rmse': float(rmse)
    })

@app.route('/api/training-data', methods=['GET'])
def get_training_data():
    """Get training dataset"""
    data = []
    for smiles, activity in TRAINING_DATA:
        desc = calculate_descriptors(smiles)
        if desc:
            data.append({
                'smiles': smiles,
                'activity': activity,
                'descriptors': desc
            })
    return jsonify(data)

@app.route('/api/quiz', methods=['GET'])
def get_quiz():
    """Get random quiz question about descriptors"""
    quizzes = [
        {
            'question': 'What does LogP represent?',
            'options': [
                'Lipophilicity (oil/water partition)',
                'Molecular weight',
                'Polar surface area',
                'Number of hydrogen bonds'
            ],
            'correct': 0,
            'explanation': 'LogP measures the lipophilicity of a molecule, indicating its preference for oil vs water.'
        },
        {
            'question': 'Which descriptor indicates hydrogen bonding capacity?',
            'options': [
                'Molecular Weight',
                'LogP',
                'HBD (Hydrogen Bond Donors)',
                'Aromatic Rings'
            ],
            'correct': 2,
            'explanation': 'HBD (Hydrogen Bond Donors) and HBA (Acceptors) indicate the hydrogen bonding capacity.'
        },
        {
            'question': 'What does TPSA measure?',
            'options': [
                'Total Polar Surface Area',
                'Total Protein Surface Area',
                'Topological Polar Structure Analysis',
                'Thermodynamic Polarity Scale'
            ],
            'correct': 0,
            'explanation': 'TPSA (Topological Polar Surface Area) is important for predicting drug absorption.'
        },
        {
            'question': 'Higher LogP generally indicates:',
            'options': [
                'Better water solubility',
                'Higher lipophilicity',
                'More hydrogen bonds',
                'Larger molecular size'
            ],
            'correct': 1,
            'explanation': 'Higher LogP values indicate greater lipophilicity and lower water solubility.'
        }
    ]

    return jsonify(random.choice(quizzes))

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
