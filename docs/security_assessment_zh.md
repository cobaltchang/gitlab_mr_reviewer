````markdown
# 安全評估 — SSDLC / CRA / IEC 62443 差距分析

日期：2026-01-22

## 目的

本文件記錄一次簡明的安全差距分析與修復建議，協助本倉庫對齊 SSDLC 要求以及相關工業標準（如 CRA、IEC 62443）。

## 高階發現

- 專案具良好工程習慣：有規格文件、測試、對 `src` 的 100% 覆蓋率及貢獻指引。
- 但缺少 CRA / IEC 62443 常見的若干安全生命週期產物（詳見下方差距清單）。

## 差距摘要

1. 安全需求規格（Security requirements）— 未建立。
2. 威脅建模 / 風險評估 — 未建立。
3. 軟體材料清單（SBOM）生成 — 專案中無穩定 SBOM。
4. 相依性漏洞掃描與 CVE 追蹤 — CI 中尚未自動化執行。
5. 專注於安全的靜態分析（SAST）— 只有一般 linters，未完整導入 `bandit`。
6. 安全測試案例 / 整合測試（安全情境）— 缺乏相關測試。
7. 漏洞通報與事件回應政策 — 未建立 `SECURITY.md`。
8. 發行完整性（簽章 / 校驗）— 未建立。
9. 設計與架構的安全文件（資料流程、信任邊界）— 不完整。
10. 變更/補丁管理與 CVE 分級流程— 尚未制度化。

## 對應 IEC 62443（摘要）

- SR-2（威脅建模）：缺失
- SVV-1 / SVV-2（安全驗證/測試）：缺乏自動化安全測試
- DM-1 / DM-2（缺陷與更新管理）：部分（有 git 歷史）但無正式 SLA 或流程

## 快速動作建議（工具與命令）

1. 產生 SBOM（CycloneDX）：

```bash
pip install cyclonedx-bom
cyclonedx-py -r requirements.txt -o sbom.json
```

2. 相依性稽核：

```bash
pip install pip-audit
pip-audit
```

3. 靜態安全掃描：

```bash
pip install bandit
bandit -r src/ -ll
```

4. 在 pre-merge / PR 流程加入 `pip-audit`、`bandit` 與 SBOM 產生步驟。

## 優先交付項目（建議順序）

短期（數日）：
- 新增 `SECURITY.md`（漏洞通報、聯絡方式、SLA）
- 將 `bandit` 與 `pip-audit` 加入 CI
- 產生 SBOM 並於 release 時附上或儲存為 artifact

中期（數週）：
- 撰寫 `docs/threat-model.md`（STRIDE/PASTA，資料流程與邊界）
- 撰寫 `docs/security-requirements.md` 與 `docs/security-design.md`
- 建置安全測試（fuzzing、輸入驗證、權限測試）

長期（發行治理）：
- 發行簽章或校驗機制；文件化發行流程
- 正式 CVE 分級與修補流程（含 SLA）
- 定期第三方審查或滲透測試

## 建議 CI 整合（範例工作項）

- `security-deps`：執行 `pip-audit` 並在發現問題時失敗
- `security-sast`：執行 `bandit` 並對高嚴重性問題失敗
- `sbom`：產生並儲存 SBOM 為 artifact

## 下一步（如需我協助）

1. 我可新增 `SECURITY.md` 與 `docs/threat-model.md` 範本至此倉庫。  
2. 我可新增 GitHub Actions workflow，在 push 時執行 `pip-audit`、`bandit` 並產生 SBOM。  
3. 我亦可立即產生 SBOM 並 commit（如你要求）。

---

此檔案由存倉安全評估助理生成。

````
