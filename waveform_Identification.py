import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import numpy as np

def read_data(file_path):
    try:
        xls = pd.ExcelFile(file_path, engine='openpyxl')
        sheets = xls.sheet_names
        data = {sheet: xls.parse(sheet) for sheet in sheets}
        return data
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        return None
    except ValueError as e:
        print(f"Value error reading {file_path}: {e}")
        return None
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return None

def prepare_data(data):
    X, y = [], []
    for sheet_name, df in data.items():
        if len(df) > 0:
            features = df.iloc[:, 1].values.flatten()
            label = df.iloc[0, 2]
            X.append(features)
            y.append(label)
    return X, y

def pad_and_normalize_features(X, max_length):
    padded_X = []
    lengths = []
    for features in X:
        if len(features) < max_length:
            padded_features = np.pad(features, (0, max_length - len(features)), 'constant')
        else:
            padded_features = features[:max_length]
        padded_X.append(padded_features)
        lengths.append(len(features))
    padded_X = np.array(padded_X)

    lengths = np.array(lengths).reshape(-1, 1)
    final_X = np.hstack([padded_X, lengths])

    scaler = StandardScaler()
    final_X = scaler.fit_transform(final_X)

    return final_X, scaler

def train_model(X, y):
    y = np.array(y)
    if not np.issubdtype(y.dtype, np.integer):
        raise ValueError("Labels are not discrete classes. Please provide discrete class labels.")

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    print(f"Model accuracy: {model.score(X_test, y_test)}")
    return model

def predict_and_save(model, file_path, max_length, scaler):
    data = read_data(file_path)
    if data is None:
        return

    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')

    for sheet_name, df in data.items():
        if len(df) > 0:
            features = df.iloc[:, 1].values.flatten()
            if len(features) < max_length:
                padded_features = np.pad(features, (0, max_length - len(features)), 'constant')
            else:
                padded_features = features[:max_length]
            length = np.array([len(features)])
            final_features = np.hstack([padded_features, length])
            final_features = scaler.transform([final_features])[0]
            prediction = model.predict([final_features])[0]
            df.iloc[0, 2] = prediction  # Update the label in the third column
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    writer.close()

def main():
    train_files = [
        r'C:\Users\dell\Desktop\training_data\training_data_1.xlsx',
        r'C:\Users\dell\Desktop\training_data\training_data_2.xlsx'
    ]
    test_file = r'C:\Users\dell\Desktop\training_data\test_data.xlsx'

    all_data = {}
    for file in train_files:
        data = read_data(file)
        if data:
            all_data[file] = data

    X, y = [], []
    for data in all_data.values():
        Xi, yi = prepare_data(data)
        X.extend(Xi)
        y.extend(yi)

    max_length = max(len(features) for features in X)
    X, scaler = pad_and_normalize_features(X, max_length)

    model = train_model(X, y)

    predict_and_save(model, test_file, max_length, scaler)

if __name__ == "__main__":
    main()