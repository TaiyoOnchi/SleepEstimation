SleepEstimation/<br>
  ├ app/<br>
  │  ├ events/  # 開眼率基準値、講義中の開眼率を計測する処理<br>
  │  │  ├ baseline_measure.py  # 開眼率基準値の測定
  │  │  ├ eye_openness_monitor.py  # 講義中の開眼率測定
  │  ├ eye_openness/  # 開眼率の測定方法、保存
  │  ├ models/  # 学生、教員のクラスを定義するファイル
  │  ├ routes/  # Flaskのルーティングを管理するフォルダ
  │  ├ templates/  # HTMLテンプレートファイルを格納するフォルダ
  │  └ utils/  # データ処理や汎用的な機能が格納されているフォルダ
  ├ .gitignore  # Gitで管理しないファイルやフォルダを指定する設定ファイル
  ├ config.py  # プロジェクトの設定ファイル
  ├ db_setup.py  # データベースの初期設定を行うスクリプト
  ├ requirements.txt  # プロジェクトで使用するPythonパッケージのリスト
  ├ run.py  # アプリケーションのエントリーポイント
  └ shape_predictor_68_face_landmarks.dat  # dlibの68個の顔のランドマークを検出するための学習済みモデルデータ
