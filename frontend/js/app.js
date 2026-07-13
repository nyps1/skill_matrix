// State Management
const State = {
    user: null,
    currentExamSession: null,
    autosaveInterval: null
};

// Utils
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast show';
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

function escapeHtml(unsafe) {
    return (unsafe||'').toString()
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
}

// Router & View Renderer
const App = {
    async init() {
        // Check Auth Status
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const res = await Api.getMe();
                State.user = res.user;
                this.setupHeader();
                this.routeBasedOnRole();
            } catch (e) {
                this.renderLogin();
            }
        } else {
            this.renderLogin();
        }

        // Setup logout
        document.getElementById('logout-btn').addEventListener('click', () => {
            localStorage.removeItem('token');
            State.user = null;
            window.location.reload();
        });
    },

    setupHeader() {
        document.getElementById('main-header').classList.remove('hidden');
        document.getElementById('current-username').textContent = `Hi, ${State.user.username} (${State.user.role})`;
    },

    routeBasedOnRole() {
        if (State.user.role === 'admin') {
            this.renderAdminDashboard();
        } else {
            this.renderEngineerDashboard();
        }
    },

    // --- Views ---

    renderLogin() {
        const main = document.getElementById('main-content');
        document.getElementById('main-header').classList.add('hidden');
        
        main.innerHTML = `
            <div id="login-view" class="glass-panel">
                <h2>Skill Matrix 登入</h2>
                <form id="login-form">
                    <div class="form-group">
                        <label>Username (admin / engineer1)</label>
                        <input type="text" id="username" required>
                    </div>
                    <div class="form-group">
                        <label>Password (password)</label>
                        <input type="password" id="password" required>
                    </div>
                    <button type="submit" class="btn btn-primary" style="width:100%">Login</button>
                </form>
            </div>
        `;

        document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const u = document.getElementById('username').value;
            const p = document.getElementById('password').value;
            try {
                const res = await Api.login(u, p);
                localStorage.setItem('token', res.token);
                State.user = res.user;
                this.setupHeader();
                this.routeBasedOnRole();
                showToast('登入成功');
            } catch (err) {
                showToast('登入失敗: ' + err.message);
            }
        });
    },

    async renderAdminDashboard() {
        const main = document.getElementById('main-content');
        main.innerHTML = `<div class="text-center mt-4">載入中...</div>`;

        try {
            const res = await Api.getAdminDashboard();
            const skillsRes = await Api.getSkills();
            
            let html = `
                <h2>主管總表 (Admin Dashboard)</h2>
                
                <div class="glass-panel" style="padding: 1.5rem; margin-bottom: 2rem;">
                    <h3>新增測驗題目</h3>
                    <div class="form-group">
                        <label>技能分類</label>
                        <select id="new-q-skill">
                            ${skillsRes.map(s => `<option value="${s.id}">${s.name}</option>`).join('')}
                        </select>
                    </div>
                    <div class="form-group">
                        <label>題型</label>
                        <select id="new-q-type">
                            <option value="multiple_choice">選擇題</option>
                            <option value="open_ended">簡答題</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>題目內容</label>
                        <textarea id="new-q-content" rows="3"></textarea>
                    </div>
                    <div class="form-group" id="options-group">
                        <label>選項 (JSON 格式，例如: ["A. 1", "B. 2", "C. 3"])</label>
                        <input type="text" id="new-q-options" placeholder='["A", "B"]'>
                    </div>
                    <div class="form-group">
                        <label>標準答案</label>
                        <input type="text" id="new-q-answer">
                    </div>
                    <button class="btn btn-primary" id="btn-add-q">新增題目</button>
                </div>

                <h3>工程師技能檢測結果</h3>
                <div class="card-grid">
                    ${res.dashboard.map((d, index) => `
                        <div class="card glass-panel">
                            <h4>${escapeHtml(d.user.username)}</h4>
                            <p class="text-secondary">最新總分: ${d.latest_score !== null ? d.latest_score : '無資料'}</p>
                            ${d.skills_radar && d.skills_radar.length > 0 ? `<canvas id="radar-${index}"></canvas>` : '<p>無技能數據</p>'}
                        </div>
                    `).join('')}
                </div>
            `;
            main.innerHTML = html;

            // Render Charts
            res.dashboard.forEach((d, index) => {
                if (d.skills_radar && d.skills_radar.length > 0) {
                    const ctx = document.getElementById(`radar-${index}`).getContext('2d');
                    new Chart(ctx, {
                        type: 'radar',
                        data: {
                            labels: d.skills_radar.map(s => s.skill),
                            datasets: [{
                                label: 'Skill Level',
                                data: d.skills_radar.map(s => s.score),
                                backgroundColor: 'rgba(59, 130, 246, 0.2)',
                                borderColor: 'rgba(59, 130, 246, 1)',
                                pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                            }]
                        },
                        options: {
                            scales: {
                                r: {
                                    min: 0,
                                    max: 10,
                                    grid: { color: 'rgba(255, 255, 255, 0.1)' },
                                    pointLabels: { color: 'rgba(255, 255, 255, 0.7)' },
                                    ticks: { display: false }
                                }
                            },
                            plugins: { legend: { display: false } }
                        }
                    });
                }
            });

            // Add question listener
            document.getElementById('btn-add-q').addEventListener('click', async () => {
                const skill_id = document.getElementById('new-q-skill').value;
                const type = document.getElementById('new-q-type').value;
                const content = document.getElementById('new-q-content').value;
                let optionsText = document.getElementById('new-q-options').value;
                const answer = document.getElementById('new-q-answer').value;

                let options = null;
                if (type === 'multiple_choice') {
                    try { options = JSON.parse(optionsText); } 
                    catch(e) { return showToast('選項 JSON 格式錯誤'); }
                }

                try {
                    await Api.createQuestion({ skill_id, type, content, options, answer });
                    showToast('題目新增成功');
                } catch(e) {
                    showToast('新增失敗: ' + e.message);
                }
            });

        } catch (e) {
            main.innerHTML = `<div class="text-center text-danger">載入失敗: ${e.message}</div>`;
        }
    },

    async renderEngineerDashboard() {
        const main = document.getElementById('main-content');
        main.innerHTML = `
            <h2>工程師測驗專區</h2>
            <div class="glass-panel" style="padding: 2rem; text-align: center; margin-top: 2rem;">
                <p class="mb-4">準備好進行技能檢測了嗎？</p>
                <button id="btn-start-exam" class="btn btn-primary">開始/繼續測驗</button>
            </div>
        `;

        document.getElementById('btn-start-exam').addEventListener('click', async () => {
            try {
                const res = await Api.startExam();
                State.currentExamSession = res.session_id;
                this.renderAssessmentView(res.session_id);
            } catch(e) {
                showToast('無法開始測驗: ' + e.message);
            }
        });
    },

    async renderAssessmentView(sessionId) {
        const main = document.getElementById('main-content');
        main.innerHTML = `<div class="text-center mt-4">載入測驗題目中...</div>`;

        try {
            const questions = await Api.getExamQuestions(sessionId);
            
            let html = `
                <h2>技能檢測進行中</h2>
                <div class="glass-panel" style="padding: 2rem;">
                    <form id="exam-form">
            `;

            questions.forEach((q, idx) => {
                html += `
                    <div class="question-block" data-answer-id="${q.answer_id}">
                        <h4>Q${idx + 1}. [${escapeHtml(q.question.skill_name)}]</h4>
                        <p>${escapeHtml(q.question.content)}</p>
                `;

                if (q.question.type === 'multiple_choice' && q.question.options) {
                    html += `<ul class="options-list">`;
                    q.question.options.forEach((opt, optIdx) => {
                        const isChecked = q.provided_answer === opt ? 'checked' : '';
                        html += `
                            <li>
                                <label>
                                    <input type="radio" name="q_${q.answer_id}" value="${escapeHtml(opt)}" ${isChecked}>
                                    ${escapeHtml(opt)}
                                </label>
                            </li>
                        `;
                    });
                    html += `</ul>`;
                } else {
                    html += `
                        <textarea name="q_${q.answer_id}" rows="4" class="mt-4" placeholder="請在此輸入答案...">${escapeHtml(q.provided_answer || '')}</textarea>
                    `;
                }

                html += `</div>`;
            });

            html += `
                        <div style="display: flex; justify-content: space-between; margin-top: 2rem;">
                            <span id="autosave-status" class="text-secondary"></span>
                            <button type="submit" class="btn btn-primary">提交測驗</button>
                        </div>
                    </form>
                </div>
            `;

            main.innerHTML = html;

            // Start Autosave Loop
            if (State.autosaveInterval) clearInterval(State.autosaveInterval);
            State.autosaveInterval = setInterval(() => this.triggerAutosave(sessionId), 10000); // Save every 10s

            document.getElementById('exam-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.triggerAutosave(sessionId); // final save
                
                if(confirm('確定要提交測驗嗎？提交後無法修改。')) {
                    clearInterval(State.autosaveInterval);
                    try {
                        await Api.submitExam(sessionId);
                        showToast('測驗已提交！');
                        this.renderEngineerDashboard();
                    } catch(err) {
                        showToast('提交失敗: ' + err.message);
                    }
                }
            });

        } catch(e) {
            main.innerHTML = `<div class="text-center text-danger">載入失敗: ${e.message}</div>`;
        }
    },

    async triggerAutosave(sessionId) {
        const blocks = document.querySelectorAll('.question-block');
        const answers = [];

        blocks.forEach(block => {
            const answerId = block.dataset.answerId;
            const textarea = block.querySelector('textarea');
            const checkedRadio = block.querySelector('input[type="radio"]:checked');
            
            let val = null;
            if (textarea) val = textarea.value;
            else if (checkedRadio) val = checkedRadio.value;

            if (val !== null && val !== '') {
                answers.push({
                    answer_id: parseInt(answerId),
                    provided_answer: val
                });
            }
        });

        if (answers.length > 0) {
            try {
                await Api.autosaveExam(sessionId, answers);
                const statusStr = `上次自動儲存: ${new Date().toLocaleTimeString()}`;
                const el = document.getElementById('autosave-status');
                if (el) el.textContent = statusStr;
            } catch(e) {
                console.error('Autosave failed', e);
            }
        }
    }
};

// Start application
document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
