import psycopg2

conn = psycopg2.connect(host='localhost', dbname='db_tests', user='onalone', password='q1w2e3r4', port=5432)
cur = conn.cursor()

cur.execute("""CREATE TABLE IF NOT EXISTS tasks (task_id BIGSERIAL PRIMARY KEY, user_id INT, task_desc TEXT);""")

conn.commit()
cur.close()
conn.close()




