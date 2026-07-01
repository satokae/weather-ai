import numpy as np
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import TensorDataset, DataLoader
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report

# Set random seeds for reproducibility
np.random.seed(42)
torch.manual_seed(42)

# Constants
WINDOW_SIZE = 12  # past 12 hours of data
BATCH_SIZE = 64
EPOCHS = 30
LEARNING_RATE = 0.003
DEVICE = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

# Mapping for Japanese wind directions to angles (in degrees)
WIND_DIR_ANGLES = {
    "北": 0.0, "北北東": 22.5, "北東": 45.0, "東北東": 67.5,
    "東": 90.0, "東南東": 112.5, "南東": 135.0, "南南東": 157.5,
    "南": 180.0, "南南西": 202.5, "南西": 225.0, "西南西": 247.5,
    "西": 270.0, "西北西": 292.5, "北西": 315.0, "北北西": 337.5,
}

# Weather code mapping (0: Sunny, 1: Cloudy, 2: Rainy)
WEATHER_MAPPING = {2: 0, 4: 1, 10: 2}

def load_and_preprocess_data(csv_paths):
    dfs = []
    for csv_path in csv_paths:
        print(f"Loading raw data from {csv_path}...")
        # Skip first 5 rows (metadata and headers)
        df_year = pd.read_csv(csv_path, encoding='shift_jis', skiprows=5, header=None)
        df_year.columns = [
            'year', 'month', 'day', 'hour', 'dew_point',
            'weather_code', 'temperature', 'wind_speed',
            'wind_direction', 'pressure'
        ]
        dfs.append(df_year)

    df = pd.concat(dfs, ignore_index=True)

    # 1. Fill missing/empty numeric values to maintain time-series continuity
    numeric_cols = ['temperature', 'dew_point', 'pressure', 'wind_speed']
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors='coerce')
        df[col] = df[col].ffill().bfill()  # Forward and backward fill

    # 2. Compute Engineered Features
    df['depression'] = df['temperature'] - df['dew_point']
    df['press_grad'] = df['pressure'] - df['pressure'].shift(3)
    df['press_grad'] = df['press_grad'].ffill().bfill()  # Fill initial NaNs

    # 3. Parse wind direction to continuous vector components
    def get_wind_components(row):
        dir_str = row['wind_direction']
        speed = row['wind_speed']
        if dir_str in WIND_DIR_ANGLES:
            rad = np.deg2rad(WIND_DIR_ANGLES[dir_str])
            return speed * np.sin(rad), speed * np.cos(rad)
        return 0.0, 0.0  # Includes "静穏" (Calm) and other unparseable states

    wind_vectors = df.apply(get_wind_components, axis=1)
    df['wind_x'] = [w[0] for w in wind_vectors]
    df['wind_y'] = [w[1] for w in wind_vectors]

    # 4. Cyclical Time encoding
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24.0)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24.0)

    # Cyclical Date encoding (Day of Year)
    for col in ['year', 'month', 'day']:
        df[col] = pd.to_numeric(df[col], errors='coerce').astype(int)
    date_series = pd.to_datetime(df[['year', 'month', 'day']])
    day_of_year = date_series.dt.dayofyear
    days_in_year = np.where(date_series.dt.is_leap_year, 366.0, 365.0)
    df['doy_sin'] = np.sin(2 * np.pi * day_of_year / days_in_year)
    df['doy_cos'] = np.cos(2 * np.pi * day_of_year / days_in_year)

    # 5. Extract features for standardizing
    feature_cols = [
        'temperature', 'pressure', 'depression', 'press_grad',
        'wind_x', 'wind_y', 'hour_sin', 'hour_cos', 'doy_sin', 'doy_cos'
    ]

    # Scale features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df[feature_cols])

    # 6. Build sliding windows
    print("Constructing sliding window sequences...")
    X, y = [], []
    for i in range(WINDOW_SIZE - 1, len(df)):
        # Target label at current hour
        w_code = df.iloc[i]['weather_code']

        # Check if the current weather is one of our target classes
        if pd.isna(w_code) or int(w_code) not in WEATHER_MAPPING:
            continue

        # Feature window from t - WINDOW_SIZE + 1 to t
        window = scaled_features[i - WINDOW_SIZE + 1 : i + 1]

        X.append(window)
        y.append(WEATHER_MAPPING[int(w_code)])

    return np.array(X, dtype=np.float32), np.array(y, dtype=np.int64)

# Define 1D CNN Architecture
class WeatherCNN1D(nn.Module):
    def __init__(self, num_features=8, num_classes=3):
        super(WeatherCNN1D, self).__init__()

        # Input shape: (Batch, Features, WindowSize)
        self.conv_block1 = nn.Sequential(
            nn.Conv1d(in_channels=num_features, out_channels=32, kernel_size=3, padding=1),
            nn.BatchNorm1d(32),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2)
        )

        self.conv_block2 = nn.Sequential(
            nn.Conv1d(in_channels=32, out_channels=64, kernel_size=3, padding=1),
            nn.BatchNorm1d(64),
            nn.ReLU(),
            nn.MaxPool1d(kernel_size=2)
        )

        # Input WindowSize=12.
        # After block1 pool: 12 / 2 = 6
        # After block2 pool: 6 / 2 = 3 (taking floor/standard pooling)
        self.fc_block = nn.Sequential(
            nn.Flatten(),
            nn.Linear(64 * 3, 64),
            nn.ReLU(),
            nn.Dropout(0.3),
            nn.Linear(64, num_classes)
        )

    def forward(self, x):
        # PyTorch Conv1D expects: (Batch, Channels/Features, Length/Time)
        # Input shape from DataLoader: (Batch, Length, Features) -> Permute to (Batch, Features, Length)
        x = x.permute(0, 2, 1)
        x = self.conv_block1(x)
        x = self.conv_block2(x)
        logits = self.fc_block(x)
        return logits

def main():
    # Load and preprocess data
    csv_paths = ['data/2023.csv', 'data/2024.csv', 'data/2025.csv']
    X, y = load_and_preprocess_data(csv_paths)

    # Train / Test split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f"Dataset Size: Train={len(X_train)}, Test={len(X_test)}")

    # Build DataLoaders
    train_dataset = TensorDataset(torch.tensor(X_train), torch.tensor(y_train))
    test_dataset = TensorDataset(torch.tensor(X_test), torch.tensor(y_test))

    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=BATCH_SIZE, shuffle=False)

    # Initialize Model, Optimizer, and Loss
    model = WeatherCNN1D(num_features=X.shape[2], num_classes=3).to(DEVICE)
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=LEARNING_RATE)

    print(f"\nTraining WeatherCNN1D on {DEVICE}...")
    for epoch in range(1, EPOCHS + 1):
        model.train()
        running_loss = 0.0
        correct = 0
        total = 0

        for batch_x, batch_y in train_loader:
            batch_x, batch_y = batch_x.to(DEVICE), batch_y.to(DEVICE)

            optimizer.zero_grad()
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            loss.backward()
            optimizer.step()

            running_loss += loss.item() * batch_x.size(0)
            _, predicted = outputs.max(1)
            total += batch_y.size(0)
            correct += predicted.eq(batch_y).sum().item()

        epoch_loss = running_loss / len(train_loader.dataset)
        epoch_acc = correct / total

        # Evaluate on test set
        model.eval()
        test_loss = 0.0
        test_correct = 0
        test_total = 0

        with torch.no_grad():
            for batch_x, batch_y in test_loader:
                batch_x, batch_y = batch_x.to(DEVICE), batch_y.to(DEVICE)
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)

                test_loss += loss.item() * batch_x.size(0)
                _, predicted = outputs.max(1)
                test_total += batch_y.size(0)
                test_correct += predicted.eq(batch_y).sum().item()

        val_loss = test_loss / len(test_loader.dataset)
        val_acc = test_correct / test_total

        if epoch % 5 == 0 or epoch == 1:
            print(f"Epoch {epoch:2d}/{EPOCHS} | Train Loss: {epoch_loss:.4f} | Train Acc: {epoch_acc*100:.2f}% | Test Loss: {val_loss:.4f} | Test Acc: {val_acc*100:.2f}%")

    # Final Evaluation & Classification Report
    model.eval()
    all_preds = []
    all_targets = []

    with torch.no_grad():
        for batch_x, batch_y in test_loader:
            batch_x = batch_x.to(DEVICE)
            outputs = model(batch_x)
            _, preds = outputs.max(1)
            all_preds.extend(preds.cpu().numpy())
            all_targets.extend(batch_y.numpy())

    print("\n" + "="*50)
    print("FINAL TEST EVALUATION REPORT")
    print("="*50)
    target_names = ['Sunny', 'Cloudy', 'Rainy']
    print(classification_report(all_targets, all_preds, target_names=target_names))

if __name__ == '__main__':
    main()
