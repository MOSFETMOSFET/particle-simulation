import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import os


def read_data(file_path):

    xls = pd.ExcelFile(file_path)
    sheets = xls.sheet_names
    data = {sheet: xls.parse(sheet) for sheet in sheets}
    return data


def prepare_data(data):

    X, y = [], []
    for sheet_name, df in data.items():
        if len(df) > 0:
            X.extend(df.iloc[:, 1].values)
            y.extend(df.iloc[:, 2].values)
    return pd.DataFrame(X), pd.DataFrame(y)


def train_model(X, y):

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier()
    model.fit(X_train, y_train)
    print(f"Model accuracy: {model.score(X_test, y_test)}")
    return model


def predict_and_save(model, file_path):

    data = read_data(file_path)
    writer = pd.ExcelWriter(file_path, engine='xlsxwriter')

    for sheet_name, df in data.items():
        if len(df) > 0:
            predictions = model.predict(df.iloc[:, 1].values.reshape(-1, 1))
            df.iloc[0, 2] = predictions[0]
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    writer.save()


def main():
    train_files = ['train_file1.xlsx', 'train_file2.xlsx']
    test_file = 'test_file.xlsx'

    all_data = {file: read_data(file) for file in train_files}
    X, y = [], []
    for data in all_data.values():
        Xi, yi = prepare_data(data)
        X.append(Xi)
        y.append(yi)

    X = pd.concat(X)
    y = pd.concat(y)

    model = train_model(X, y)

    predict_and_save(model, test_file)


if __name__ == "__main__":
    main()