# 安全評估 — SSDLC / CRA / IEC 62443 差距分析

日期: 2026-01-22

## 目的

此文件記錄針對本專案之安全差距分析與補救計畫，以利對齊 SSDLC 要求與相關標準（包括 CRA 與 IEC 62443）。

## 高階結論

- 專案具良好工程實務：有規格、測試、`src` 100% 覆蓋率與貢獻指南。  
- 但缺少 CRA / IEC 62443 常見的多項安全生命週期產物（下列差距詳述）。

## 差距總覽

1. 安全需求規格：專案中未見明確的安全需求文件。  
2. 威脅建模 / 風險評估：缺乏系統性威脅辨識與風險評估結果。  
3. 軟體物料清單（SBOM）：尚未產生或保存 SBOM。  
4. 依賴漏洞掃描與 CVE 追蹤：未自動化於 CI 中。  
5. 安全導向靜態分析（SAST）：目前只有一般 linter，未使用 `bandit` 等安全掃描工具。  
6. 安全測試案例：無專門針對輸入驗證、注入、認證失敗等安全案例。  
7. 漏洞通報與事件回應政策：缺少 `SECURITY.md` 或通報規定。  
8. 發行完整性（簽章/校驗）：發行時無 checksum 或簽章流程。  
9. 安全設計文件（資料流程、信任邊界）：文件不完整或缺乏安全視角。  
10. 修補與變更管理流程：缺乏正式 CVE 分級 / 修補 SLA 流程。

## 對應 IEC 62443 的重點缺口

- SR-2（威脅建模）：缺乏相關成果文件。  
- SVV-1 / SVV-2（安全驗證 / 測試）：無自動化安全測試流程。  
- DM-1 / DM-2（缺陷管理 / 更新管理）：只有基本的 commit 歷史，未有正式 SLA 與流程文件。

## 立即可執行的工具與命令（快速起步）

1. 產生 SBOM（CycloneDX）：

```bash
pip install cyclonedx-bom
cyclonedx-py -r requirements.txt -o sbom.json
```

2. 依賴性稽核：

```bash
pip install pip-audit
pip-audit
```

3. 靜態安全掃描（Bandit）：

```bash
pip install bandit
bandit -r src/ -ll
```

4. 建議在 CI 中加入 `pip-audit`、`bandit` 與 SBOM 產生步驟。

## 建議交付物（優先順序）

短期（幾天內）：
- `SECURITY.md`（漏洞通報、聯繫方式、回應 SLA）  
- 在 CI 中加入 `bandit` 與 `pip-audit` 工作  
- 產生 SBOM 並保存於 `dist/` 或作為 release artifact

中期（數週）：
- `docs/threat-model.md`（使用 STRIDE 或 PASTA，包含資料流程圖與信任邊界）  
- `docs/security-requirements.md` 與 `docs/security-design.md`  
- 撰寫安全測試（fuzzing、邊界輸入測試、授權測試）

長期（發行治理）：
- 發行簽章或 checksum 並記錄發行流程  
- 正式 CVE 分級與修補流程、SLA  30/60/90 天分級範例  
- 定期第三方滲透測試或安全評估

## 建議的 CI 整合範例工作

- `security-deps`: 執行 `pip-audit`，若發現高危 CVE 則失敗  
- `security-sast`: 執行 `bandit`，對高嚴重度問題 fail  
- `sbom`: 產生 SBOM 並上傳為 artifact

## 如果你要我接手的下一步（可選）

1. 立即產生 SBOM 並加入 repo（或作為 artifact）。  
2. 新增 `SECURITY.md` 與 `docs/threat-model.md` 範本。  
3. 在 `.github/workflows/` 新增 GitHub Actions，執行 `pip-audit`、`bandit` 與 SBOM 產生。

---

檔案由專案安全評估助手自動建立。
