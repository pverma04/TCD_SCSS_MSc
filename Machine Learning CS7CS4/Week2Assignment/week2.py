import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.svm import LinearSVC


#load data
df = pd.read_csv("week2.csv", comment='#', header=None)
print(df.head())
x1 = df.iloc[:, 0]
x2 = df.iloc[:, 1]
x = np.column_stack((x1, x2))
y=df.iloc[:, 2]

#-----PART A-----
#part a(i)

#plot: 
# x axis: be the value of the first feature
# y-axis the value of the second feature
# the marker: a + marker when target = +1, and a o when target = -1

#+ points
plt.scatter(x1[y==1], x2[y==1], marker='+', color='blue', label='target = +1')
 #- points
plt.scatter(x1[y==-1], x2[y==-1], marker='o', color='green', label='target = -1')
#label
plt.xlabel('x1')
plt.ylabel('x2')
plt.title('a(i) Training Data Distribution')
plt.legend()
plt.savefig('a(i)_plot.png')
#comment out for testing purposes
#plt.show()

#part a(ii)
#train logistic regression model
lr = LogisticRegression()
lr.fit(x, y)
print("Intercept (theta0):", lr.intercept_)
print("Coefficients (theta1, theta2):", lr.coef_)
#Coefficients (theta1, theta2): [[0.09983397 3.42504821]]
# Theta2 is much larger, thus x2 has a greater influence on the decision boundary than x1.


#part a(iii)
#predict target values, show desicion boundary

#predict on training data
y_pred = lr.predict(x)
plt.figure(figsize=(8, 6))

#include part a(i) plot
plt.scatter(x1[y==1], x2[y==1], marker='+', color='blue', label='target = +1')
plt.scatter(x1[y==-1], x2[y==-1], marker='o', color='green', label='target = -1')

#predictions, new markers/colors
plt.scatter(x1[y_pred==1], x2[y_pred==1], marker='x', color='red', label='predicted = +1')
plt.scatter(x1[y_pred==-1], x2[y_pred==-1], marker='s', color='orange', label='predicted = -1')

#decision boundary
#decision boundary: theta0 + theta1*x1 + theta2*x2 = 0
#solve for x2: x2 = -(theta0 + theta1*x1)/theta2
theta0 = lr.intercept_[0]
theta1 = lr.coef_[0][0]
theta2 = lr.coef_[0][1]

x1_range = np.linspace(x1.min(), x1.max(), 100)    
x2_range = -(theta0 + theta1 * x1_range)/theta2

plt.plot(x1_range, x2_range, color='black', linewidth=2, label='Decision Boundary')
plt.xlabel('x1')
plt.ylabel('x2')
plt.title('a(iii) Logistic Regression Predictions, Decision Boundary, with Actual Data')
plt.legend()
plt.savefig('a(iii)_plot.png')
#comment out for testing purposes
#plt.show()

#part a(iv)
acc = accuracy_score(y, y_pred)
print("Training accuracy:", acc)

print()

#-----PART B-----
#part b(i)
#train linear SVM model at various C values 
C_values = [0.001, 1, 100]
svm_models = {}
for C in C_values:
    svm = LinearSVC(C=C, max_iter=10000)
    svm.fit(x, y)
    svm_models[C] = svm
    print("Intercept:", svm.intercept_)
    print("Coefficients:", svm.coef_)
    print(f"Trained Linear SVM with C={C}")
    print()

#part b(ii)
#use each of these trained classifiers to predict the target values in the training
#data. Plot these predictions and the actual target values from the data, together
#with the classifier decision boundary.

#use each classifier to predict target values and plot with actual target values and decision boundary
for C in C_values:
    svm = svm_models[C]
    y_pred_svm = svm.predict(x)
    
    plt.figure(figsize=(8, 6))

    #actual target values
    plt.scatter(x1[y==1], x2[y==1], marker='+', color='blue', label='target = +1')
    plt.scatter(x1[y==-1], x2[y==-1], marker='o', color='green', label='target = -1')
    
    #predicted target values
    plt.scatter(x1[y_pred_svm==1], x2[y_pred_svm==1], marker='x', color='red', label='predicted = +1')
    plt.scatter(x1[y_pred_svm==-1], x2[y_pred_svm==-1], marker='s', color='orange', label='predicted = -1')
    
    #decision boundary
    theta0_svm = svm.intercept_[0]
    theta1_svm = svm.coef_[0][0]
    theta2_svm = svm.coef_[0][1]
    x1_range = np.linspace(x1.min(), x1.max(), 100)
    x2_range_svm = -(theta0_svm + theta1_svm * x1_range)/theta2_svm
    plt.plot(x1_range, x2_range_svm, color='black', linewidth=2, label=f'Decision Boundary (C={C})')


    plt.xlabel('x1')
    plt.ylabel('x2')
    plt.title(f'b(ii) Linear SVM Predictions, Decision Boundary, with Actual Data (C={C})')
    plt.legend()
    plt.savefig(f'b(ii)_plot_C_{C}.png')
    #comment out for testing purposes
    #plt.show()
    acc = accuracy_score(y, y_pred_svm)
    print(f"C={C}: training accuracy = {acc}")


#-----PART C-----
#part c(i)
#add square of each feature
#train classifier

#create additional features
x1_sq = x1**2
x2_sq = x2**2
x_q = np.column_stack((x1, x2, x1_sq, x2_sq))

lr_q = LogisticRegression()
lr_q.fit(x_q, y)
print("Intercept (theta0):", lr_q.intercept_)
print("Coefficients (theta1, theta2, theta3, theta4):", lr_q.coef_)

#part c(ii)
#predict target values
y_pred_q = lr_q.predict(x_q)
plt.figure(figsize=(8, 6))
#actual
plt.scatter(x1[y==1], x2[y==1], marker='+', color='blue', label='target = +1')
plt.scatter(x1[y==-1], x2[y==-1], marker='o', color='green', label='target = -1')
#predicted
plt.scatter(x1[y_pred_q==1], x2[y_pred_q==1], marker='x', color='red', label='predicted = +1')
plt.scatter(x1[y_pred_q==-1], x2[y_pred_q==-1], marker='s', color='orange', label='predicted = -1')   

plt.xlabel('x1')
plt.ylabel('x2')
plt.title('c(ii) Logistic Regression with Polynomial Features Predictions, with Actual Data')
plt.legend()
plt.savefig('c(ii)_plot.png')
#comment out for testing purposes
plt.show()

acc_q = accuracy_score(y, y_pred_q)
print("Training accuracy with polynomial features:", acc_q) 
