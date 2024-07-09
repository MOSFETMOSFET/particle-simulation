import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import os
import numpy as np

file_path = r'C:\Users\dell\Desktop\training_data\waveform_data_with_labels.xlsx'


def read_data(file_path):
    xls = pd.ExcelFile(file_path)
    sheets = xls.sheet_names
    data = {sheet: xls.parse(sheet) for sheet in sheets}
    return data


def prepare_data(data):
    X, y = [], []
    for sheet_name, df in data.items():
        if len(df) > 0:
            features = df.iloc[0, 2:].values.flatten()
            length = len(features)
            label = df.iloc[0, 1]
            X.append((features, length))
            y.append(label)
    return X, y


def pad_and_normalize_features(X, max_length):
    padded_X = []
    lengths = []
    for features, length in X:
        if len(features) < max_length:
            padded_features = np.pad(features, (0, max_length - len(features)), 'constant')
        else:
            padded_features = features[:max_length]
        padded_X.append(padded_features)
        lengths.append(length)
    padded_X = np.array(padded_X)

    scaler = StandardScaler()
    padded_X = scaler.fit_transform(padded_X)

    lengths = np.array(lengths).reshape(-1, 1)
    lengths = scaler.fit_transform(lengths)

    final_X = np.hstack([padded_X, lengths])
    return final_X


def train_model(X, y):
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    print(f"Model accuracy: {model.score(X_test, y_test)}")
    return model


def predict_and_save(model, file_path, max_length, scaler):
    data = read_data(file_path)
    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')

    for sheet_name, df in data.items():
        if len(df) > 0:
            features = df.iloc[0, 2:].values.flatten()
            length = len(features)
            if len(features) < max_length:
                padded_features = np.pad(features, (0, max_length - len(features)), 'constant')
            else:
                padded_features = features[:max_length]
            padded_features = scaler.transform([padded_features])[0]
            length = scaler.transform([[length]])[0]
            final_features = np.hstack([padded_features, length])
            prediction = model.predict([final_features])[0]
            df.iloc[0, 1] = prediction
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    writer.save()


def main():
    train_files = [
        r'C:\Users\dell\Desktop\training_data\train_file1.xlsx',
        r'C:\Users\dell\Desktop\training_data\train_file2.xlsx'
    ]
    test_file = r'C:\Users\dell\Desktop\training_data\test_file.xlsx'

    all_data = {file: read_data(file) for file in train_files}
    X, y = [], []
    for data in all_data.values():
        Xi, yi = prepare_data(data)
        X.extend(Xi)
        y.extend(yi)

    max_length = max(len(features) for features, _ in X)
    X = pad_and_normalize_features(X, max_length)

    model = train_model(X, y)

    scaler = StandardScaler()
    scaler.fit(X[:, :-1])

    predict_and_save(model, test_file, max_length, scaler)


if __name__ == "__main__":
    main()