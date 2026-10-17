import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split, StratifiedKFold, cross_val_score
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier



#-------PART I-------

#data set up

df = pd.read_csv("week4_1.csv", comment='#', header=None)
print(df.head())
print("Shape:", df.shape)

X = df.iloc[:, 0:2].values
y = df.iloc[:, 2].values

print("Class counts:", dict(zip(*np.unique(y, return_counts=True))))
print("Fraction of +1:", np.mean(y == 1))
plt.figure(figsize=(8, 6))
plt.scatter(X[y == 1, 0], X[y == 1, 1], marker = '+', color='blue', label='target = +1')
plt.scatter(X[y == -1, 0], X[y == -1, 1], marker = 'o', color='red', label='target = -1')
plt.xlabel('x1')
plt.ylabel('x2')
plt.title('Dataset 1: training data')
plt.legend()
plt.tight_layout()
plt.savefig('dataset1.png', dpi=300)
plt.show()

#part i(a)
print("Part i(a)")
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, stratify = y, random_state = 0)
skf = StratifiedKFold(n_splits=5, shuffle=True, random_state = 0)
degrees = range(1, 9)
C_list = np.logspace(-3, 3, 13)

results = {}
for d in degrees:
    means, stds = [], []
    for C in C_list:
        model = make_pipeline(
            PolynomialFeatures(degree=d, include_bias=False),
            StandardScaler(),
            LogisticRegression(C=C, max_iter=10000))
        scores = cross_val_score(model, X_train, y_train, cv=skf, scoring='accuracy')
        means.append(scores.mean())
        stds.append(scores.std())
    results[d] = (np.array(means), np.array(stds))
    best = np.argmax(means)
    print(f"degree {d}: best C={C_list[best]:.3g}, CV accuracy={means[best]:.4f} +/- {stds[best]:.4f}")

baseline = np.mean(y_train == 1)
print("Always-predict-/+1 accuracy on training portion:", round(baseline, 4))

plt.figure(figsize=(8, 6))
for d in [1, 2, 3, 5, 8]:
    plt.errorbar(C_list, results[d][0], yerr=results[d][1], fmt='o-', capsize=3, label=f"degree {d}")
plt.axhline(baseline, color='black', linestyle='--', label='always predict +1')
plt.xscale('log')
plt.xlabel("C (inverse penalty weight)")
plt.ylabel("CV accuracy (5-fold)")
plt.title("Logistic regression: CV accuracy vs C")
plt.legend(loc='upper left', bbox_to_anchor=(1.02, 1))
plt.tight_layout()
plt.savefig("i_a_cv.png", dpi=150)
plt.show()    

log_model = make_pipeline(
    PolynomialFeatures(degree=1, include_bias=False),
    StandardScaler(),
    LogisticRegression(C=0.001, penalty='l2', max_iter=10000)
)

log_model.fit(X_train, y_train)

print("Logistic Regression Training Accuracy:",
      log_model.score(X_train, y_train))
print("Logistic Regression Test Accuracy:",
      log_model.score(X_test, y_test))

print("Predicted Class Counts:",
      np.unique(log_model.predict(X_test), return_counts=True))

x1_grid = np.linspace(X[:, 0].min(), X[:, 0].max(), 300)
x2_grid = np.linspace(X[:, 1].min(), X[:, 1].max(), 300)
xx, yy = np.meshgrid(x1_grid, x2_grid)
grid = np.c_[xx.ravel(), yy.ravel()]
predictions = log_model.predict(grid).reshape(xx.shape)

plt.figure(figsize=(8, 6))

plt.contourf(xx, yy, predictions,
             levels=[-1.5, 0, 1.5],
             alpha=0.25)

plt.scatter(X_train[y_train == 1, 0],
            X_train[y_train == 1, 1],
            marker='+', color='blue', label='Actual +1')

plt.scatter(X_train[y_train == -1, 0],
            X_train[y_train == -1, 1],
            marker='o', color='red', label='Actual -1')

plt.xlabel('x1')
plt.ylabel('x2')
plt.title('Dataset 1: Logistic Regression Predictions')
plt.legend()
plt.tight_layout()
plt.savefig('i_a_predictions.png', dpi=300)
plt.show()

#part i(b)
print("Part i(b)")

k_values = range(1, 51)
means, stds = [], []
for k in k_values:
    model = make_pipeline(
        StandardScaler(),
        KNeighborsClassifier(n_neighbors=k)
    )
    scores = cross_val_score(model, X_train, y_train, cv=skf, scoring='accuracy')
    means.append(scores.mean())
    stds.append(scores.std())
best_index = np.argmax(means)
best_k = k_values[best_index]
print("Best k value:", best_k)
print("Best CV accuracy:", means[best_index])
print("CV standard deviation:", stds[best_index])

#cross validation accuracy plot
plt.figure(figsize=(8, 6))
plt.errorbar(k_values, means, yerr=stds, fmt='o-', capsize=3, markersize=4, label='kNN')
plt.axhline(baseline, color='black', linestyle='--', label='Majority baseline')

plt.xlabel('Number of neighbors (k)')
plt.ylabel('CV accuracy (5-fold)')
plt.title('Dataset 1: kNN Cross-Validation')
plt.legend()
plt.tight_layout()
plt.savefig('i_b_cv.png', dpi=300)
plt.show()

#final kNN model
knn_model = make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=best_k))
knn_model.fit(X_train, y_train)

print("kNN training accuracy:", knn_model.score(X_train, y_train))
print("kNN test accuracy:", knn_model.score(X_test, y_test))
print("Predicted class counts:", np.unique(knn_model.predict(X_test), return_counts=True))

#kNN predictions plot
predictions_knn = knn_model.predict(grid).reshape(xx.shape)

plt.figure(figsize=(8, 6))
plt.contourf(xx, yy, predictions_knn, levels=[-1.5, 0, 1.5], alpha=0.25)
plt.scatter(X_train[y_train == 1, 0], X_train[y_train == 1, 1], marker='+', color='blue', label='Actual +1')
plt.scatter(X_train[y_train == -1, 0], X_train[y_train == -1, 1], marker='o', color='red', label='Actual -1')

plt.xlabel('x1')
plt.ylabel('x2')
plt.title(f'Dataset 1: kNN Predictions (k={best_k})')
plt.legend()
plt.tight_layout()
plt.savefig('i_b_predictions.png', dpi=300)
plt.show()

