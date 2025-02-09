import sqlite3

def revert_is_correct():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # 1: 現在のデータをバックアップ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attentions_backup AS
        SELECT * FROM attentions
    ''')
    print("バックアップテーブル 'attentions_backup' を作成しました。")

    # 2: 元のテーブルを削除
    cursor.execute('DROP TABLE attentions')
    print("元のテーブル 'attentions' を削除しました。")

    # 3: 新しい構成でテーブルを作成（is_wrong → is_correct に変更）
    cursor.execute('''
        CREATE TABLE attentions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_participation_id INTEGER NOT NULL,
            timestamp DATETIME NOT NULL,
            sleep_time TIME NOT NULL DEFAULT '00:00:00',
            is_correct BOOLEAN NOT NULL DEFAULT TRUE,  -- is_correct に戻す
            reason INTEGER NOT NULL DEFAULT 0 CHECK(reason IN (0, 1, 2)),
            FOREIGN KEY (student_participation_id) REFERENCES student_participations(id)
        )
    ''')
    print("新しい構成で 'attentions' テーブルを作成しました。")

    # 4: データをバックアップから移行（is_wrong を is_correct に戻す）
    cursor.execute('''
        INSERT INTO attentions (id, student_participation_id, timestamp, sleep_time, is_correct, reason)
        SELECT id, student_participation_id, timestamp, sleep_time, is_wrong, reason
        FROM attentions_backup
    ''')
    print("データをバックアップテーブルから新しいテーブルに移行しました。")

    # 5: バックアップテーブルを削除（必要に応じて）
    cursor.execute('DROP TABLE attentions_backup')
    print("バックアップテーブル 'attentions_backup' を削除しました。")

    conn.commit()
    conn.close()
    print("テーブル構造の更新が完了しました。")

# 実行
revert_is_correct()
