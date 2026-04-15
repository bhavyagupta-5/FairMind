import pandas as pd
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split

class DataPreprocessor:

    def load(self, file_path: str) -> pd.DataFrame:
        df = pd.read_csv(file_path)
        return df

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        # Drop rows where ALL values are null
        df = df.dropna(how='all')
        # Fill remaining nulls
        for col in df.columns:
            if df[col].dtype in ['float64', 'int64']:
                df[col] = df[col].fillna(df[col].median())
            else:
                df[col] = df[col].fillna(df[col].mode()[0])
        # Strip whitespace from string columns
        for col in df.select_dtypes(include='object').columns:
            df[col] = df[col].str.strip()
        return df

    def encode(self, df: pd.DataFrame, exclude_cols: list) -> pd.DataFrame:
        """Label-encode all categorical columns except those in exclude_cols."""
        df = df.copy()
        le = LabelEncoder()
        for col in df.select_dtypes(include='object').columns:
            if col not in exclude_cols:
                df[col] = le.fit_transform(df[col].astype(str))
        return df

    def split(self, df: pd.DataFrame, target_col: str, test_size=0.3):
        X = df.drop(columns=[target_col])
        y = df[target_col]
        return train_test_split(X, y, test_size=test_size, random_state=42)