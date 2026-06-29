import psycopg2

def get_connection():

    return psycopg2.connect(

        host="localhost",

        database="agriculture_system",

        user="postgres",

        password="كلمة_مرور_PostgreSQL"

    )