import pandas as pd

df = pd.read_csv("accepted_2007_to_2018Q4.csv.gz", compression="gzip", low_memory=False, nrows=1000)

print(f"Columnas: {len(df.columns)}")
print(f"Filas (muestra): {len(df)}")
print("\nPrimeras columnas:")
print(df.columns.tolist()[:30])
print("\nPrimeras filas:")
print(df.head(3))
