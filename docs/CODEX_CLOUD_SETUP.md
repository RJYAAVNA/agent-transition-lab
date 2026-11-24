# Codex Cloud 配置与迁移报告

## 1. 创建新版 Cloud 环境

1. 通过 GitHub 授权 Codex 访问 `RJYAAVNA/agent-transition-lab`。先审查本次改动，再提交并推送任务分支，使云端可以检出它。当前本地 `main` 含有尚未出现在本地 `origin/main` 引用上的提交，选择任务分支后核对实际检出的 commit。
2. 在网页或桌面端打开 **Settings → Codex Cloud → Environments**，创建环境并选择该 GitHub 仓库。在设置对话里指定任务分支，要求从仓库根目录配置下面的 Install script 和 Start skill。
3. 检查 Python、安装、测试和启动结果。按需设置网络和凭证，然后 **Publish**。后续安装配置有改动时，进入 **Edit** 修改并 **Republish**，用新任务验证更新。

[新版 Cloud 环境官方指南](https://learn.chatgpt.com/docs/environments/cloud-environments)

## 2. Install script

选择 Python 3.11+，建议与本地验证使用同一 Python 次版本。若镜像没有 uv，Python 需要提供 `venv` 和 `ensurepip`，脚本会从 PyPI 安装固定版 uv 到仓库的 `.codex-tools/`。可用 `CODEX_PYTHON=python3.12` 显式选择解释器。

```bash
bash scripts/codex-setup.sh
```

脚本按 `uv.lock` 安装开发依赖。运行两次应成功，`git diff --exit-code -- uv.lock` 应通过。缓存目录和虚拟环境随工作区保存时可供后续使用。锁文件更新后，重新运行安装并验证。默认测试命令直接使用已安装的虚拟环境，支持传入 pytest 参数。

```bash
bash scripts/codex-test.sh
bash scripts/codex-test.sh -q tests/test_research_agent.py
```

## 3. Start skill

在 Start skill 中保存以下启动说明。纯代码和测试任务直接运行测试脚本。需要 API 时，在仓库根目录执行启动命令，将服务保持在后台或独立终端，再请求健康检查。

```bash
.venv/bin/python -m uvicorn --app-dir src app.main:app --host 127.0.0.1 --port 8765
```

```bash
curl -fsS http://127.0.0.1:8765/openapi.json
```

在 Codex 的 **HTTP Previews** 中按需添加端口 `8765` 并应用到聊天，打开预览的 `/docs`。如果预览需要服务监听工作区网络接口，使用 `--host 0.0.0.0`。健康检查与 OpenAPI 文档无需凭证。真实 `POST /research` 会访问 RSS 和搜索服务。

[Cloud 启动与 HTTP Previews](https://learn.chatgpt.com/docs/environments/cloud-environments)

## 4. 环境变量、HTTP secrets 和网络权限

配置优先级为进程环境变量、仓库根目录 `.env`、旧版 `src/.env`。本地需要覆盖默认值时复制 `.env.example` 到 `.env`，用 UTF-8 保存。Windows 启动可继续使用 `py -m uv run --locked uvicorn --app-dir src app.main:app --reload`。

| 场景 | 云端配置 |
| --- | --- |
| 安装 | 启用 **Enable package manager domains**，验证可以访问锁文件使用的 `pypi.org` 和分发包所在的 `files.pythonhosted.org` |
| 核心测试及健康检查 | 安装后可断网执行，无需填入凭证 |
| 真实 RSS 和 Search | 在 **Additional allowed domains** 添加实际使用的 `feeds.bbci.co.uk` 与 `en.wikipedia.org`。自定义端点或发生重定向时，再按需加入实际目标域名 |
| 真实 OpenAI Agent | **Environment variables** 设置 `LLM_PROVIDER=openai`，按需设置 `OPENAI_MODEL`。**HTTP secrets** 中将 `OPENAI_API_KEY` 绑定到 `api.openai.com` |
| 真实 DeepSeek Agent | 设置 `LLM_PROVIDER=deepseek`，按需设置 `DEEPSEEK_MODEL` 与 `DEEPSEEK_BASE_URL`。将 `DEEPSEEK_API_KEY` 绑定到配置使用的 HTTPS 域名，默认 `api.deepseek.com` |

HTTP secrets 把占位符传给应用，代理仅对匹配的 HTTPS 443 目标替换为真实值。凭证键避免同时配置成普通环境变量。保存环境级 HTTP secrets 后检查目标域名策略，使用应用实际客户端验证。保留平台代理和 TLS 校验。个人凭证可通过 **Personal vault** 提供。直接 TCP 的 PostgreSQL 连接需要单独配置网络和数据库凭证，本教程的测试实例仅用本地 Unix socket。

[Cloud 网络和凭证配置](https://learn.chatgpt.com/docs/environments/cloud-environments)

## 5. 离线测试与可选 PostgreSQL

核心 pytest 套件在进程内使用 FastAPI ASGI、LLM 假客户端、RSS/Search 固定数据及替身。新增 HTTP 用例时，在模块实际引用的请求入口替换请求，例如 `tests/test_rss_tool.py` 替换 `app.tools.rss_tool.urlopen`；Agent 工具选择和异常路径沿用 `tests/test_research_agent.py` 的注入式替身。真实外部服务的验收可在单独的 Cloud 任务中按上节开启网络后运行。

当前应用使用内存状态。PostgreSQL 仅用于验证未来数据库任务的基本流程，示例表和种子使用合成数据。运行此演练要有 PostgreSQL 17 工具，使用非 root 身份，并确保 `initdb`、`pg_ctl`、`createdb` 和 `psql` 在 PATH 上。以下命令在仓库根目录运行，使用短路径的临时目录和私有 Unix socket。子 shell 结束后清理临时实例。

```bash
(
    set -euo pipefail
    db_dir="$(mktemp -d)"
    cleanup() {
        pg_ctl -D "$db_dir/data" -m fast -w stop >/dev/null 2>&1 || true
        rm -rf -- "$db_dir"
    }
    trap cleanup EXIT

    initdb -D "$db_dir/data" -A trust --no-locale
    pg_ctl -D "$db_dir/data" -l "$db_dir/postgres.log" \
        -o "-c listen_addresses= -c unix_socket_directories=$db_dir" -w start
    createdb -h "$db_dir" agent_transition_test
    for attempt in 1 2; do
        psql -X -h "$db_dir" -d agent_transition_test -v ON_ERROR_STOP=1 \
            --single-transaction -f tests/postgres/migrations/001_create_fixture.sql \
            -f tests/postgres/seed.sql
    done
    psql -X -h "$db_dir" -d agent_transition_test -v ON_ERROR_STOP=1 \
        -Atc 'SELECT fixture_id, title FROM cloud_test_fixture;'
)
```

预期只输出一条 fixture 数据 `sample-feed|Sample feed for cloud setup`。示例迁移按编号执行，种子按主键 upsert，每个演练使用独立数据库。后续任务实际引入持久化时，再结合项目的数据模型和部署需求确定正式迁移机制。

## 6. 手机与 Windows 接续

- 手机端打开 Codex，选择已发布环境。继续已有云端工作时打开同一个聊天；开始新任务时核对 GitHub 分支与提交。发布环境和任务工作区分别保存，分支上的改动需要推送才能给新的工作区使用。
- 新任务示例提示词：请在指定任务分支读取 `AGENTS.md`、`docs/AI_CONTEXT.md`、`docs/LEARNING_STATE.md` 和 `tasks/TASK-010.md`，按任务范围运行测试，更新项目进度文档并汇报结果。提交、推送和合并前先交我审查。
- 本地 Windows 接续时拉取对应任务分支，使用 `py -m uv sync --locked --dev` 和 `py -m uv run --locked pytest`。学习路线与任务状态仍通过 `docs/LEARNING_ROADMAP.md`、`docs/LEARNING_STATE.md`、`docs/AI_CONTEXT.md` 和 `tasks/` 同步。

[跨网页、桌面和手机继续 Cloud 任务](https://learn.chatgpt.com/docs/environments/cloud-environments)

## 7. 迁移检查报告

| 检查 | 结果 |
| --- | --- |
| 工作区和 Git | 原 Windows 工作区在 `feature/TASK-009-execution-loop`，有已暂存、未暂存和未跟踪的学习资料。本任务从本地 `main` 的 `dafc362` 创建独立工作树和 `feature/TASK-010-codex-cloud` |
| 依赖和运行 | Python 3.11+、uv、公开 PyPI 锁文件、FastAPI/Uvicorn。Windows 专用命令出现在本地使用说明中，Linux 使用单独的 Bash 命令；脚本固定 LF |
| 配置和凭证 | 已补齐空 API Key、配置优先级及忽略规则。启始分支的可达 Git 历史中，常见 OpenAI/GitHub/AWS 凭证、私钥头和含用户名密码的 PostgreSQL URI 模式未命中。模式检查范围有限，当前 Trace 仍会保存工具参数、结果及异常，请对分享内容脱敏 |
| 数据库和外部依赖 | 核心测试无需 PostgreSQL、RSS、Search 或 LLM 网络。PostgreSQL 迁移和种子可在隔离实例演练 |
| Linux 安装与测试 | 干净 `python:3.12-slim` 容器连续安装两次，`uv.lock` 校验和一致。随后在 `--network none` 容器中运行统一入口，42 项通过 |
| Windows 安装与测试 | Python 3.12 下从锁文件安装成功，42 项通过。Uvicorn 启动后通过 `/openapi.json` 确认 `/research` 已注册 |
| PostgreSQL 演练 | `postgres:17-alpine` 断网容器中初始化、迁移和种子执行成功。迁移和种子应用两次后查询得到一条预期记录 |

### 仍需人工配置

1. 审查差异后，将任务分支提交并推送到 GitHub。保留原 TASK-009 工作区的学习资料。
2. 在账号侧授权仓库，填写并验证 Install script、Start skill，然后发布环境。
3. 在手机上打开已发布环境，确认实际检出目标分支、运行测试并检查结果。
4. 只有需要验证真实服务时才添加目标域名和个人 API 凭证，随后用实际客户端确认可用。
