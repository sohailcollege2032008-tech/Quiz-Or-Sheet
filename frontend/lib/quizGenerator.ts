export function generateStandaloneQuiz(questions: any[], fileName: string): string {
  const questionsJSONString = JSON.stringify(questions, null, 4);
  const quizTitle = fileName.replace(/\.[^/.]+$/, "") + " - Quiz";

  return `<!DOCTYPE html>
<html lang="ar" dir="auto">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>${quizTitle}</title>
    <style>
        :root {
            --primary: #2c3e50; --secondary: #34495e; --success: #27ae60;
            --danger: #e74c3c; --light: #f4f7f6; --warning: #f39c12;
        }
        body { font-family: 'Segoe UI', sans-serif; background: var(--light); padding: 20px; display: flex; justify-content: center; }
        .quiz-container { background: white; width: 100%; max-width: 850px; padding: 25px; border-radius: 12px; box-shadow: 0 5px 20px rgba(0,0,0,0.1); }
        h1 { text-align: center; color: var(--primary); border-bottom: 2px solid #eee; padding-bottom: 10px; }
        
        .nav-panel { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 25px; justify-content: center; background: #eee; padding: 15px; border-radius: 8px; direction: ltr; }
        .nav-btn { width: 35px; height: 35px; border: 1px solid #ccc; background: white; cursor: pointer; border-radius: 4px; font-weight: bold; transition: 0.2s; }
        .nav-btn.active { border: 2px solid var(--primary); transform: scale(1.1); }
        .nav-btn.correct { background: var(--success); color: white; border: none; }
        .nav-btn.wrong { background: var(--danger); color: white; border: none; }

        .question-section { min-height: 300px; }
        .question-box { display: none; }
        .question-box.active { display: block; animation: fadeIn 0.3s; }
        @keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }

        .options { display: grid; gap: 12px; margin-top: 20px; }
        .option-btn { padding: 15px; border: 2px solid #e0e0e0; border-radius: 8px; background: white; cursor: pointer; text-align: start; font-size: 16px; transition: 0.2s; }
        .option-btn:hover:not(:disabled) { background: #f9f9f9; border-color: #bbb; }
        .option-btn.selected-correct { background: var(--success) !important; color: white; border-color: #1e8449; }
        .option-btn.selected-wrong { background: var(--danger) !important; color: white; border-color: #a93226; }
        .option-btn.show-correct { border: 2px solid var(--success); background: #e8f6ed; }

        .feedback { margin-top: 15px; padding: 12px; border-radius: 6px; font-weight: bold; display: none; }
        .controls { display: flex; justify-content: space-between; margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; }
        .btn { padding: 10px 25px; border: none; border-radius: 5px; cursor: pointer; font-size: 15px; font-weight: 600; color: white; transition: 0.3s; }
        .btn-nav { background: var(--secondary); }
        .btn-nav:disabled { background: #ccc; cursor: not-allowed; }
        .btn-finish { background: var(--success); display: none; }

        #results-screen { display: none; text-align: center; }
        .score-box { font-size: 48px; margin: 20px 0; color: var(--primary); direction: ltr; }
        .result-filters { display: flex; flex-direction: column; gap: 10px; max-width: 300px; margin: 20px auto; }
    </style>
</head>
<body>

<div class="quiz-container">
    <h1 id="main-title">${quizTitle}</h1>
    
    <div id="quiz-interface">
        <div class="nav-panel" id="nav-panel"></div>
        <div class="question-section" id="questions-container"></div>
        <div class="controls">
            <button class="btn btn-nav" id="next-btn" onclick="move(1)">Next / التالي</button>
            <button class="btn btn-finish" id="finish-btn" onclick="showResults()">Show Final Results / النتيجة</button>
            <button class="btn btn-nav" id="prev-btn" onclick="move(-1)">Previous / السابق</button>
        </div>
    </div>

    <div id="results-screen">
        <h2>Quiz Completed! / اكتمل الاختبار</h2>
        <div class="score-box" id="final-score">0 / 0</div>
        <div class="result-filters">
            <button class="btn" style="background: var(--primary)" onclick="review('all')">Review All / مراجعة الكل</button>
            <button class="btn" style="background: var(--warning)" onclick="review('wrong')">Review Incorrect / مراجعة الأخطاء</button>
            <button class="btn" style="background: #8e44ad" id="retake-wrong-btn" onclick="retakeWrong()">Retake Wrong / إعادة الأخطاء</button>
            <button class="btn" style="background: var(--secondary)" onclick="location.reload()">Restart / إعادة الاختبار</button>
        </div>
    </div>
</div>

<script>
const allQuestions = ${questionsJSONString};
let currentQuestions = [...allQuestions];
let userAnswers = [];
let currentIdx = 0;

function initQuiz() {
    const container = document.getElementById('questions-container');
    const nav = document.getElementById('nav-panel');
    container.innerHTML = '';
    nav.innerHTML = '';
    userAnswers = new Array(currentQuestions.length).fill(null);
    currentIdx = 0;

    currentQuestions.forEach((q, i) => {
        const btn = document.createElement('button');
        btn.className = 'nav-btn';
        btn.id = \\\`nav-\\\${i}\\\`;
        btn.innerText = i + 1;
        btn.onclick = () => jump(i);
        nav.appendChild(btn);

        const box = document.createElement('div');
        box.className = \\\`question-box \\\${i===0?'active':''}\\\`;
        box.id = \\\`q-box-\\\${i}\\\`;
        
        let opts = q.a.map((opt, oi) => \\\`
            <button class="option-btn" id="q-\\\${i}-o-\\\${oi}" onclick="select(\\\${i}, \\\${oi})">\\\${opt}</button>
        \\\`).join('');

        box.innerHTML = \\\`
            <h3>Q \\\${i+1}:</h3>
            <p style="font-size: 18px;">\\\${q.q}</p>
            <div class="options">\\\${opts}</div>
            <div class="feedback" id="feed-\\\${i}"></div>
        \\\`;
        container.appendChild(box);
    });
    updateUI();
}

function select(qIdx, oIdx) {
    if (userAnswers[qIdx] !== null) return;
    userAnswers[qIdx] = oIdx;
    const correct = currentQuestions[qIdx].c;
    const btn = document.getElementById(\\\`q-\\\${qIdx}-o-\\\${oIdx}\\\`);
    const navBtn = document.getElementById(\\\`nav-\\\${qIdx}\\\`);
    const feed = document.getElementById(\\\`feed-\\\${qIdx}\\\`);
    
    feed.style.display = 'block';
    if (oIdx === correct) {
        btn.classList.add('selected-correct');
        navBtn.classList.add('correct');
        feed.innerHTML = "Correct! ✨";
        feed.style.color = "var(--success)";
    } else {
        btn.classList.add('selected-wrong');
        document.getElementById(\\\`q-\\\${qIdx}-o-\\\${correct}\\\`).classList.add('show-correct');
        navBtn.classList.add('wrong');
        feed.innerHTML = "Incorrect.";
        feed.style.color = "var(--danger)";
    }
    if (userAnswers.every(a => a !== null)) document.getElementById('finish-btn').style.display = 'block';
}

function move(step) {
    let target = currentIdx + step;
    if (target >= 0 && target < currentQuestions.length) jump(target);
}

function jump(idx) {
    document.querySelectorAll('.question-box').forEach(b => b.classList.remove('active'));
    document.querySelectorAll('.nav-btn').forEach(b => b.classList.remove('active'));
    document.getElementById(\\\`q-box-\\\${idx}\\\`).classList.add('active');
    document.getElementById(\\\`nav-\\\${idx}\\\`).classList.add('active');
    currentIdx = idx;
    updateUI();
}

function updateUI() {
    document.getElementById('prev-btn').disabled = currentIdx === 0;
    document.getElementById('next-btn').disabled = currentIdx === currentQuestions.length - 1;
}

function showResults() {
    document.getElementById('quiz-interface').style.display = 'none';
    document.getElementById('results-screen').style.display = 'block';
    let score = userAnswers.filter((a, i) => a === currentQuestions[i].c).length;
    document.getElementById('final-score').innerText = \\\`\\\${score} / \\\${currentQuestions.length}\\\`;
    let wrongCount = currentQuestions.length - score;
    document.getElementById('retake-wrong-btn').style.display = wrongCount > 0 ? 'block' : 'none';
}

function review(mode) {
    document.getElementById('results-screen').style.display = 'none';
    document.getElementById('quiz-interface').style.display = 'block';
    document.getElementById('finish-btn').style.display = 'none';
    currentQuestions.forEach((q, i) => {
        const isWrong = userAnswers[i] !== q.c;
        const visible = (mode === 'all' || (mode === 'wrong' && isWrong));
        document.getElementById(\\\`nav-\\\${i}\\\`).style.display = visible ? 'block' : 'none';
    });
    for(let i=0; i<currentQuestions.length; i++) {
        if(document.getElementById(\\\`nav-\\\${i}\\\`).style.display !== 'none') {
            jump(i); break;
        }
    }
}

function retakeWrong() {
    const wrongOnes = currentQuestions.filter((q, i) => userAnswers[i] !== q.c);
    currentQuestions = [...wrongOnes];
    document.getElementById('results-screen').style.display = 'none';
    document.getElementById('quiz-interface').style.display = 'block';
    document.getElementById('main-title').innerText = "Retaking Errors / إعادة الأخطاء";
    initQuiz();
}

initQuiz();
<\\/script>
</body>
</html>`;
}
