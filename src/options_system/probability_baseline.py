import math
def sigmoid(z):
    z=max(-35,min(35,z));return 1/(1+math.exp(-z))
def fit_standardizer(X):
    n=len(X);p=len(X[0]);mu=[sum(r[j] for r in X)/n for j in range(p)]
    sd=[math.sqrt(sum((r[j]-mu[j])**2 for r in X)/n) or 1.0 for j in range(p)]
    return mu,sd
def transform(X,mu,sd):return [[(r[j]-mu[j])/sd[j] for j in range(len(mu))] for r in X]
def fit_logistic(X,y,l2=.1,lr=.03,steps=4000):
    n=len(X);p=len(X[0]);w=[0.0]*p;b=math.log((sum(y)+.5)/(n-sum(y)+.5))
    for _ in range(steps):
        ps=[sigmoid(b+sum(w[j]*x[j] for j in range(p))) for x in X]
        gb=sum(ps[i]-y[i] for i in range(n))/n
        gw=[sum((ps[i]-y[i])*X[i][j] for i in range(n))/n+l2*w[j] for j in range(p)]
        b-=lr*gb
        for j in range(p):w[j]-=lr*gw[j]
    return {"w":w,"b":b}
def predict(model,X):return [sigmoid(model["b"]+sum(a*b for a,b in zip(model["w"],x))) for x in X]
def metrics(y,p):
    eps=1e-12;n=len(y);pred=[v>=.5 for v in p]
    return {"n":n,"accuracy":sum(pred[i]==bool(y[i]) for i in range(n))/n,
      "brier":sum((p[i]-y[i])**2 for i in range(n))/n,
      "logloss":-sum(y[i]*math.log(max(eps,p[i]))+(1-y[i])*math.log(max(eps,1-p[i])) for i in range(n))/n,
      "mean_p":sum(p)/n,"event_rate":sum(y)/n}
