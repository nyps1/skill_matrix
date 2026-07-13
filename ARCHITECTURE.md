# 系統架構與元件說明 (System Architecture & Components)

本專案 (Skill Matrix) 採用**前後端分離 (Frontend-Backend Separation)** 的設計模式。後端由 Python Flask 提供 RESTful API 服務，前端則以 Vanilla HTML/CSS/JavaScript 建構單頁應用程式 (SPA)。以下針對各個系統模組與檔案進行深入的技術拆解。

## 1. 核心技術棧 (Technology Stack)

*   **後端框架**：Flask 3.x (輕量級 API 伺服器)
*   **資料儲存**：SQLite3 (輕量級關聯式資料庫) + SQLAlchemy (ORM)
*   **身分驗證**：JSON Web Token (JWT) + Bcrypt 密碼雜湊
*   **前端渲染**：原生 HTML5 + Vanilla JS (動態 DOM 操作)
*   **樣式設計**：Vanilla CSS3 (實作 CSS Variables, Glassmorphism, Dark Mode)
*   **資料視覺化**：Chart.js (雷達圖渲染)

## 2. 專案目錄結構 (Directory Structure)

```text
engineer_skill_assessment/
├── backend/                  # 後端核心邏輯
│   ├── app.py                # 應用程式進入點與初始化
│   ├── models.py             # 資料庫 Schema 與 ORM 模型
│   ├── routes/               # RESTful API 路由層
│   │   ├── admin.py          # 主管/管理員專屬邏輯
│   │   ├── assessment.py     # 測驗進行與狀態儲存邏輯
│   │   └── auth.py           # 登入與授權邏輯
│   └── utils/                # 輔助工具層
│       └── auth_middleware.py# JWT 攔截器與權限驗證裝飾器
├── frontend/                 # 前端使用者介面
│   ├── index.html            # 唯一 HTML 進入點 (SPA 掛載點)
│   ├── css/
│   │   └── style.css         # 系統全域樣式與 Design System
│   └── js/
│       ├── api.js            # Fetch API 封裝層
│       └── app.js            # 前端狀態機、路由與 DOM 渲染邏輯
├── DEPENDENCIES.md           # 環境依賴與套件清單
├── requirements.txt          # Python pip 依賴清單
└── .gitignore                # Git 忽略檔案設定
```

## 3. 後端模組深度解析 (Backend Components)

### 3.1 `backend/app.py`
*   **職責**：Flask 應用程式的初始化工廠 (Application Factory)。
*   **運作機制**：負責註冊所有的 Blueprints (路由模組)、設定 CORS (跨來源資源共用) 標頭、綁定 SQLAlchemy 實例，並處理全域錯誤 (Error Handlers)。
*   **防錯機制**：在啟動時自動檢查資料庫結構，若為空則執行 Seeding，建立預設的 `admin` 與 `engineer1` 帳號，避免系統初始無法登入。

### 3.2 `backend/models.py`
*   **職責**：定義關聯式資料庫 (SQLite) 的實體關聯模型 (Entity-Relationship Model)。
*   **核心 Table**：
    *   `User`: 管理使用者帳號、密碼雜湊值 (`password_hash`) 與角色 (`role`)。
    *   `SkillCategory`: 定義技能圖譜的基礎節點。
    *   `Question`: 題庫，透過 Foreign Key 關聯至特定的 `SkillCategory`。包含 JSON 序列化的選項欄位 (`options`)。
    *   `ExamSession`: 測驗狀態機的核心。追蹤測驗狀態 (`draft`, `submitted`, `graded`)，支援非同步儲存與中斷恢復。
    *   `ExamAnswer`: 紀錄使用者提交的答案與該題得分，並透過關聯聯動 `ExamSession`。

### 3.3 `backend/utils/auth_middleware.py`
*   **職責**：請求攔截 (Request Interception) 與授權檢查。
*   **運作機制**：實作 `@token_required` 與 `@admin_required`。透過解析 HTTP Header 中的 `Authorization: Bearer <Token>`，利用 `PyJWT` 驗證簽章有效性，並將解析出的使用者物件注入後續函式，有效防止越權存取。

### 3.4 `backend/routes/*.py` (API 控制器)
*   **`auth.py`**：處理 `/api/auth/login`。負責比對 Bcrypt Hash，驗證成功後簽發包含 `user_id` 與過期時間的 JWT Token。
*   **`admin.py`**：主管層級控制器。負責提供 `/api/admin/dashboard` 的資料聚合 (Data Aggregation)，計算各技能的平均得分以供前端繪製雷達圖；同時處理題庫的 CRUD 操作。
*   **`assessment.py`**：工程師測驗控制器。設計了完整的測驗防錯生命週期：
    1.  建立 `draft` 狀態的 Session (`/exams/start`)。
    2.  接收前端定期打過來的 `/autosave` 請求，更新對應的 `ExamAnswer`。
    3.  接收 `/submit` 請求，將狀態鎖定為 `submitted`，並對 `multiple_choice` 題型進行自動化比對與評分。

## 4. 前端模組深度解析 (Frontend Components)

### 4.1 `frontend/index.html`
*   **職責**：SPA (Single Page Application) 的基礎骨架。
*   **運作機制**：僅提供 `<header>` 導覽列與 `<main id="main-content">` 掛載點。所有的互動介面皆由 JavaScript 動態生成並注入至掛載點中。

### 4.2 `frontend/js/api.js`
*   **職責**：Client-side 的資料存取層 (Data Access Layer)。
*   **運作機制**：利用原生 `fetch` API 封裝所有的 HTTP 請求。集中管理 `API_BASE`，並自動在每個 Request 的 Headers 中注入 `localStorage` 內的 JWT Token。若收到 `401 Unauthorized` 狀態碼，會自動清除 Token 並強制重新載入頁面，阻斷無效請求。

### 4.3 `frontend/js/app.js`
*   **職責**：前端的核心狀態機 (State Machine) 與畫面渲染器 (View Renderer)。
*   **運作機制**：
    *   **路由機制**：依據 `State.user.role` 動態呼叫 `renderAdminDashboard()` 或 `renderEngineerDashboard()`，切換 DOM 內容。
    *   **Autosave 迴圈**：當進入測驗畫面 (`renderAssessmentView`) 時，啟動 `setInterval`，每 10 秒將使用者在表單填寫的資料搜集並非同步推送至後端。
    *   **記憶體管理防護**：在提交測驗或切換畫面時，會呼叫 `clearInterval` 銷毀 Autosave 計時器，防止 Memory Leak (記憶體洩漏)。

### 4.4 `frontend/css/style.css`
*   **職責**：全域樣式與視覺設計系統 (Design System)。
*   **設計風格**：採用 CSS 變數 (CSS Variables) 定義一致的色票 (`--bg-base`, `--accent-primary`)。大量使用 `backdrop-filter` 實作 Glassmorphism 視覺特效，確保在 Dark Mode 下維持高質感的層次。

## 5. 系統運作時序範例 (Data Flow Example)

以「工程師進行測驗」為例，資料流與狀態機的互動如下：

1.  **[前端]** 工程師點擊「開始測驗」，`app.js` 呼叫 `Api.startExam()`。
2.  **[後端]** `assessment.py` 確認資料庫是否有未完成的 `draft`。若有則直接返回該 `session_id` (容錯恢復)；若無則建立全新 `ExamSession`，並預先產生所有題目的空白 `ExamAnswer`，隨後回傳。
3.  **[前端]** `app.js` 收到 `session_id`，呼叫 API 取得所有題目並渲染表單。同時啟動 `setInterval` 每 10 秒執行一次 `triggerAutosave()`。
4.  **[前端]** 使用者作答過程中，Autosave 非同步將資料 `PUT` 至後端。
5.  **[後端]** 後端更新對應 `ExamAnswer` 的 `provided_answer` 欄位，維持 `draft` 狀態。
6.  **[前端]** 使用者點擊提交，發送 `POST /submit`。
7.  **[後端]** 系統自動比對選擇題答案並給分，將 `ExamSession` 狀態更新為 `submitted`，完成本次檢測。
