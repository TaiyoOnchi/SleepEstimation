SleepEstimation/<br>
  ├ app/<br>
  │  ├ events/  # 開眼率基準値、講義中の開眼率を計測する処理<br>
  │  ├ eye_openness/  # 開眼率の測定方法、保存<br>
  │  ├ models/  # 学生、教員のクラスを定義するファイル<br>
  │  ├ routes/  # Flaskのルーティングを管理するフォルダ<br>
  │  ├ templates/  # HTMLテンプレートファイルを格納するフォルダ<br>
  │  └ utils/  # データ処理や汎用的な機能が格納されているフォルダ<br>
  ├ .gitignore  # Gitで管理しないファイルやフォルダを指定する設定ファイル<br>
  ├ config.py  # プロジェクトの設定ファイル<br>
  ├ db_setup.py  # データベースの初期設定を行うスクリプト<br>
  ├ requirements.txt  # プロジェクトで使用するPythonパッケージのリスト<br>
  ├ run.py  # アプリケーションのエントリーポイント<br>
  └ shape_predictor_68_face_landmarks.dat  # dlibの68個の顔のランドマークを検出するための学習済みモデルデータ<br>
