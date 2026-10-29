import os
import pandas as pd
from sklearn.impute import SimpleImputer

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATASET_DIR = os.path.join(BASE_DIR, "dataset")

# LOAD DATASET

data = pd.read_csv(os.path.join(DATASET_DIR, "student_learning_pathway1_data.csv"))

print("DATASET LOADED SUCCESSFULLY")
print(data.head())

# REMOVE DUPLICATES

data = data.drop_duplicates()

# REMOVE EXTRA SPACES FROM COLUMN NAMES

data.columns = data.columns.str.strip()

# CLEAN TEXT VALUES

# STANDARDIZE GENDER COLUMN
data['Gender'] = data['Gender'].astype(str).str.strip().str.capitalize()

# STANDARDIZE TARGET COLUMN
data['Recommended_Stream'] = (
    data['Recommended_Stream']
    .astype(str)
    .str.strip()
    .str.capitalize()
)

# CONVERT COLUMNS TO NUMERIC

numerical_columns = [
    'Math_Marks',
    'Science_Marks',
    'Arts_Marks',
    'Study_Hours_Per_Week'
]

for col in numerical_columns:
    data[col] = pd.to_numeric(data[col], errors='coerce')

# CHECK MISSING VALUES

print("\nMISSING VALUES:")
print(data.isnull().sum())

# HANDLE MISSING NUMERICAL VALUES

num_imputer = SimpleImputer(strategy='mean')

data[numerical_columns] = num_imputer.fit_transform(
    data[numerical_columns]
)

# HANDLE MISSING GENDER VALUES

cat_imputer = SimpleImputer(strategy='most_frequent')

data[['Gender']] = cat_imputer.fit_transform(
    data[['Gender']]
)

# REMOVE ROWS WHERE TARGET IS MISSING

data = data.dropna(subset=['Recommended_Stream'])

# REMOVE INVALID MARK VALUES

data = data[
    (data['Math_Marks'] >= 0) &
    (data['Math_Marks'] <= 100) &

    (data['Science_Marks'] >= 0) &
    (data['Science_Marks'] <= 100) &

    (data['Arts_Marks'] >= 0) &
    (data['Arts_Marks'] <= 100)
]

# ROUND DECIMAL VALUES TO WHOLE NUMBERS

# COLUMNS TO ROUND
round_columns = [
    'Math_Marks',
    'Science_Marks',
    'Arts_Marks',
    'Study_Hours_Per_Week'
]

# ROUND VALUES
data[round_columns] = data[round_columns].round(0)

# CONVERT TO INTEGER
data[round_columns] = data[round_columns].astype(int)



# REMOVE INVALID STUDY HOURS

data = data[
    (data['Study_Hours_Per_Week'] >= 0) &
    (data['Study_Hours_Per_Week'] <= 80)
]

# KEEP ONLY VALID GENDER VALUES

data = data[
    data['Gender'].isin(['Male', 'Female'])
]

# KEEP ONLY VALID STREAM VALUES

data = data[
    data['Recommended_Stream'].isin(
        ['Technical', 'Academic']
    )
]

# RESET INDEX

data = data.reset_index(drop=True)

# SAVE CLEANED DATASET

data.to_csv(
    os.path.join(DATASET_DIR, "fully_cleaned_student_pathway_data.csv"),
    index=False
)

# FINAL OUTPUT

print("\nDATA CLEANING COMPLETED SUCCESSFULLY")

print("\nFINAL DATASET SHAPE:")
print(data.shape)

print("\nFIRST 5 ROWS:")
print(data.head())