# ✨ 会计系统专业版 (Professional Accounting System)

<div align="center">

**全功能中文会计桌面应用 · 适合中小企业财务管理**

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![tkinter](https://img.shields.io/badge/tkinter-Desktop%20GUI-FF6B9D?style=for-the-badge&logo=python&logoColor=white)](https://docs.python.org/3/library/tkinter.html)
[![SQLite](https://img.shields.io/badge/SQLite-3-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-Charts-11557C?style=for-the-badge&logo=python&logoColor=white)](https://matplotlib.org/)
[![Blockchain](https://img.shields.io/badge/Blockchain-SHA--256-121D33?style=for-the-badge&logo=blockchain.com&logoColor=white)](https://en.wikipedia.org/wiki/SHA-2)
[![AI](https://img.shields.io/badge/AI-Cloud%20Integration-8B5CF6?style=for-the-badge&logo=openai&logoColor=white)](https://openai.com/)
[![ESG](https://img.shields.io/badge/ESG-Reporting-4CAF50?style=for-the-badge&logo=leaflet&logoColor=white)](https://en.wikipedia.org/wiki/Environmental,_social_and_governance)
[![License](https://img.shields.io/badge/License-MIT-yellow?style=for-the-badge)](LICENSE)

</div>

> 一款功能全面的中文会计桌面系统，提供从凭证录入到财务报表、固定资产管理、税务计算、多币种核算、AI 智能分析、区块链账本、ESG 报告等 29+ 核心模块，覆盖中小企业财务管理的全流程需求。

> **📌 简历摘要：** 在一套 30+ 模块的遗留会计桌面系统（Python / tkinter / SQLite）基础上，**用 AI 协作、以绞杀者(strangler)模式增量现代化**为分层全栈架构：核心业务解耦为纯函数 + SQLAlchemy ORM 数据层（`DATABASE_URL` 一键切 SQLite/PostgreSQL）→ FastAPI 后端（Pydantic + 自动 Swagger 文档 + JWT 鉴权 + 角色权限，~40 个接口）→ React + TypeScript + Ant Design 前端（14 个页面）→ Docker Compose 一键部署。**164 个 pytest 全过**，全程版本化提交；桌面版亦保留并打磨（现代主题、品牌图标、PyInstaller 单文件 EXE）。

---

## 📋 目录

- [功能特点](#-功能特点)
- [技术栈](#-技术栈)
- [项目结构](#-项目结构)
- [快速开始](#-快速开始)
- [打包为 EXE](#-打包为-exe)
- [运行截图](#-运行截图)
- [测试](#-测试)
- [许可协议](#-许可协议)

---

## 🏗️ 架构与现代化

本项目从一套**遗留单机桌面系统**（tkinter + 裸 `sqlite3`）出发，采用**绞杀者(strangler)模式**增量演进为现代分层架构——不停机、不推翻旧系统，让新栈在旁逐步生长，并复用同一业务核心 `accsys`：

```
React + TS + AntD  ┐
                   ├─►  FastAPI (REST + JWT + Swagger)  ─►  SQLAlchemy ORM  ─►  SQLite / PostgreSQL
Flask Web (备用)   ┘                                            ▲
tkinter 桌面版 (保留) ───────────────────────────────────────────┘   ← 共用业务核心 accsys
```

- **业务核心 `accsys`**：领域逻辑与 I/O 解耦——纯计算函数（税务、报表 `*_data`）+ `repo.py`（纯 ORM 数据访问，认 `DATABASE_URL`）。
- **数据层**：SQLAlchemy 2.0，**24 个 ORM 模型 1:1 镜像原库**；设一个 `DATABASE_URL` 即可从本地 SQLite 切到 PostgreSQL。
- **后端 API**：FastAPI + Pydantic，自动 OpenAPI/Swagger 文档（`/docs`），**JWT 登录 + 角色权限**（admin / accountant / viewer），约 40 个接口。
- **Web 前端**：React 18 + TypeScript + Ant Design + Vite，**14 个功能页**（登录 / 仪表盘 / 报表 / 凭证 / 库存 / 薪资 / 项目 / 账龄 / ESG …）。
- **桌面版**：tkinter 24 个 Tab 完整保留，并做了 UI 现代化（靛紫主题、卡片登录页、品牌图标）+ PyInstaller 单文件 EXE。
- **部署**：Docker Compose 一键启动（PostgreSQL + FastAPI + Nginx 托管前端）。
- **质量**：**164 个 pytest 全过**，分阶段、可回溯的 git 提交历史。

---

## 🚀 功能特点

### 📒 凭证管理
- 标准借贷记账法，支持多分录凭证
- 自动凭证编号与模板快速录入
- 凭证审核、查询、修改、删除、批量导出 (Excel/CSV)
- CSV 导入凭证

### 📊 财务报表
- **资产负债表** — 自动生成，资产 = 负债 + 所有者权益
- **利润表** — 多步式损益计算，营业利润 → 利润总额 → 净利润
- **现金流量表** — 间接法与直接法双模式
- **科目余额表 / 试算平衡表**
- **财务比率分析** — 流动比率、速动比率、资产负债率、毛利率、净利润率等
- **智能趋势预测** — 基于历史数据的下月预测

### 🏠 固定资产管理
- 固定资产卡片登记 (原值、残值、使用年限)
- 自动计提折旧 (年限平均法)
- 折旧明细查询与批量折旧运行
- 反折旧处理

### 🧾 税务计算
- **增值税 (VAT)** 计算与申报模拟
- **个人所得税 (PIT)** 预扣预缴，支持 7 级超额累进税率
- 税务速算表与减免参考
- 学生兼职税务指导

### 💱 多币种支持
- 实时汇率获取 (exchangerate-api.com)
- 手动汇率录入
- 外币业务凭证记录
- 多币种核算

### 📈 数据可视化
- 收支对比柱状图
- 资产负债表饼图
- 月度趋势折线图
- 财务比率雷达图
- 综合看板 (Dashboard)

### 🧠 智能分析
- **AI 云集成** — 支持 OpenAI / 兼容 API，自然语言财务问答
- **异常检测** — 自动识别异常分录与离群交易
- **智能建议** — 基于财务比率的经营建议
- **趋势分析** — 收入/费用月度趋势

### ⛓️ 区块链账本
- 基于 SHA-256 的区块链接结构
- 每笔凭证作为交易记录上链
- 区块链完整性验证 (防篡改)
- 区块链导出/导入 JSON
- 链状态统计 (区块数、交易数、时间线)

### 🌿 ESG 报告
- **环境 (E)** — 碳排放、能耗、用水、废弃物、可再生能源等指标
- **社会 (S)** — 员工总数、女性比例、培训时长、安全、客户满意度
- **治理 (G)** — 董事会、独立董事、合规、审计、数据安全
- 雷达图与趋势图分析
- 综合评分与报告导出

### 🤖 AI 助手
- AI 配置管理 (端点、密钥、模型、参数)
- 自动构建财务上下文
- 自然语言数据库查询 (Text-to-SQL)
- 财务顾问问答

### 📋 应收应付 (AR/AP)
- 应收账款 / 应付账款账龄分析
- 账龄区间划分 (30/60/90/180/365 天)
- 坏账准备自动计提 (按账龄比例)
- AR/AP 汇总与明细

### 📦 库存管理
- 产品档案管理 (编码、名称、规格、单价)
- **FIFO (先进先出)** 成本核算
- 入库 / 出库 / 盘点操作
- 库存流水与库存汇总查询
- 库存数量与金额实时更新

### 📊 预算管理
- 科目预算编制 (年初/月度预算)
- 预算执行进度监控
- 实际 vs 预算对比

### 💰 薪资管理
- 员工信息管理 (部门、岗位、基本工资)
- 自动工资计算 (社保、公积金、个税)
- 工资确认与凭证生成
- 工资发放记录查询

### 🏦 银企对账
- 导入银行流水
- 自动勾对 (自动对账)
- 对账状态管理
- 余额调节表

### 🏗️ 项目会计
- 项目立项与基本信息管理
- 项目收支明细 (关联凭证)
- 项目损益计算
- 项目利润分析

### 🔔 财务预警
- 自定义预警规则 (流动比率、资产负债率、净利润率等)
- 实时指标计算与预警触发
- 预警历史与处理
- 预警级别 (warning/critical)

### 📎 附件管理
- 凭证附件上传与管理
- 文件类型识别
- 附件目录自动初始化
- 附件删除与查看

### 🔐 多用户权限
- 用户登录/登出 (默认 admin/admin123)
- 角色权限管理 (管理员 / 会计 / 出纳)
- 操作审计日志
- 界面主题独立记忆

### 🌙 深色模式
- 浅色 / 深色主题一键切换
- 粉紫配色方案
- 主题持久化存储

### 🗓️ 期末结账
- 期末自动结转损益
- 期间状态管理 (未结账 / 已结账)
- 结账日志查询
- 反结账处理

### 📤 数据备份与恢复
- 数据库一键备份
- 备份文件管理
- 数据库恢复还原

### 🎓 考证助手
- CPA / 初中级会计 / 税务师考试信息
- 学习计划生成器
- 个人学习进度追踪

### 📈 微型账本
- 个人收支流水记录
- 收支分类汇总
- 学生税务参考

---

## 🛠️ 技术栈

| 类别 | 技术 | 用途 |
|------|------|------|
| **语言** | Python 3.10+ / TypeScript | 后端 / 前端 |
| **桌面 GUI** | tkinter / ttk | 桌面图形界面，24 个功能 Tab |
| **后端 API** | FastAPI + Pydantic | REST 接口、数据校验、自动 Swagger 文档 |
| **鉴权** | PyJWT (JWT) | 登录令牌 + 角色权限 |
| **ORM / 数据层** | SQLAlchemy 2.0 | 24 个模型，`DATABASE_URL` 切换数据库 |
| **数据库** | SQLite 3 / PostgreSQL | 本地单文件 / 生产多用户 |
| **Web 前端** | React 18 + Ant Design + Vite | 14 个功能页，现代后台 UI |
| **图表** | matplotlib / ECharts | 桌面 / Web 数据可视化 |
| **测试** | pytest | 164 个用例，覆盖核心/API/数据层 |
| **部署** | Docker Compose + Nginx | 一键启动 db + api + 前端 |
| **打包** | PyInstaller | 桌面版单文件 EXE（带品牌图标） |
| **其他** | openpyxl / requests / hashlib / Pillow | Excel / 网络 / SHA-256 区块链 / 图标 |

---

## 📁 项目结构

```
accounting_system/                    # 项目根目录
│
├── accsys/                           # 后端核心包 (Python package)
│   ├── __init__.py                   #   统一导出入口
│   ├── constants.py                  #   全局常量、科目表、税率、ESG指标
│   ├── database.py                   #   数据库初始化与连接管理
│   ├── accounts.py                   #   科目表管理、试算平衡
│   ├── vouchers.py                   #   凭证 CRUD、导入导出
│   ├── reports.py                    #   财务报表 (资产负债表、利润表、现金流量表)
│   ├── assets.py                     #   固定资产管理与折旧计算
│   ├── tax.py                        #   增值税与个人所得税计算
│   ├── currency.py                   #   多币种汇率管理
│   ├── period.py                     #   期末结账与期间管理
│   ├── blockchain.py                 #   区块链账本 (SHA-256)
│   ├── esg.py                        #   ESG 报告与评分
│   ├── startup.py                    #   启动工具与微型账本
│   ├── ai.py                         #   AI 云集成配置与调用
│   ├── auth.py                       #   认证、权限、主题管理
│   ├── aging.py                      #   应收应付账龄分析
│   ├── budget.py                     #   预算编制与执行监控
│   ├── inventory.py                  #   库存管理 (FIFO)
│   ├── viz.py                        #   数据可视化图表生成
│   ├── audit.py                      #   审计轨迹日志
│   ├── alerts.py                     #   财务预警规则与检查
│   ├── backup.py                     #   数据库备份与恢复
│   ├── reconciliation.py             #   银企对账自动匹配
│   ├── payroll.py                    #   薪资计算、个税、凭证生成
│   ├── projects.py                   #   项目会计与损益分析
│   ├── cashflow.py                   #   现金流量表（直接法）
│   ├── attachments.py                #   文件附件上传与管理
│   └── cli.py                        #   命令行 TUI 交互界面
│
├── gui/                              # 前端 GUI 包
│   ├── app.py                        #   主应用骨架（~300行）
│   ├── constants.py                  #   UI 样式常量
│   └── tabs/                         #   24 个标签页模块（Mixin 模式）
│       ├── voucher.py                #   凭证录入
│       ├── query.py                  #   凭证查询
│       ├── accounts.py               #   科目余额
│       ├── reports.py                #   财务报表
│       ├── assets.py                 #   固定资产
│       ├── tax.py                    #   税务计算
│       ├── currency.py               #   多币种
│       ├── period.py                 #   期末处理
│       ├── aging.py                  #   应收应付
│       ├── budget.py                 #   预算管理
│       ├── inventory.py              #   库存管理
│       ├── viz.py                    #   数据可视化
│       ├── intel.py                  #   智能分析
│       ├── blockchain.py             #   区块链账本
│       ├── esg.py                    #   ESG 报告
│       ├── startup.py                #   创业工具
│       ├── ai.py                     #   AI 助手
│       ├── audit.py                  #   审计日志
│       ├── alerts.py                 #   财务预警
│       ├── recon.py                  #   银企对账
│       ├── payroll.py                #   薪资管理
│       ├── projects.py               #   项目会计
│       ├── cashflow.py               #   现金流量
│       └── attachments.py            #   附件管理
│
├── tests/                            # 测试目录 (pytest, 164 个用例)
│   ├── test_core.py                  #   核心业务 / 报表 / 税务
│   ├── test_repo.py                  #   SQLAlchemy ORM 数据层
│   ├── test_api.py                   #   FastAPI 接口 / 鉴权 / 写操作
│   └── test_webapp.py                #   Flask 网页路由
│
├── api/                              # FastAPI 后端 (REST + JWT + Swagger)
│   ├── main.py                       #   应用与路由
│   ├── schemas.py                    #   Pydantic 模型
│   └── auth.py                       #   JWT 鉴权与角色权限
│
├── frontend/                         # React + TS + AntD 前端 (Vite)
│   ├── src/pages/                    #   14 个功能页
│   ├── src/api.ts                    #   接口客户端 (axios + JWT)
│   └── Dockerfile / nginx.conf       #   前端容器与反代
│
├── webapp.py                         # Flask 备用网页端 (复用 ORM repo)
├── seed_data.py                      # 演示数据填充脚本
├── Dockerfile                        # 后端镜像
├── docker-compose.yml                # 一键部署 (db + api + 前端)
├── accounting_icon.ico               # 品牌图标
├── screenshots/                      # 运行截图
├── main.py                           # 桌面版入口
└── requirements.txt                  # 依赖清单
```

> 注：`accsys/` 新增 `db.py`（引擎/会话）、`models.py`（24 个 ORM 模型）、`repo.py`（纯 ORM 数据访问，认 `DATABASE_URL`），构成可切 SQLite/PostgreSQL 的数据层。

---

## ⚡ 快速开始

### 前置要求

- Python 3.10 或更高版本
- pip 包管理器

### 安装与运行

```bash
# 1. 克隆仓库
git clone https://github.com/yourusername/accounting_system.git
cd accounting_system

# 2. 安装依赖
pip install -r requirements.txt

# 3. 三种运行方式（任选）

# ① 桌面版（tkinter）
python main.py

# ② 后端 API（FastAPI）— 自动文档 http://localhost:8000/docs
uvicorn api.main:app --reload

# ③ Web 前端（React）— http://localhost:5173
cd frontend && npm install && npm run dev
```

> 默认账号：`admin / admin123`（管理员）、`accountant / acc123`（会计）、`viewer / view123`（只读）

### 🐳 Docker 一键部署

```bash
docker compose up --build
# 前端 http://localhost:8080   后端 http://localhost:8000/docs
```

### 依赖清单

```
openpyxl      # Excel 导入导出
pyinstaller   # 打包为 EXE
pillow        # 图标与图片
matplotlib    # 数据可视化图表
requests      # AI API & 汇率请求
```

---

## 📦 打包为 EXE

使用 PyInstaller 打包为单文件可执行程序，无需 Python 环境即可运行：

```bash
# 标准打包 (带控制台窗口，方便调试)
pyinstaller --onefile --icon=accounting_icon.ico main.py --name=会计系统专业版

# 生产环境打包 (隐藏控制台窗口)
pyinstaller --onefile --windowed --icon=accounting_icon.ico main.py --name=会计系统专业版
```

打包完成后，可执行文件位于 `dist/会计系统专业版.exe`。

> 💡 如需生成安装包，运行 `build_installer.bat` (基于 NSIS)。

---

## 🌐 Web 版本 (Flask)

基于 `accsys` 包的独立性，增加 Flask Web 前端，展示后端逻辑完全解耦：

```bash
pip install flask
python seed_data.py      # 先填充种子数据
python webapp.py          # 启动 Web 服务
# 浏览器打开 http://localhost:5000
```

| 路由 | 功能 |
|------|------|
| `/` | 财务仪表盘 (KPI + 比率 + 预警) |
| `/vouchers` | 凭证列表 (按年月查询) |
| `/accounts` | 科目余额表 |
| `/reports` | 三张财务报表 |
| `/api/ratios` | 财务比率 JSON API |
| `/api/vouchers` | 凭证 JSON API |
| `/api/accounts` | 科目余额 JSON API |
| `/api/reports/*` | 报表 JSON API |

> 桌面 GUI (`/gui`) 和 Web 版 (`webapp.py`) 共用同一套 `accsys` 后端模块，证明 MVC 架构的解耦程度。

---

## 📸 运行截图

> 以下为功能界面预览，截图文件位于 `screenshots/` 目录。

```
screenshots/
├── 01_main.png          # 主界面 (凭证录入 + 种子数据)
├── 02_reports.png       # 财务报表
├── 03_viz.png           # 数据可视化看板
└── 04_aging.png         # 应收应付账龄分析
```

| 主界面 / 凭证录入 | 财务报表 |
|:------:|:--------:|
| ![主界面](screenshots/01_main.png) | ![财务报表](screenshots/02_reports.png) |
| **数据可视化看板** | **应收应付账龄** |
| ![可视化](screenshots/03_viz.png) | ![账龄](screenshots/04_aging.png) |

---

## 🧪 测试

```bash
# 安装测试依赖
pip install pytest

# 运行全部测试（共 164 个用例，全部通过）
pytest

# 按模块运行
pytest tests/test_core.py     # 核心业务 / 报表 / 税务
pytest tests/test_repo.py     # SQLAlchemy ORM 数据层
pytest tests/test_api.py      # FastAPI 接口 / 鉴权 / 写操作
pytest tests/test_webapp.py   # Flask 网页路由
```

> 测试覆盖核心业务逻辑、ORM 数据层、REST API（含 JWT 鉴权与角色权限）及 Web 路由。

---

## 📄 许可协议

本项目基于 **MIT License** 开源，您可以自由使用、修改和分发。

```
MIT License

Copyright (c) 2024-2026

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
...
```

---

<div align="center">
  <sub>Built with ❤️ using Python & tkinter</sub>
  <br>
  <sub>会计系统专业版 · Professional Accounting System</sub>
</div>
