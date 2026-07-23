# Engineer Skill Assessment System

這是一個為企業內部工程師設計的「技能量化與出題測驗系統」。系統分為 Leader 與 Engineer 兩種角色，旨在協助團隊追蹤、量化工程師的各項技術能力，並允許擁有特定技能出題權限的工程師擴充題庫。

## 系統核心功能

1. **角色與權限隔離 (Role-Based Access Control)**
   - **Leader**: 具備最高權限。可以建立技能分類、管理題庫、檢視所有工程師的量化雷達圖、以及強制重設工程師密碼。
   - **Engineer**: 可以進行已分配的技能測驗、檢視自身的專屬雷達圖。若被授予特定技能的「出題權限」，則可以進入出題模式貢獻題庫。

2. **動態能力量化 (Quantified Skill Matrix)**
   - 使用 Chart.js 將測驗結果轉換為動態雷達圖。
   - Leader 可透過儀表板一次檢視所有工程師的能力分佈，並支援點擊卡片無縫展開詳細技能分數。
   - Engineer 擁有專屬的儀表板，專注於自身的技能成長。

3. **Multi-Page Application 架構 (MPA)**
   - 後端使用 Flask，透過 Jinja2 模板引擎進行頁面渲染，確保各功能（儀表板、題庫管理、使用者管理）在獨立路由下運作。
   - 提供 `/api` 端點進行所有資料互動（如登入、出題、交卷），達到前後端邏輯解耦。

4. **測驗與題庫管理**
   - 支援自動儲存 (Auto-save) 功能，工程師若中斷測驗，下次登入可無縫接續。
   - 題庫提供「單選題」與「簡答題」，並支援 Inline-editing，方便即時修正題目內容。

## 環境依賴 (Dependencies)

請參考 `MAINTENANCE.md` 中詳細的環境設定與交接指南。

## 快速啟動指南

1. **安裝環境與依賴** (請確保系統已安裝 Python 3.10+)：
   ```bash
   pip install -r requirements.txt
   ```
2. **啟動伺服器**：
   ```bash
   python run.py
   ```
3. **瀏覽器訪問**：
   開啟 `http://127.0.0.1:5000/`

4. **預設測試帳號**：
   - **Leader**: `帳號: leader` / `密碼: password`
   - **Engineer**: `帳號: engineer1` / `密碼: password`

## 專案結構

- `app/`
  - `__init__.py` : Flask App Factory，包含所有頁面路由
  - `extensions.py` : 初始化 SQLAlchemy 等擴充套件
  - `models/` : 資料庫模型 (User, Skill, Question, AssessmentSession, Answer)
  - `routes/` : API 路由控制器 (auth, admin, assessment)
  - `services/` : 業務邏輯層
  - `repositories/` : 資料庫存取層 (Data Access Layer)
  - `templates/` : Jinja2 HTML 模板
  - `static/` : 靜態資源 (CSS, JS)
- `run.py` : 程式進入點
- `skill_assessment.db` : SQLite 本機資料庫 (開發測試用)
