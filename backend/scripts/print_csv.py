import pandas as pd

csv_path = "train.csv"

df = pd.read_csv(
    csv_path,
    encoding="utf-8",
    on_bad_lines="skip"
)

print(df.head(10))
print(df.columns.tolist())