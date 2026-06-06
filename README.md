## 專案動機
以個人興趣為出發點的實作專案。藉由開發一個有完整功能的系統，
同時練習新技術（FastAPI 非同步開發、SQLAlchemy Session 管理、
Redis 快取、Docker 容器化、JWT 認證）與複習既有基礎
（Python 爬蟲、SQL 資料庫設計、前端切版）。

## 功能
**後端**
- FastAPI（非同步 API，適合 I/O 密集的爬蟲場景）
- SQLAlchemy（async ORM）+ SQLite
- JWT（python-jose）
- curl_cffi（繞過 Cloudflare 爬取 ArtStation）
- Redis（快取常用查詢結果）
- RBAC 角色權限控制

**前端**
- HTML + JavaScript（純前端，無框架）

**部署**
- Docker + docker-compose

## 快速開始
**使用 Docker（推薦）**
git clone https://github.com/ChinoEst/gallery.git
cd gallery
docker-compose up --build

API 文件：http://localhost:8000/docs

**本地開發**
pip install -r requirements.txt
python -m uvicorn server:app --reload

前端：直接用瀏覽器開啟 `frontend/index.html`，或使用 Live Server。

## 使用流程
1. 開啟前端介面，註冊或登入帳號
2. 在左側新增想追蹤的 ArtStation 創作者（輸入名稱和個人頁網址）
3. 系統自動爬取該創作者的作品
4. 瀏覽圖片、用 Tag 搜尋、或依創作者篩選
