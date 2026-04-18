import pandas as pd

# Load your dataset (change filename if needed)
df = pd.read_csv("backend/datasets/compass.csv")

# Columns you want to keep
columns_to_keep = [
    "sex",
    "age",
    "race",
    "juv_fel_count",
    "juv_misd_count",
    "priors_count",
    "c_charge_degree",
    "two_year_recid"
]

# Select only those columns
df_cleaned = df[columns_to_keep]

# Save the cleaned dataset
df_cleaned.to_csv("cleaned_dataset.csv", index=False)

print("Done! Cleaned dataset saved as 'cleaned_dataset.csv'")