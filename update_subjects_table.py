import sqlite3

def update_subjects_table():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # 1: 現在のデータをバックアップ
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects_backup AS
        SELECT * FROM subjects
    ''')
    print("バックアップテーブル 'subjects_backup' を作成しました。")

    # 2: 元のテーブルを削除
    cursor.execute('DROP TABLE subjects')
    print("元のテーブル 'subjects' を削除しました。")

    # 3: 新しい構成でテーブルを作成
    cursor.execute('''
        CREATE TABLE subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            subject_name TEXT NOT NULL,
            default_classroom TEXT NOT NULL,
            default_day_of_week TEXT NOT NULL,
            default_period INTEGER NOT NULL,
            eor_threshold INTEGER NOT NULL, 
            FOREIGN KEY (teacher_id) REFERENCES teachers (id)
        )
    ''')
    print("新しい構成で 'subjects' テーブルを作成しました。")

    # 4: データをバックアップから移行
    cursor.execute('''
        INSERT INTO subjects (id, teacher_id, subject_name, default_classroom, default_day_of_week, default_period, eor_threshold)
        SELECT id, teacher_id, subject_name, default_classroom, default_day_of_week, default_period, ero_threshold
        FROM subjects_backup
    ''')
    print("データをバックアップテーブルから新しいテーブルに移行しました。")

    # バックアップテーブルを削除（必要に応じて）
    cursor.execute('DROP TABLE subjects_backup')
    print("バックアップテーブル 'subjects_backup' を削除しました。")

    conn.commit()
    conn.close()
    print("テーブル構造の更新が完了しました。")

if __name__ == "__main__":
    update_subjects_table()
