import sqlite3

def add_column_to_attentions():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    # attentionsテーブルにis_correctカラムを追加
    try:
        cursor.execute('''
            ALTER TABLE attentions ADD COLUMN is_correct BOOLEAN DEFAULT TRUE
        ''')
        print("カラム 'is_correct' を追加しました（デフォルト: TRUE）。")
    except sqlite3.OperationalError as e:
        print(f"エラー: {e}")
    
    # 既存のデータに対してTRUEを設定
    try:
        cursor.execute('''
            UPDATE attentions
            SET is_correct = TRUE
            WHERE is_correct IS NULL
        ''')
        print("既存のデータにTRUEを設定しました。")
    except sqlite3.OperationalError as e:
        print(f"エラー: {e}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    add_column_to_attentions()


# def update_attentions_table():
#     conn = sqlite3.connect('users.db')
#     cursor = conn.cursor()

#     # ステップ 1: 現在のデータをバックアップ
#     cursor.execute('''
#         CREATE TABLE IF NOT EXISTS attentions_backup AS
#         SELECT * FROM attentions
#     ''')
#     print("バックアップテーブル 'attentions_backup' を作成しました。")

#     # ステップ 2: 元のテーブルを削除
#     cursor.execute('DROP TABLE attentions')
#     print("元のテーブル 'attentions' を削除しました。")

#     # ステップ 3: 新しい構成でテーブルを作成
#     cursor.execute('''
#         CREATE TABLE attentions (
#             id INTEGER PRIMARY KEY AUTOINCREMENT,
#             student_participation_id INTEGER NOT NULL,
#             timestamp DATETIME NOT NULL,
#             sleep_time TIME DEFAULT '00:00:00' NOT NULL,
#             is_correct BOOLEAN DEFAULT TRUE NOT NULL,
#             FOREIGN KEY (student_participation_id) REFERENCES student_participations(id)
#         )
#     ''')
#     print("新しい構成で 'attentions' テーブルを作成しました。")

#     # ステップ 4: データをバックアップから移行
#     cursor.execute('''
#         INSERT INTO attentions (id, student_participation_id, timestamp, sleep_time, is_correct)
#         SELECT id, student_participation_id, timestamp, sleep_time, COALESCE(is_correct, TRUE)
#         FROM attentions_backup
#     ''')
#     print("データをバックアップテーブルから新しいテーブルに移行しました。")

#     # バックアップテーブルを削除（必要に応じて）
#     cursor.execute('DROP TABLE attentions_backup')
#     print("バックアップテーブル 'attentions_backup' を削除しました。")

#     conn.commit()
#     conn.close()
#     print("テーブル構造の更新が完了しました。")

# if __name__ == "__main__":
#     update_attentions_table()
