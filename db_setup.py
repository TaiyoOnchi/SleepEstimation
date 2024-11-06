import sqlite3

def init_db():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()

    # 学生テーブルを作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_number TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            kana_last_name TEXT NOT NULL,
            kana_first_name TEXT NOT NULL,
            face_photo BLOB NOT NULL,
            gender BOOLEAN NOT NULL,
            is_active BOOLEAN NOT NULL,
            right_eye_baseline REAL NOT NULL,
            left_eye_baseline REAL NOT NULL
        )
    ''')

    # 開眼率データ保存用テーブル（ユーザーごとに最新3件だけ保持）
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS eye_openness (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            right_eye_openness REAL,
            left_eye_openness REAL,
            FOREIGN KEY (student_id) REFERENCES students(id)
        )
    ''')

    # 教員テーブルを作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS teachers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_number TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            last_name TEXT NOT NULL,
            first_name TEXT NOT NULL,
            kana_last_name TEXT NOT NULL,
            kana_first_name TEXT NOT NULL
        )
    ''')

    # 講義テーブルを作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            subject_name TEXT NOT NULL,
            default_room TEXT NOT NULL,
            default_day_of_week TEXT NOT NULL,
            default_period INTEGER NOT NULL,
            max_eor_value INTEGER NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers (id)
        )
    ''')
    
    # 講義回テーブルを作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subject_counts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_id INTEGER NOT NULL,
            room TEXT NOT NULL,
            day_of_week TEXT NOT NULL,
            period INTEGER NOT NULL,
            start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            end_time DATETIME DEFAULT CURRENT_TIMESTAMP,
            is_active BOOLEAN NOT NULL,
            FOREIGN KEY (subject_id) REFERENCES subjects (id)
        )
    ''')

    # クラステーブルを作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_subjects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id INTEGER NOT NULL,
            subject_id INTEGER NOT NULL,
            average_eor REAL,
            total_sleep_time TIME,
            total_attention INTEGER,
            total_warnings INTEGER,
            FOREIGN KEY (student_id) REFERENCES students(id),
            FOREIGN KEY (subject_id) REFERENCES subjects(id)
        )
    ''')
    
    

    # 講義回テーブルを作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS student_participations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_subject_id INTEGER NOT NULL,
            subject_count_id INTEGER NOT NULL,
            session_number INTEGER,
            seat_number INTEGER,
            average_eor REAL,
            attendance_time DATETIME,
            exit_time DATETIME,
            attention_count INTEGER,
            warning_count INTEGER,
            FOREIGN KEY (student_subject_id) REFERENCES student_subjects(id),
            FOREIGN KEY (subject_count_id) REFERENCES subject_counts(id)
        )
    ''')

    # 注意テーブルを作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS attentions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_participation_id INTEGER NOT NULL,
            attention_count INTEGER,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_participation_id) REFERENCES student_participations(id)
        )
    ''')

    # 警告テーブルを作成
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS warnings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_participation_id INTEGER NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            reason TEXT,
            FOREIGN KEY (student_participation_id) REFERENCES student_participations(id)
        )
    ''')

    conn.commit()
    conn.close()
