# 環境依賴 (Dependencies)

本專案使用 Python Flask 作為後端架構，無前端框架，僅使用原生 HTML/CSS/JS。
以下為 Python 後端的環境依賴清單：

| Package Name | Version | Purpose |
| :--- | :--- | :--- |
| `Flask` | `3.0.3` | Python 網頁框架，負責提供 RESTful API 服務 |
| `Flask-Cors` | `4.0.1` | 處理跨來源資源共用 (CORS)，允許前端存取 API |
| `Flask-SQLAlchemy` | `3.1.1` | ORM (Object Relational Mapping)，管理與 SQLite 的資料庫連線 |
| `PyJWT` | `2.8.0` | 處理 JSON Web Token (JWT) 的產生與驗證，用於身分驗證 |
| `bcrypt` | `4.1.3` | 提供高強度的密碼雜湊加密功能 |

### 安裝指令 (Installation)

請確定您的系統已安裝 Python 3 (建議 3.9 以上版本)。
在專案根目錄執行以下指令：

```powershell
# 1. 建立虛擬環境
python -m venv venv

# 2. 啟動虛擬環境 (Windows PowerShell)
.\venv\Scripts\activate

# 3. 安裝相依套件
pip install -r requirements.txt
```
