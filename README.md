# DICOM Series 複製工具

這是一個基於 Python 與 tkinter 製作的圖形化工具，方便醫療人員從 DICOM 資料夾中選取指定影像 series，並根據影像描述自動建立資料夾進行複製。特別適合需要整理、搬移或篩選特定 series 的使用情境。

---

## 🖥️ 功能特色

- 📂 **DICOM 資料夾載入與 lazy 掃描**  
  僅在點選最下層資料夾後才進行影像讀取，避免一次性掃描造成卡頓。

- 🔎 **Series 即時搜尋與過濾**  
  可依照描述、來源資料夾、日期等關鍵字過濾 Series。

- 🎞️ **預覽影像**  
  自動顯示每個 series 的中央張影像，並可使用滑鼠滾輪瀏覽上下張。

- 📊 **讀取進度條**  
  掃描過程中顯示進度，提升使用者體驗。

- 🧳 **一鍵複製選取 series**  
  每個 series 會依命名規則建立一個獨立資料夾，並保留原始相對路徑結構。

- ✍️ **複製資料夾命名選項**  
  - 使用原始 Series 描述  
  - 自訂命名  
  - 自訂 prefix + 原始描述  

- ❌ **合法路徑自動處理**  
  將非法字元（如 `<>:"/\\|?*`）自動轉為 `_`，避免複製失敗。

---

## 📸 使用預覽

（請於 GitHub 上補上截圖）

---

## 📦 安裝方式

### ✅ 環境需求

- Python 3.8 或以上
- 支援 Windows / macOS / Linux
- 建議使用虛擬環境（venv）

### ✅ 安裝相當套件

```bash
pip install pydicom pillow
```

---

## ▶️ 執行方式

```bash
python DICOMSeriesCopier.py
```

開啟應用程式後：

1. 點選「載入 DICOM 資料夾」
2. 選擇最下層資料夾，即可顯示該資料夾中所有影像 series
3. 可使用搜尋欄過濾
4. 選取欲複製的 series，點選「複製選取的 Series」
5. 選擇命名方式與輸出資料夾，系統將自動建立資料夾並複製對應檔案

---

## 🚀 打包為可執行檔（Windows）

若需提供給未安裝 Python 的使用者，可使用 `pyinstaller` 打包：

```bash
pip install pyinstaller
pyinstaller --noconsole --onefile DICOMSeriesCopier.py
```

生成的 `.exe` 檔將位於 `dist/` 資料夾中。

---

## 📁 複製輸出結構

複製後的檔案結構如下：

```
<輸出路徑>/
├— <原始子資料夾>/
│   └— <Series描述或命名>/
│       ├— image1.dcm
│       ├— image2.dcm
│       └— ...
```

---

## 🛠 TODO 功能

- [ ] 匯出影像為 PNG / JPEG
- [ ] 支援拖書資料夾導入
- [ ] 加入 DICOM tag 過濾（如 Modality、StudyDate）
- [ ] 支援匿名化功能（anonymize DICOM）
- [ ] 多語系切換（繁體中文 / English）
- [ ] 支援右鍵選單與滑鼠拖選
- [ ] 支援檔案總算器中開啟後拖書顯示 series preview

---

## 🙌 作者與授權
作者: Yen-Ju Chu (e-mail:mantour.tw@gmail.com)
本專案採用 [MIT License](LICENSE) 授權，歡迎自由使用、修改與散佈。

