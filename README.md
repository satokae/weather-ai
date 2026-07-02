# Weather AI

```
$ uv run main.py
```

```
Epoch  1/30 | Train Loss: 0.7375 | Train Acc: 64.08% | Test Loss: 0.6726 | Test Acc: 67.71%
Epoch  5/30 | Train Loss: 0.6057 | Train Acc: 72.48% | Test Loss: 0.5909 | Test Acc: 72.78%
Epoch 10/30 | Train Loss: 0.5576 | Train Acc: 75.02% | Test Loss: 0.5724 | Test Acc: 74.08%
Epoch 15/30 | Train Loss: 0.5137 | Train Acc: 77.05% | Test Loss: 0.5600 | Test Acc: 74.98%
Epoch 20/30 | Train Loss: 0.4853 | Train Acc: 78.42% | Test Loss: 0.5682 | Test Acc: 75.53%
Epoch 25/30 | Train Loss: 0.4523 | Train Acc: 79.61% | Test Loss: 0.5724 | Test Acc: 75.28%
Epoch 30/30 | Train Loss: 0.4351 | Train Acc: 81.03% | Test Loss: 0.5698 | Test Acc: 75.43%

==================================================
FINAL TEST EVALUATION REPORT
==================================================
              precision    recall  f1-score   support

       Sunny       0.78      0.86      0.82      2601
      Cloudy       0.70      0.65      0.67      1962
       Rainy       0.81      0.67      0.73       680

    accuracy                           0.75      5243
   macro avg       0.76      0.72      0.74      5243
weighted avg       0.75      0.75      0.75      5243
```

## データ

データ出典：気象庁ホームページ [過去の気象データ](https://www.data.jma.go.jp/risk/obsdl/#)

### 地点

- 浜松

### 項目

- 気温
- 露点温度
- 風向・風速
- 現地気圧
- 天気

### 期間（日本標準時）

- 2023年1月1日から
- 2023年12月31日まで

- 2024年1月1日から
- 2024年12月31日まで

- 2025年1月1日から
- 2025年12月31日まで

の時別値を表示

### オプション

- 利用上注意が必要なデータを表示させない
- 観測環境などの変化以前のデータを表示させない
- ダウンロードデータはすべて数値で格納
