# TASK-010 Codex Cloud 云端开发环境适配

## 目标

让 GitHub、Windows 本地 Codex 和手机端 Codex Cloud 通过任务分支和项目文档接续开发。此任务属于开发环境维护，学习进度仍由 `docs/LEARNING_STATE.md` 管理。

## 范围

- 保留 Windows 开发路径，提供锁定依赖的 Linux 安装和统一测试入口。
- 提供无凭证配置示例、忽略规则和凭证风险检查。
- 核心测试隔离 LLM、RSS 与 Search 外部请求。提供独立、可选的 PostgreSQL 迁移与测试数据示例。
- 记录新版 Cloud 安装、启动、环境变量、HTTP secrets、网络权限与手机接续方式。
- 禁止自动合并或推送到 `main`。

## 验收

1. 干净 Linux 运行两次 `bash scripts/codex-setup.sh`，依赖锁文件保持一致。
2. 已安装依赖后，断网运行 `bash scripts/codex-test.sh`。Windows 运行 pytest。
3. 按云端教程验证新环境和手机端可见的任务分支。测试通过后更新 `docs/AI_CONTEXT.md`，保留已有学习记录。

验证结果和账号侧操作见 [云端配置与迁移报告](../docs/CODEX_CLOUD_SETUP.md)。
