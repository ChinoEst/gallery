# Gallery

創作者追蹤與圖片收藏管理系統。追蹤 ArtStation 上喜歡的創作者，自動爬取作品，並透過網頁介面瀏覽、搜尋。

> ⚠️ 本專案開發中，部分功能尚未完整實作。

## 功能

**已完成**
- 帳號系統（JWT 認證）
- 創作者管理（新增、追蹤）
- ArtStation 爬蟲（自動抓取作品與標籤）
- 圖片瀏覽（分頁、依創作者篩選、依 Tag 搜尋）
- Redis 快取
- Docker 容器化

**開發中**
- 角色權限控管（RBAC）
- 批次下載（勾選圖片下載到本地）

## 技術棧

**後端**
- FastAPI（非同步 API，適合 I/O 密集的爬蟲場景）
- SQLAlchemy（async ORM）+ SQLite
- JWT（python-jose）
- curl_cffi（繞過 Cloudflare 爬取 ArtStation）
- Redis（快取常用查詢結果）

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
