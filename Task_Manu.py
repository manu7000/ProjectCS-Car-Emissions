import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import mean_squared_error

# Load dataset with necessary columns
df = pd.read_csv("all-vehicles-model@public.csv", usecols=["Fuel Type1", "Cylinders", "Year", "Co2 Tailpipe For Fuel Type1"])

# Drop rows with missing values
df.dropna(subset=["Fuel Type1", "Cylinders", "Year", "Co2 Tailpipe For Fuel Type1"], inplace=True)

# Encode categorical 'Fuel Type1'
le = LabelEncoder()
df["Fuel Type1"] = le.fit_transform(df["Fuel Type1"])

# Features and target
X = df[["Fuel Type1", "Cylinders", "Year"]]
y = df["Co2 Tailpipe For Fuel Type1"]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train the decision tree model
model = DecisionTreeRegressor(random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print("MSE:", mean_squared_error(y_test, y_pred))