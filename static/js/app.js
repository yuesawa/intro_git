// Game state
let score = 0;
let totalQuestions = 0;
let currentQuiz = null;

// Mode switching
document.querySelectorAll('.mode-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Update active button
        document.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');

        // Update active mode
        const mode = btn.dataset.mode;
        document.querySelectorAll('.game-mode').forEach(m => m.classList.remove('active'));
        document.getElementById(`${mode}-mode`).classList.add('active');

        // Initialize mode
        if (mode === 'tutorial') {
            loadQuiz();
        } else if (mode === 'data') {
            loadTrainingData();
        }
    });
});

// Tutorial Mode - Quiz
async function loadQuiz() {
    try {
        const response = await fetch('/api/quiz');
        currentQuiz = await response.json();

        document.getElementById('quiz-question').textContent = currentQuiz.question;

        const optionsContainer = document.getElementById('quiz-options');
        optionsContainer.innerHTML = '';

        currentQuiz.options.forEach((option, index) => {
            const btn = document.createElement('button');
            btn.className = 'option-btn';
            btn.textContent = option;
            btn.addEventListener('click', () => checkAnswer(index));
            optionsContainer.appendChild(btn);
        });

        document.getElementById('quiz-explanation').classList.add('hidden');
        document.getElementById('next-quiz-btn').classList.add('hidden');
    } catch (error) {
        console.error('Error loading quiz:', error);
    }
}

function checkAnswer(selectedIndex) {
    totalQuestions++;

    const optionBtns = document.querySelectorAll('.option-btn');
    optionBtns.forEach((btn, index) => {
        btn.disabled = true;
        if (index === currentQuiz.correct) {
            btn.classList.add('correct');
        } else if (index === selectedIndex) {
            btn.classList.add('incorrect');
        }
    });

    if (selectedIndex === currentQuiz.correct) {
        score++;
    }

    document.getElementById('score').textContent = score;
    document.getElementById('total').textContent = totalQuestions;

    const explanationDiv = document.getElementById('quiz-explanation');
    explanationDiv.textContent = currentQuiz.explanation;
    explanationDiv.classList.remove('hidden');

    document.getElementById('next-quiz-btn').classList.remove('hidden');
}

document.getElementById('next-quiz-btn').addEventListener('click', loadQuiz);

// Model Building Mode
document.getElementById('predict-btn').addEventListener('click', async () => {
    const smiles = document.getElementById('smiles-input').value.trim();
    if (!smiles) {
        alert('SMILES式を入力してください');
        return;
    }

    const modelType = document.querySelector('input[name="model-type"]:checked').value;

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ smiles, model: modelType })
        });

        if (!response.ok) {
            const error = await response.json();
            alert(error.error || '予測に失敗しました');
            return;
        }

        const data = await response.json();

        document.getElementById('pred-activity').textContent = data.prediction.toFixed(2);
        document.getElementById('model-r2').textContent = data.model_r2.toFixed(3);
        document.getElementById('model-rmse').textContent = data.model_rmse.toFixed(3);

        const descriptorTable = document.getElementById('descriptor-table');
        descriptorTable.innerHTML = '';

        for (const [key, value] of Object.entries(data.descriptors)) {
            const item = document.createElement('div');
            item.className = 'descriptor-item';
            item.innerHTML = `
                <div class="desc-label">${key}</div>
                <div class="desc-value">${value.toFixed(2)}</div>
            `;
            descriptorTable.appendChild(item);
        }

        document.getElementById('prediction-results').classList.remove('hidden');
    } catch (error) {
        console.error('Error predicting:', error);
        alert('予測に失敗しました');
    }
});

// Molecular Design Challenge Mode
const TARGET_ACTIVITY = 6.5;
const TARGET_TOLERANCE = 0.5;
const MW_MIN = 100;
const MW_MAX = 250;
const LOGP_MIN = 1.0;
const LOGP_MAX = 5.0;
const HBD_MAX = 3;

document.getElementById('check-design-btn').addEventListener('click', async () => {
    const smiles = document.getElementById('design-smiles-input').value.trim();
    if (!smiles) {
        alert('SMILES式を入力してください');
        return;
    }

    try {
        const response = await fetch('/api/predict', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ smiles, model: 'rf' })
        });

        if (!response.ok) {
            const error = await response.json();
            alert(error.error || '評価に失敗しました');
            return;
        }

        const data = await response.json();
        const desc = data.descriptors;
        const activity = data.prediction;

        // Check constraints
        const activityOk = Math.abs(activity - TARGET_ACTIVITY) <= TARGET_TOLERANCE;
        const mwOk = desc.MW >= MW_MIN && desc.MW <= MW_MAX;
        const logpOk = desc.LogP >= LOGP_MIN && desc.LogP <= LOGP_MAX;
        const hbdOk = desc.HBD <= HBD_MAX;

        const allOk = activityOk && mwOk && logpOk && hbdOk;

        // Display results
        document.getElementById('design-activity').textContent = activity.toFixed(2);
        document.getElementById('design-mw').textContent = desc.MW.toFixed(2);
        document.getElementById('design-logp').textContent = desc.LogP.toFixed(2);
        document.getElementById('design-hbd').textContent = desc.HBD;

        document.getElementById('activity-status').textContent = activityOk ? '✓' : '✗';
        document.getElementById('mw-status').textContent = mwOk ? '✓' : '✗';
        document.getElementById('logp-status').textContent = logpOk ? '✓' : '✗';
        document.getElementById('hbd-status').textContent = hbdOk ? '✓' : '✗';

        const statusMessage = document.getElementById('design-status');
        if (allOk) {
            statusMessage.textContent = 'すべての条件をクリアしました！';
            statusMessage.className = 'status-message success';
            document.getElementById('success-message').classList.remove('hidden');
        } else {
            const failedCount = [activityOk, mwOk, logpOk, hbdOk].filter(x => !x).length;
            statusMessage.textContent = `${4 - failedCount}/4 条件を満たしています。もう少しです！`;
            statusMessage.className = 'status-message partial';
            document.getElementById('success-message').classList.add('hidden');
        }

        document.getElementById('design-results').classList.remove('hidden');
    } catch (error) {
        console.error('Error checking design:', error);
        alert('評価に失敗しました');
    }
});

document.getElementById('new-challenge-btn').addEventListener('click', () => {
    document.getElementById('design-smiles-input').value = '';
    document.getElementById('design-results').classList.add('hidden');
    document.getElementById('success-message').classList.add('hidden');
});

// Training Data View
async function loadTrainingData() {
    try {
        const response = await fetch('/api/training-data');
        const data = await response.json();

        const tbody = document.getElementById('data-table-body');
        tbody.innerHTML = '';

        data.forEach(item => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${item.smiles}</td>
                <td>${item.activity.toFixed(2)}</td>
                <td>${item.descriptors.MW.toFixed(2)}</td>
                <td>${item.descriptors.LogP.toFixed(2)}</td>
                <td>${item.descriptors.HBD}</td>
                <td>${item.descriptors.HBA}</td>
                <td>${item.descriptors.TPSA.toFixed(2)}</td>
            `;
            tbody.appendChild(row);
        });
    } catch (error) {
        console.error('Error loading training data:', error);
    }
}

// Initialize
loadQuiz();
