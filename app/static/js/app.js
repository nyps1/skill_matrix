// State Management
const State = {
    user: null,
    currentExamSession: null,
    autosaveInterval: null,
    skillsList: [],
    usersList: [],
    dashboardData: [],
    filterActiveOnly: true // Default to showing only active engineers
};

// Utils
function showToast(message) {
    const toast = document.createElement('div');
    toast.className = 'toast-custom show';
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
        this.injectGlobalModals();

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

        document.getElementById('logout-btn').addEventListener('click', () => {
            localStorage.removeItem('token');
            State.user = null;
            window.location.reload();
        });
    },

    injectGlobalModals() {
        if (document.getElementById('global-modals')) return;
        const html = `
            <div id="global-modals">
                <!-- Change Password Modal (Self) -->
                <div class="modal fade" id="changePwdModal" tabindex="-1">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content border-0 shadow">
                            <div class="modal-header bg-primary text-white">
                                <h5 class="modal-title fw-bold">更改密碼 (Change Password)</h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body p-4">
                                <form id="change-pwd-form">
                                    <div class="mb-3">
                                        <label class="form-label required fw-semibold">新密碼</label>
                                        <input type="password" class="form-control" id="new-self-pwd" required>
                                    </div>
                                    <button type="submit" class="btn btn-primary w-100 mt-2">確認更改</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>

                <!-- Reset Password Modal (Leader Only) -->
                <div class="modal fade" id="resetPwdModal" tabindex="-1">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content border-0 shadow">
                            <div class="modal-header bg-danger text-white">
                                <h5 class="modal-title fw-bold">強制重設密碼 - <span id="reset-pwd-username"></span></h5>
                                <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body p-4">
                                <form id="reset-pwd-form">
                                    <div class="mb-3">
                                        <label class="form-label required fw-semibold">請輸入配發的新密碼</label>
                                        <input type="password" class="form-control" id="new-target-pwd" required>
                                    </div>
                                    <button type="submit" class="btn btn-danger w-100 mt-2">強制重設</button>
                                </form>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
        document.body.insertAdjacentHTML('beforeend', html);

        // Bind Change Password Event
        document.getElementById('change-pwd-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const newPwd = document.getElementById('new-self-pwd').value;
            try {
                await Api.changeMyPassword(newPwd);
                showToast('密碼更改成功！');
                bootstrap.Modal.getInstance(document.getElementById('changePwdModal')).hide();
                document.getElementById('new-self-pwd').value = '';
            } catch(err) {
                showToast('更改失敗: ' + err.message);
            }
        });
    },

    setupHeader() {
        document.getElementById('main-header').classList.remove('hidden');
        document.getElementById('current-username').textContent = `${State.user.username} (${State.user.role.toUpperCase()})`;
        
        // Add Change Password button if not exists
        if (!document.getElementById('change-pwd-btn')) {
            const logoutBtn = document.getElementById('logout-btn');
            logoutBtn.insertAdjacentHTML('beforebegin', `
                <button id="change-pwd-btn" class="btn btn-outline-info btn-sm mt-1 me-2" data-bs-toggle="modal" data-bs-target="#changePwdModal">更改密碼</button>
            `);
        }

        const navLinks = document.getElementById('nav-links');
        
        // Inject Tabs into Navbar for Leader
        if (State.user.role === 'leader') {
            navLinks.innerHTML = `
                <li class="nav-item"><a class="nav-link active cursor-pointer" data-bs-toggle="tab" data-bs-target="#pane-dashboard" role="tab">總覽分析</a></li>
                <li class="nav-item"><a class="nav-link cursor-pointer" data-bs-toggle="tab" data-bs-target="#pane-skills" role="tab">技能管理</a></li>
                <li class="nav-item"><a class="nav-link cursor-pointer" data-bs-toggle="tab" data-bs-target="#pane-users" role="tab">人員與權限</a></li>
                <li class="nav-item"><a class="nav-link cursor-pointer" data-bs-toggle="tab" data-bs-target="#pane-questions" role="tab">題庫管理</a></li>
            `;
            // When tabs change, trigger resize for charts if needed
            document.querySelectorAll('#nav-links [data-bs-toggle="tab"]').forEach(tab => {
                tab.addEventListener('shown.bs.tab', (e) => {
                    // Update active state manually for navbar styling
                    document.querySelectorAll('#nav-links .nav-link').forEach(l => l.classList.remove('active'));
                    e.target.classList.add('active');
                });
            });
        } else {
            navLinks.innerHTML = `
                <li class="nav-item"><a class="nav-link active" href="#" id="nav-exam">Dashboard (Engineer)</a></li>
            `;
            document.getElementById('nav-exam').addEventListener('click', (e) => {
                e.preventDefault();
                this.renderEngineerDashboard();
            });
        }
    },

    routeBasedOnRole() {
        if (State.user.role === 'leader') {
            this.renderAdminDashboard();
        } else {
            this.renderEngineerDashboard();
        }
    },

    // --- Components ---

    getAddQuestionHtml() {
        let availableSkills = State.skillsList;
        if (State.user.role === 'engineer') {
            availableSkills = availableSkills.filter(s => State.user.authorized_skills.includes(s.id));
        }

        return `
            <div class="card shadow-sm border-0">
                <div class="card-header bg-primary text-white">新增測驗題目 (Add Question)</div>
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-md-6">
                            <label class="form-label required">技能(考試)分類</label>
                            <select class="form-select" id="new-q-skill">
                                ${availableSkills.map(s => `<option value="${s.id}">${s.name}</option>`).join('')}
                            </select>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label required">題型</label>
                            <select class="form-select" id="new-q-type">
                                <option value="multiple_choice">選擇題 (Multiple Choice)</option>
                                <option value="open_ended">簡答題 (Open Ended)</option>
                            </select>
                        </div>
                        <div class="col-12">
                            <label class="form-label required">題目內容</label>
                            <textarea class="form-control" id="new-q-content" rows="3"></textarea>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">選項 (僅限選擇題，JSON 格式: ["A", "B"])</label>
                            <input type="text" class="form-control" id="new-q-options" placeholder='["A", "B", "C"]'>
                        </div>
                        <div class="col-md-6">
                            <label class="form-label required">標準答案</label>
                            <input type="text" class="form-control" id="new-q-answer">
                        </div>
                        <div class="col-12 mt-3">
                            <button class="btn btn-primary" id="btn-add-q">新增題目 (Submit)</button>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    bindAddQuestionEvents(onSuccessCallback) {
        const btn = document.getElementById('btn-add-q');
        if(!btn) return;
        btn.addEventListener('click', async () => {
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
                if(onSuccessCallback) onSuccessCallback();
            } catch(e) {
                showToast('新增失敗: ' + e.message);
            }
        });
    },

    renderDashboardCharts() {
        const container = document.getElementById('dashboard-charts-container');
        if (!container) return;

        let filteredData = State.dashboardData;
        if (State.filterActiveOnly) {
            filteredData = filteredData.filter(d => d.user.is_active);
        }

        if (filteredData.length === 0) {
            container.innerHTML = `<div class="col-12 text-center text-muted my-5">無符合條件的工程師資料</div>`;
            return;
        }

        container.innerHTML = filteredData.map((d, index) => `
            <div class="col-md-6 col-lg-4 mb-4">
                <div class="card dashboard-card h-100 shadow-sm border-0">
                    <div class="card-body">
                        <h5 class="card-title text-primary">${escapeHtml(d.user.username)} ${!d.user.is_active ? '<span class="badge bg-danger">已停權</span>' : ''}</h5>
                        <h6 class="card-subtitle mb-3 text-muted">
                            最新總分: <span class="badge ${d.latest_score !== null ? 'bg-success' : 'bg-secondary'}">${d.latest_score !== null ? d.latest_score : '無資料'}</span>
                        </h6>
                        ${d.skills_radar && d.skills_radar.length > 0 ? `<canvas id="radar-${d.user.id}" style="max-height: 250px;"></canvas>` : '<p class="text-muted small text-center mt-4">尚無技能數據</p>'}
                    </div>
                </div>
            </div>
        `).join('');

        // Render Charts
        filteredData.forEach((d) => {
            if (d.skills_radar && d.skills_radar.length > 0) {
                const ctx = document.getElementById(`radar-${d.user.id}`).getContext('2d');
                new Chart(ctx, {
                    type: 'radar',
                    data: {
                        labels: d.skills_radar.map(s => s.skill),
                        datasets: [{
                            label: 'Skill Level',
                            data: d.skills_radar.map(s => s.score),
                            backgroundColor: 'rgba(13, 110, 253, 0.2)',
                            borderColor: 'rgba(13, 110, 253, 1)',
                            pointBackgroundColor: 'rgba(13, 110, 253, 1)'
                        }]
                    },
                    options: { 
                        scales: { r: { min: 0, max: 10, ticks: { display: false } } }, 
                        plugins: { legend: { display: false } },
                        maintainAspectRatio: false
                    }
                });
            }
        });
    },

    // --- Views ---

    renderLogin() {
        const main = document.getElementById('main-content');
        document.getElementById('main-header').classList.add('hidden');
        
        main.innerHTML = `
            <div class="login-wrapper">
                <div class="card login-card shadow border-0">
                    <div class="card-header text-center py-4 bg-white border-0">
                        <h4 class="mb-0 text-primary fw-bold">Skill Matrix</h4>
                        <p class="text-muted mb-0 small mt-1">工程師技能檢測系統</p>
                    </div>
                    <div class="card-body p-4">
                        <form id="login-form">
                            <div class="mb-3">
                                <label class="form-label required fw-semibold">Username</label>
                                <input type="text" class="form-control form-control-lg" id="username" placeholder="leader / engineer1" required>
                            </div>
                            <div class="mb-2">
                                <label class="form-label required fw-semibold">Password</label>
                                <input type="password" class="form-control form-control-lg" id="password" placeholder="password" required>
                            </div>
                            <div class="text-end mb-4">
                                <a href="#" id="forgot-pwd-link" class="text-decoration-none small">Forgot Password?</a>
                            </div>
                            <div class="d-grid gap-2">
                                <button type="submit" class="btn btn-primary btn-lg fw-semibold shadow-sm">登入系統</button>
                            </div>
                        </form>
                    </div>
                </div>
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

        document.getElementById('forgot-pwd-link').addEventListener('click', (e) => {
            e.preventDefault();
            showToast('請聯絡您的主管 (Leader) 進行密碼重置。');
        });
    },

    async renderAdminDashboard() {
        const main = document.getElementById('main-content');
        main.innerHTML = `<div class="text-center mt-5"><div class="spinner-border text-primary" role="status"></div></div>`;

        try {
            const [dashboardRes, usersRes, skillsRes] = await Promise.all([
                Api.getAdminDashboard(),
                Api.getUsers(),
                Api.getSkills()
            ]);
            State.skillsList = skillsRes;
            State.usersList = usersRes;
            State.dashboardData = dashboardRes.dashboard;
            
            // Note: The Tabs headers are now inside setupHeader() nav-links!
            let html = `
                <!-- Tabs Content -->
                <div class="tab-content" id="adminTabsContent">
                    
                    <!-- 1. Dashboard Pane -->
                    <div class="tab-pane fade show active" id="pane-dashboard" role="tabpanel">
                        <div class="d-flex justify-content-between align-items-center mb-4">
                            <h4 class="mb-0 fw-bold">工程師技能量化雷達圖</h4>
                            <div class="form-check form-switch fs-5">
                                <input class="form-check-input" type="checkbox" id="filter-active" ${State.filterActiveOnly ? 'checked' : ''}>
                                <label class="form-check-label fs-6 text-muted ms-1" for="filter-active">隱藏離職/停權工程師</label>
                            </div>
                        </div>
                        <div class="row" id="dashboard-charts-container">
                            <!-- Charts injected here -->
                        </div>
                    </div>

                    <!-- 2. Skills Pane -->
                    <div class="tab-pane fade" id="pane-skills" role="tabpanel">
                        <h4 class="mb-4 fw-bold">技能(考試)管理中心</h4>
                        <div class="card shadow-sm border-0 mb-4">
                            <div class="card-header bg-secondary text-white">建立新考試 / 技能分類</div>
                            <div class="card-body">
                                <form id="add-skill-form" class="row g-3">
                                    <div class="col-md-5">
                                        <input type="text" class="form-control" id="new-s-name" placeholder="技能名稱 (e.g. Python, Frontend)" required>
                                    </div>
                                    <div class="col-md-5">
                                        <input type="text" class="form-control" id="new-s-desc" placeholder="簡單描述 (可選)">
                                    </div>
                                    <div class="col-md-2">
                                        <button type="submit" class="btn btn-secondary w-100">新增技能</button>
                                    </div>
                                </form>
                            </div>
                        </div>
                        
                        <div class="card shadow-sm border-0">
                            <div class="card-header bg-light">現有技能列表</div>
                            <div class="card-body">
                                <div class="d-flex flex-wrap gap-2">
                                    ${skillsRes.map(s => `<span class="badge bg-info text-dark fs-6 px-3 py-2 border border-info-subtle shadow-sm">${escapeHtml(s.name)}</span>`).join('')}
                                    ${skillsRes.length === 0 ? '<p class="text-muted">尚無技能分類</p>' : ''}
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 3. Users & Permissions Pane -->
                    <div class="tab-pane fade" id="pane-users" role="tabpanel">
                        <h4 class="mb-4 fw-bold">人員與權限管理</h4>
                        <div class="card shadow-sm border-0 mb-4">
                            <div class="card-body">
                                <form id="add-user-form" class="row g-3 mb-4 bg-light p-3 rounded mx-0">
                                    <h6 class="mb-1 text-muted">新增工程師帳號</h6>
                                    <div class="col-md-5 mt-2">
                                        <input type="text" class="form-control" id="new-u-name" placeholder="帳號 (Username)" required>
                                    </div>
                                    <div class="col-md-5 mt-2">
                                        <input type="password" class="form-control" id="new-u-pass" placeholder="密碼 (Password)" required>
                                    </div>
                                    <div class="col-md-2 mt-2">
                                        <button type="submit" class="btn btn-success w-100">建立帳號</button>
                                    </div>
                                </form>
                                
                                <div class="table-responsive mt-4">
                                    <table class="table table-hover align-middle border">
                                        <thead class="table-light">
                                            <tr>
                                                <th>ID</th>
                                                <th>Username</th>
                                                <th>狀態 (Status)</th>
                                                <th>操作 (Actions)</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            ${usersRes.map(u => `
                                                <tr>
                                                    <td>${u.id}</td>
                                                    <td class="fw-semibold">${escapeHtml(u.username)}</td>
                                                    <td>
                                                        <div class="form-check form-switch">
                                                            <input class="form-check-input toggle-active" type="checkbox" data-id="${u.id}" ${u.is_active ? 'checked' : ''}>
                                                            <label class="form-check-label ${u.is_active ? 'text-success' : 'text-danger'}">${u.is_active ? 'Active' : 'Inactive'}</label>
                                                        </div>
                                                    </td>
                                                    <td>
                                                        <button class="btn btn-sm btn-outline-primary btn-permissions me-2" data-id="${u.id}">
                                                            設定出題權限 (${u.authorized_skills.length})
                                                        </button>
                                                        <button class="btn btn-sm btn-outline-danger btn-reset-pwd" data-id="${u.id}" data-name="${escapeHtml(u.username)}">
                                                            重設密碼
                                                        </button>
                                                    </td>
                                                </tr>
                                            `).join('')}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- 4. Questions Pane -->
                    <div class="tab-pane fade" id="pane-questions" role="tabpanel">
                        <h4 class="mb-4 fw-bold">題庫管理</h4>
                        ${this.getAddQuestionHtml()}
                    </div>
                </div>

                <!-- Permissions Modal -->
                <div class="modal fade" id="permissionsModal" tabindex="-1">
                    <div class="modal-dialog modal-dialog-centered">
                        <div class="modal-content border-0 shadow">
                            <div class="modal-header bg-light">
                                <h5 class="modal-title fw-bold">設定出題權限 - <span id="perm-username" class="text-primary"></span></h5>
                                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                            </div>
                            <div class="modal-body p-4" id="perm-modal-body">
                                <!-- Checkboxes injected here -->
                            </div>
                            <div class="modal-footer bg-light">
                                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                                <button type="button" class="btn btn-primary px-4" id="btn-save-permissions">儲存設定</button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            main.innerHTML = html;

            // Render Dashboard Charts Initially
            this.renderDashboardCharts();

            // Bind Filter Toggle
            document.getElementById('filter-active').addEventListener('change', (e) => {
                State.filterActiveOnly = e.target.checked;
                this.renderDashboardCharts();
            });

            // Bind Add Skill
            document.getElementById('add-skill-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const name = document.getElementById('new-s-name').value;
                const desc = document.getElementById('new-s-desc').value;
                try {
                    await Api.createSkill({ name, description: desc });
                    showToast('技能新增成功');
                    this.renderAdminDashboard();
                } catch(err) {
                    showToast('新增失敗: ' + err.message);
                }
            });

            // Bind Add User
            document.getElementById('add-user-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const username = document.getElementById('new-u-name').value;
                const password = document.getElementById('new-u-pass').value;
                try {
                    await Api.createUser({ username, password });
                    showToast('人員新增成功');
                    this.renderAdminDashboard();
                } catch(err) {
                    showToast('新增失敗: ' + err.message);
                }
            });

            // Bind Toggle Active
            document.querySelectorAll('.toggle-active').forEach(chk => {
                chk.addEventListener('change', async (e) => {
                    try {
                        await Api.toggleActive(e.target.dataset.id);
                        showToast('狀態更新成功');
                        // Quick re-fetch to update dashboard data
                        const dashboardRes = await Api.getAdminDashboard();
                        State.dashboardData = dashboardRes.dashboard;
                        this.renderDashboardCharts();
                    } catch(err) {
                        e.target.checked = !e.target.checked;
                        showToast('更新失敗');
                    }
                });
            });

            // Bind Reset Password
            let targetResetUserId = null;
            const resetPwdModalEl = document.getElementById('resetPwdModal');
            const resetPwdModal = new bootstrap.Modal(resetPwdModalEl);
            document.querySelectorAll('.btn-reset-pwd').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    targetResetUserId = parseInt(e.currentTarget.dataset.id);
                    document.getElementById('reset-pwd-username').textContent = e.currentTarget.dataset.name;
                    document.getElementById('new-target-pwd').value = '';
                    resetPwdModal.show();
                });
            });

            const resetPwdForm = document.getElementById('reset-pwd-form');
            resetPwdForm.replaceWith(resetPwdForm.cloneNode(true)); // Remove previous listeners
            document.getElementById('reset-pwd-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                const newPwd = document.getElementById('new-target-pwd').value;
                try {
                    await Api.resetUserPassword(targetResetUserId, newPwd);
                    showToast('該員密碼已強制重設成功！');
                    resetPwdModal.hide();
                } catch(err) {
                    showToast('重設失敗: ' + err.message);
                }
            });

            // Bind Permissions Modal
            let currentPermUserId = null;
            const permModalEl = document.getElementById('permissionsModal');
            const permModal = new bootstrap.Modal(permModalEl);
            
            document.querySelectorAll('.btn-permissions').forEach(btn => {
                btn.addEventListener('click', (e) => {
                    currentPermUserId = parseInt(e.currentTarget.dataset.id);
                    const user = State.usersList.find(u => u.id === currentPermUserId);
                    if (!user) return;
                    
                    document.getElementById('perm-username').textContent = user.username;
                    const body = document.getElementById('perm-modal-body');
                    
                    let checkboxes = State.skillsList.map(s => {
                        const isChecked = user.authorized_skills.includes(s.id) ? 'checked' : '';
                        return `
                            <div class="form-check mb-3 p-3 border rounded shadow-sm ${isChecked ? 'bg-primary-subtle border-primary' : 'bg-light'}">
                                <input class="form-check-input perm-chk fs-5 ms-1" type="checkbox" value="${s.id}" id="chk-s-${s.id}" ${isChecked}>
                                <label class="form-check-label fs-5 fw-semibold ms-3" for="chk-s-${s.id}">
                                    ${escapeHtml(s.name)}
                                </label>
                            </div>
                        `;
                    }).join('');
                    
                    if (State.skillsList.length === 0) checkboxes = '<div class="alert alert-warning">目前尚無任何技能(考試)，請先建立。</div>';
                    body.innerHTML = checkboxes;
                    
                    // Add subtle styling change on checkbox toggle
                    body.querySelectorAll('.perm-chk').forEach(cb => {
                        cb.addEventListener('change', (ev) => {
                            const parent = ev.target.closest('.form-check');
                            if(ev.target.checked) {
                                parent.classList.add('bg-primary-subtle', 'border-primary');
                                parent.classList.remove('bg-light');
                            } else {
                                parent.classList.remove('bg-primary-subtle', 'border-primary');
                                parent.classList.add('bg-light');
                            }
                        });
                    });

                    permModal.show();
                });
            });

            document.getElementById('btn-save-permissions').addEventListener('click', async () => {
                const checkedIds = Array.from(document.querySelectorAll('.perm-chk:checked')).map(cb => parseInt(cb.value));
                try {
                    await Api.updatePermissions(currentPermUserId, checkedIds);
                    permModal.hide();
                    showToast('權限更新成功');
                    this.renderAdminDashboard(); // Refresh completely to sync lists
                } catch(err) {
                    showToast('更新失敗: ' + err.message);
                }
            });

            // Bind Add Question form inside Questions Tab
            this.bindAddQuestionEvents(() => {
                document.getElementById('new-q-content').value = '';
                document.getElementById('new-q-options').value = '';
                document.getElementById('new-q-answer').value = '';
            });

        } catch (e) {
            main.innerHTML = `<div class="alert alert-danger">載入失敗: ${e.message}</div>`;
        }
    },

    async renderEngineerDashboard() {
        const main = document.getElementById('main-content');
        main.innerHTML = `<div class="text-center mt-5"><div class="spinner-border text-primary" role="status"></div></div>`;
        
        try {
            const skillsRes = await Api.getSkills();
            State.skillsList = skillsRes;

            let html = `
                <div class="page-header mb-4">
                    <h2>工程師專區 (Engineer Dashboard)</h2>
                </div>
            `;

            if (State.user.authorized_skills && State.user.authorized_skills.length > 0) {
                html += this.getAddQuestionHtml();
            }

            html += `
                <div class="card text-center p-5 mt-4 shadow border-0">
                    <div class="card-body">
                        <h5 class="card-title mb-4 fw-bold fs-3 text-primary">準備好進行技能檢測了嗎？</h5>
                        <p class="card-text text-muted mb-4 fs-5">本測驗具備自動儲存功能，若中斷可隨時回來接續作答。</p>
                        <button id="btn-start-exam" class="btn btn-primary btn-lg px-5 py-3 shadow-sm rounded-pill fw-semibold">🚀 開始 / 繼續測驗</button>
                    </div>
                </div>
            `;

            main.innerHTML = html;

            if (State.user.authorized_skills && State.user.authorized_skills.length > 0) {
                this.bindAddQuestionEvents(() => {
                    document.getElementById('new-q-content').value = '';
                    document.getElementById('new-q-options').value = '';
                    document.getElementById('new-q-answer').value = '';
                });
            }

            document.getElementById('btn-start-exam').addEventListener('click', async () => {
                try {
                    const res = await Api.startExam();
                    State.currentExamSession = res.session_id;
                    this.renderAssessmentView(res.session_id);
                } catch(e) {
                    showToast('無法開始測驗: ' + e.message);
                }
            });
        } catch (e) {
            main.innerHTML = `<div class="alert alert-danger">載入失敗: ${e.message}</div>`;
        }
    },

    async renderAssessmentView(sessionId) {
        const main = document.getElementById('main-content');
        main.innerHTML = `<div class="text-center mt-5"><div class="spinner-border text-primary" role="status"></div></div>`;

        try {
            const questions = await Api.getExamQuestions(sessionId);
            
            let html = `
                <div class="d-flex justify-content-between align-items-center page-header">
                    <h2>技能檢測進行中 (In Progress)</h2>
                    <span id="autosave-status" class="badge bg-light text-dark border">自動儲存系統就緒</span>
                </div>
                
                <form id="exam-form">
            `;

            questions.forEach((q, idx) => {
                html += `
                    <div class="card mb-4 shadow-sm border-0" data-answer-id="${q.answer_id}">
                        <div class="card-header bg-white border-bottom d-flex justify-content-between align-items-center py-3">
                            <span class="fs-5 fw-semibold text-primary">Q${idx + 1}. ${escapeHtml(q.question.skill_name)}</span>
                            <span class="badge bg-info-subtle border border-info-subtle text-info-emphasis px-3 py-2 rounded-pill">${q.question.type === 'multiple_choice' ? '選擇題' : '簡答題'}</span>
                        </div>
                        <div class="card-body p-4">
                            <p class="card-text fs-5 mb-4">${escapeHtml(q.question.content)}</p>
                `;

                if (q.question.type === 'multiple_choice' && q.question.options) {
                    q.question.options.forEach((opt, optIdx) => {
                        const isChecked = q.provided_answer === opt ? 'checked' : '';
                        html += `
                            <div class="form-check mb-3 bg-light p-3 rounded border">
                                <input class="form-check-input fs-5 ms-1 mt-1" type="radio" name="q_${q.answer_id}" id="q_${q.answer_id}_${optIdx}" value="${escapeHtml(opt)}" ${isChecked}>
                                <label class="form-check-label fs-5 ms-3 cursor-pointer w-100" for="q_${q.answer_id}_${optIdx}">
                                    ${escapeHtml(opt)}
                                </label>
                            </div>
                        `;
                    });
                } else {
                    html += `
                        <textarea class="form-control fs-5 p-3" name="q_${q.answer_id}" rows="5" placeholder="請在此輸入答案...">${escapeHtml(q.provided_answer || '')}</textarea>
                    `;
                }

                html += `
                        </div>
                    </div>
                `;
            });

            html += `
                    <div class="text-end mb-5">
                        <button type="submit" class="btn btn-success btn-lg px-5 py-3 rounded-pill fw-semibold shadow-sm">提交測驗 (Submit)</button>
                    </div>
                </form>
            `;

            main.innerHTML = html;

            if (State.autosaveInterval) clearInterval(State.autosaveInterval);
            State.autosaveInterval = setInterval(() => this.triggerAutosave(sessionId), 10000);

            document.getElementById('exam-form').addEventListener('submit', async (e) => {
                e.preventDefault();
                await this.triggerAutosave(sessionId);
                
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
            main.innerHTML = `<div class="alert alert-danger" role="alert">載入失敗: ${e.message}</div>`;
        }
    },

    async triggerAutosave(sessionId) {
        const cards = document.querySelectorAll('.card[data-answer-id]');
        const answers = [];

        cards.forEach(card => {
            const answerId = card.dataset.answerId;
            const textarea = card.querySelector('textarea');
            const checkedRadio = card.querySelector('input[type="radio"]:checked');
            
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
                if (el) {
                    el.textContent = statusStr;
                    el.classList.remove('bg-light', 'text-dark');
                    el.classList.add('bg-success', 'text-white');
                    setTimeout(() => {
                        el.classList.remove('bg-success', 'text-white');
                        el.classList.add('bg-light', 'text-dark');
                    }, 2000);
                }
            } catch(e) {
                console.error('Autosave failed', e);
            }
        }
    }
};

document.addEventListener('DOMContentLoaded', () => {
    App.init();
});
