# 系統維護與交接指南 (Maintenance Guide)

這份文件旨在協助後續的開發者快速接手「Engineer Skill Assessment System」專案。請仔細閱讀以下架構設計與環境要求，並在進行擴充或重構時遵守既定的設計模式。

## 1. 環境依賴 (Dependencies)

請確保您的開發環境符合以下需求。如需重新建置環境，請使用 `pip install -r requirements.txt` 進行安裝。

| Package Name | Version (推薦) | Purpose (用途簡述) |
| :--- | :--- | :--- |
| **Python** | `3.10+` | 系統執行核心環境 |
| **Flask** | `3.0.0` | 網頁框架 (Web Framework)，負責路由解析與伺服器邏輯 |
| **Flask-SQLAlchemy** | `3.1.1` | ORM 套件，用於資料庫操作與抽象化 |
| **PyJWT** | `2.8.0` | 產生與解析 JSON Web Tokens (JWT)，處理登入與 API 認證 |
| **bcrypt** | `4.1.2` | 處理密碼雜湊加密，確保系統安全性 |

*(若專案目前缺少 `requirements.txt`，請執行 `pip freeze > requirements.txt` 產生。)*

## 2. 系統架構解析

本系統嚴格遵循 **Layered Architecture (分層架構)**，將關注點分離，確保系統具備高度的擴展性與可維護性。

### 2.1 目錄與職責劃分
*   **`app/routes/` (Controllers)**: 
    負責接收前端的 HTTP 請求，驗證 JWT (透過 `@token_required` decorator)，並將資料交給 Service 層處理。**此層絕對不能直接呼叫資料庫。**
*   **`app/services/` (Business Logic)**:
    處理核心商業邏輯（如：計算分數、驗證權限、處理出題邏輯）。如果邏輯出錯，應拋出 `ValueError` 交由 Routes 層捕捉並回傳 `400` / `403`。
*   **`app/repositories/` (Data Access Layer)**:
    唯一的資料庫溝通管道。所有 SQLAlchemy 的 `query`, `add`, `commit` 都封裝在此。這樣設計是為了確保未來若需要更換資料庫或進行複雜查詢時，不必修改上層邏輯。
*   **`app/templates/` (Views)**:
    使用 Jinja2 模板引擎進行頁面渲染。所有頁面均繼承自 `base.html`，並依賴 Bootstrap 5 進行樣式排版。

### 2.2 前端資料流
前端大量使用了 JavaScript 的非同步請求 (`async/await`)。
所有的 API 請求都集中封裝在 `app/static/js/api.js` 中的 `Api` 類別內。
*   **安全防護**: 若 API 回傳 HTTP 401，`Api.request()` 會自動清除 localStorage 的憑證並將使用者導向登入頁面，實現統一的安全控管。

## 3. 開發與擴充規範 (Development Rules)

### 3.1 擴充資料表 (Database Migration)
目前系統使用 SQLite，並透過 SQLAlchemy 處理。若您需要新增欄位，請前往 `app/models/` 修改對應的 Model，然後在開發環境中刪除舊有的 `skill_assessment.db`，重啟應用程式讓系統自動呼叫 `db.create_all()` 產生新結構。
*(若是正式環境，請考慮引入 `Flask-Migrate` 進行版本控制。)*

### 3.2 新增權限控制
系統目前的角色分為 `leader` 與 `engineer`。權限判定集中在兩處：
1.  **前端**: 透過 `localStorage.getItem('user')` 來判定是否顯示特定 UI（如 Engineer 儀表板中的出題權限提示）。
2.  **後端**: `current_user.role` 在 Route 或 Service 中被嚴格檢查。**任何安全性防護必須以後端驗證為主。**

### 3.3 錯誤回報機制
若在 Service 層遇到錯誤（例如「權限不足」或「輸入格式錯誤」），請依循防錯機制 (Fail fast)，主動拋出例外：
```python
if user.role != 'leader':
    raise ValueError('Only leader can perform this action')
```
Route 層會統一將其轉換為 JSON 格式的 HTTP 403 / 400 回應，前端收到後會透過 `showToast()` 顯示提示。

## 4. 常見問題與除錯 (Troubleshooting)

*   **Q: 前端修改了 CSS / JS 但瀏覽器沒反應？**
    *   A: 這是瀏覽器快取的問題。在 `__init__.py` 中我們配置了 static folder。開發時，可在瀏覽器按下 `Ctrl + F5` 強制重新整理，或在開發者工具中勾選「Disable cache」。
*   **Q: Engineer 點選出題頁面出現 "No Question Creation Permissions"？**
    *   A: 這是正確的行為。必須使用 Leader 帳號登入，前往 `/users` 頁面，點選該 Engineer 的「Manage Skills」，賦予他至少一項技能的權限，他才能為該技能出題。
*   **Q: 出現 `Api.getUsers is not a function` 等錯誤？**
    *   A: 系統早期為單頁架構，在重構為多頁架構 (MPA) 時，已將這些功能封裝。請確保您呼叫的是 `api.js` 裡定義的最新的 static 函式，並且在 HTML 的 `{% block scripts %}` 區塊中已確保 API script 載入。
