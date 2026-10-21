from sqlalchemy import create_engine, text

engine = create_engine('postgresql+psycopg2://postgres:Cogolludo01@127.0.0.1/credit_risk')

try:
    with engine.connect() as conn:
        result = conn.execute(text('SELECT version()'))
        print('Conexion OK:', result.fetchone()[0])
except Exception as e:
    print(f'Error: {e}')