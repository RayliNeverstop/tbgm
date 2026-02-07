# 手機版部署指南 (Android)

本指南涵蓋了從打包 Python/Flet 應用程式、測試廣告功能，到上傳至 Google Play 商店的完整流程。

## ⚠️ 重要：WSL 檔案系統權限需知

**不要在 `/mnt/c/` (Windows 掛載路徑) 下直接打包！**
由於 Windows 與 Linux 檔案權限機制不同，Buildozer 在 `/mnt/c/` 下操作 git 或 chmod 時會發生 `Operation not permitted` 錯誤。
**解決方案**：請務必將專案複製到 WSL 的 Linux 家目錄 (`~`) 下再進行打包。

## 第一階段：環境架設 (Windows 使用者)

打包 Android APK 需要 Linux 環境。在 Windows 上，我們使用 WSL2 (Windows Subsystem for Linux)。

1.  **安裝 WSL2**：
    請在 PowerShell (以系統管理員身分執行) 輸入：
    ```powershell
    wsl --install
    ```
    *如果系統提示重新啟動，請重開機。*

2.  **設定環境 (開啟 WSL 終端機)**：
    輸入以下指令來更新並安裝必要的套件 (已針對 Ubuntu 24.04 調整)：
    ```bash
    # 更新列表
    sudo apt update

    # 安裝 pip
    sudo apt install -y python3-pip

    # 安裝依賴庫
    sudo apt install -y build-essential git python3-dev \
        libssl-dev libffi-dev libsqlite3-dev openjdk-17-jdk \
        autoconf libtool pkg-config zlib1g-dev libncurses-dev \
        libncursesw5-dev cmake libffi-dev zip unzip \
        autopoint gettext

    # 設定 PATH
    echo 'export PATH=$PATH:~/.local/bin' >> ~/.bashrc
    source ~/.bashrc

    # 安裝 Buildozer
    pip3 install --user buildozer cython --break-system-packages
    ```

## 第二階段：正確的打包流程 (將專案移入 WSL)

這是最關鍵的一步，請依照以下指令操作：

1.  **在 WSL 中建立工作目錄並複製專案**：
    (假設您的 Windows 專案在桌面，請依照您的實際路徑調整)
    ```bash
    # 回到 Linux 家目錄
    cd ~
    
    # 建立一個資料夾
    mkdir build_tbgm
    
    # 將 Windows 桌面的檔案複製過來 (請替換 rayli 為您的使用者名稱)
    cp -r /mnt/c/Users/rayli/Desktop/self_learning/GM/TBGM/antigravityu/* ~/build_tbgm/
    
    # 進入該目錄
    cd ~/build_tbgm
    ```

2.  **開始打包**：
    現在您位於 Linux 原生檔案系統中，權限問題將不再出現。
    由於 Ubuntu 24.04 的限制，我們需要加入環境變數來允許 Buildozer 安裝內部依賴：
    ```bash
    PIP_BREAK_SYSTEM_PACKAGES=1 buildozer android debug
    ```
    *第一次執行會下載 Android NDK/SDK，可能需要 15-30 分鐘。*

## 第三階段：廣告串接 (AdMob)

在打包之前，確保您已設定：

1.  **`buildozer.spec`**：
    ```ini
    android.meta_data = com.google.android.gms.ads.APPLICATION_ID=ca-app-pub-您的APP-ID~...
    ```

2.  **`controllers/ad_manager.py`**：
    ```python
    self.BANNER_ID = "ca-app-pub-您的單元-ID/..."
    ```

## 第四階段：實機測試

打包成功後，APK 會生成在 `~/build_tbgm/bin/`。

1.  **將 APK 複製回 Windows 桌面 (方便安裝)**：
    ```bash
    cp ~/build_tbgm/bin/*.apk /mnt/c/Users/rayli/Desktop/
    ```

2.  **安裝到手機**：
    在 Windows 上使用 `adb install` 安裝剛剛複製出來的 APK。

## 第五階段：雲端存檔與上架

(參考先前的指南內容，此處流程相同)

---
**疑難排解**：
- **Operation not permitted (chmod/git)**：您還是在 `/mnt/c` 下操作。請務必執行 `cp` 指令將專案搬到 `~` (家目錄) 下。
- **externally-managed-environment**：使用 `pip3 install ... --break-system-packages`。
- **SyntaxError: f-string: unmatched '('**：這是 Python 3.12 的新語法導致舊版工具鏈不相容。
  解決方法：
  1. 在 `buildozer.spec` 中指定 Python 版本：`requirements = python3==3.11.6, ...`
  2. 清除全域快取 (如果不清會繼續用舊的)：`rm -rf ~/.buildozer`
  3. 重新打包。
