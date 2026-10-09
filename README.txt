AI先生 Windows最新版

【起動方法】
1. PowerShellを開く
2. AI先生_Windows最新版 のフォルダへ移動
3. 初回だけ:
   python -m pip install -r requirements.txt
4. APIキーを設定:
   $env:OPENAI_API_KEY="あなたのAPIキー"
5. 起動:
   python server.py
6. ブラウザで:
   http://127.0.0.1:5000

【重要】
- APIキーは index.html に書かないでください。
- PowerShellを閉じるとサーバーも終了します。
- Enterキーでは「AI先生に質問」を送信しません。送信ボタンを押してください。
- AI利用にはOpenAI APIの利用可能なアカウント/APIキーが必要です。
