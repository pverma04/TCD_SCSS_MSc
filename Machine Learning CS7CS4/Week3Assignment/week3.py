import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import Lasso
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from sklearn.linear_model import Ridge
from sklearn.model_selection import KFold, cross_val_score




#skip first line
df = pd.read_csv("week3.csv", comment='#', header=None)
print(df.head())
print("Shape:", df.shape)

X = df.iloc[:, 0:2].values #input matrix
y = df.iloc[:, 2].values #target

#-----------Part i-----------

#part i(a)
print("i(a)")
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')
ax.scatter(X[:, 0], X[:, 1], y, color='blue', label='training data')
ax.set_xlabel("x1")
ax.set_ylabel("x2")
ax.set_zlabel("target y")
ax.set_xticks([-1, -0.5, 0, 0.5, 1])
ax.set_yticks([-1, -0.5, 0, 0.5, 1])
ax.set_title("i(a) Training data")
ax.legend()
plt.savefig("i_a_3d_scatter.png", dpi=150)
#plt.show()

#part i(b)
print("i(b)")
#all combinations of x1 x2 deg<=5
poly = PolynomialFeatures(degree=5, include_bias=False)
X_poly = poly.fit_transform(X)
feature_names = poly.get_feature_names_out(['x1', 'x2'])
print(len(feature_names), "features:", list(feature_names))

#smallest C with all-zero Lasso weights
n = len(y)
X_centered = X_poly - X_poly.mean(axis=0)
alpha_max = np.max(np.abs(X_centered.T @ (y - y.mean()))) / n
C_zero = 1 / (2 * alpha_max)
print("All parameters are zero for C <=", C_zero)

#train model per each C val (for sklearn: alpha = 1/(2C))
C_values = [0.01, 0.1, 1, 10, 100, 1000]
lasso_models = {}
results = {}
for C in C_values:
    model = Lasso(alpha=1 / (2 * C), max_iter=100000)
    model.fit(X_poly, y)
    lasso_models[C] = model
    results[f"C={C}"] = np.append(model.intercept_, model.coef_)

table = pd.DataFrame(results, index=["intercept"] + list(feature_names))
pd.set_option("display.width", 200)
print(table.round(3))
print("Non-zero weights per C:", {C: int(np.sum(lasso_models[C].coef_ != 0)) for C in C_values})

#part i(c)
print("i(c)")

C_plot = [1, 10, 100, 1000]

#test points, beyond [-1, 1]
grid = np.linspace(-2, 2, 50)
G1, G2 = np.meshgrid(grid, grid)
X_test = np.column_stack((G1.ravel(), G2.ravel()))
X_test_poly = poly.transform(X_test)

for C in C_plot:
    y_grid = lasso_models[C].predict(X_test_poly).reshape(G1.shape)

    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(G1, G2, y_grid, color='orange', alpha=0.5)
    ax.scatter(X[:, 0], X[:, 1], y, color='blue')
    ax.set_zlim(-3, 6) #stops extreme extrapolations
    ax.set_xlabel("x1"); ax.set_ylabel("x2"); ax.set_zlabel("target y")
    ax.set_title(f"Lasso predictions, C={C}")
    ax.legend(handles=[Patch(color='orange', alpha=0.5, label='predictions'),
                       Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', label='training data')])
    plt.savefig(f"i_c_lasso_C{C}.png", dpi=150)
    #plt.show()
print("Lasso non-zero:", {C: int(np.sum(lasso_models[C].coef_ != 0)) for C in C_values})
print("Lasso sum |w|:", {C: round(float(np.sum(np.abs(lasso_models[C].coef_))), 3) for C in C_values})


#part i(d)
print("i(d)")
print("only in report")

#part i(e) repeat b-c
print("i(e)")

#part(b) for Ridge
C_ridge = [0.001, 0.01, 0.1, 1, 10, 100, 1000]
ridge_models = {}
ridge_results = {}
for C in C_ridge:
    model = Ridge(alpha=1 / (2 * C))
    model.fit(X_poly, y)
    ridge_models[C] = model
    ridge_results[f"C={C}"] = np.append(model.intercept_, model.coef_)

ridge_table = pd.DataFrame(ridge_results, index=["intercept"] + list(feature_names))
print(ridge_table.round(3))
print("Weights with |value| > 1e-6:", {C: int(np.sum(np.abs(ridge_models[C].coef_) > 1e-6)) for C in C_ridge})
print("Sum of |weights|:", {C: round(float(np.sum(np.abs(ridge_models[C].coef_))), 3) for C in C_ridge})

#part(c) for Ridge
for C in [0.01, 1, 100, 1000]:
    y_grid = ridge_models[C].predict(X_test_poly).reshape(G1.shape)
    fig = plt.figure(figsize=(8, 7))
    ax = fig.add_subplot(111, projection='3d')
    ax.plot_surface(G1, G2, y_grid, color='orange', alpha=0.3)
    ax.scatter(X[:, 0], X[:, 1], y, color='blue')
    ax.set_zlim(-3, 6)
    ax.set_xticks([-2, -1, 0, 1, 2]); ax.set_yticks([-2, -1, 0, 1, 2])
    ax.view_init(elev=20, azim=-60)
    ax.set_xlabel("x1"); ax.set_ylabel("x2"); ax.set_zlabel("target y")
    ax.set_title(f"Ridge predictions, C={C}")
    ax.legend(handles=[Patch(color='orange', alpha=0.3, label='predictions'),
                       Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', label='training data')])
    plt.savefig(f"i_e_ridge_C{C}.png", dpi=150)
    #plt.show()


#-----------Part ii-----------

#part ii(a)
print("ii(a)")

kf = KFold(n_splits=5, shuffle=True, random_state=0)
C_cv = np.logspace(-1, 3, 20)   # 0.1 to 1000
cv_mean, cv_std = [], []
for C in C_cv:
    model = Lasso(alpha=1 / (2 * C), max_iter=100000)
    scores = cross_val_score(model, X_poly, y, cv=kf, scoring='neg_mean_squared_error')
    mse = -scores
    cv_mean.append(mse.mean())
    cv_std.append(mse.std())

plt.figure(figsize=(8, 6))
plt.errorbar(C_cv, cv_mean, yerr=cv_std, fmt='o-', capsize=4)
plt.xscale('log')
plt.xlabel("C")
plt.ylabel("mean square error (5-fold CV)")
plt.title("ii(a): Lasso: cross-validated error vs C")
plt.savefig("ii_a_lasso_cv.png", dpi=150)
plt.show()

best = int(np.argmin(cv_mean))
print("Lowest mean CV error at C =", C_cv[best], "with MSE", cv_mean[best])
#table
for C, m, s in zip(C_cv, cv_mean, cv_std):
    print(f"C={C:8.2f}  mean MSE={m:.4f}  std={s:.4f}")

#part ii(b)
print("ii(b)")
print("only in report")

#part ii(c) repeat for Ridge regression
print("ii(c)")

C_cv_ridge = np.logspace(-4, 3, 25) #0.0001 to 1000
ridge_mean, ridge_std = [], []
for C in C_cv_ridge:
    model = Ridge(alpha=1 / (2 * C))
    scores = cross_val_score(model, X_poly, y, cv=kf, scoring='neg_mean_squared_error')
    mse = -scores
    ridge_mean.append(mse.mean())
    ridge_std.append(mse.std())

plt.figure(figsize=(8, 6))
plt.errorbar(C_cv_ridge, ridge_mean, yerr=ridge_std, fmt='o-', capsize=4)
plt.xscale('log')
plt.xlabel("C")
plt.ylabel("mean square error (5-fold CV)")
plt.title("ii(c): Ridge: cross-validated error vs C")
plt.savefig("ii_c_ridge_cv.png", dpi=150)
plt.show()

best = int(np.argmin(ridge_mean))
print("Lowest mean CV error at C =", C_cv_ridge[best], "with MSE", ridge_mean[best])
for C, m, s in zip(C_cv_ridge, ridge_mean, ridge_std):
    print(f"C={C:10.4f}  mean MSE={m:.4f}  std={s:.4f}")