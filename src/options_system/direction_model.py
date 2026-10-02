import math
def sigmoid(z):
 if z>=0:return 1/(1+math.exp(-z))
 e=math.exp(z);return e/(1+e)
def fit_logistic(X,y,steps=1200,lr=.05,l2=.001):
 n=len(y);p=len(X[0]);w=[0.0]*(p+1)
 for _ in range(steps):
  g=[0.0]*(p+1)
  for row,t in zip(X,y):
   pr=sigmoid(w[0]+sum(a*b for a,b in zip(w[1:],row)));e=pr-t;g[0]+=e
   for j,x in enumerate(row):g[j+1]+=e*x
  for j in range(len(w)):
   reg=0 if j==0 else l2*w[j];w[j]-=lr*(g[j]/n+reg)
 return w
def predict(w,X):return [sigmoid(w[0]+sum(a*b for a,b in zip(w[1:],r))) for r in X]
def brier(y,p):return sum((a-b)**2 for a,b in zip(y,p))/len(y)
def logloss(y,p):
 eps=1e-12;return -sum(t*math.log(max(eps,min(1-eps,q)))+(1-t)*math.log(max(eps,min(1-eps,1-q))) for t,q in zip(y,p))/len(y)
