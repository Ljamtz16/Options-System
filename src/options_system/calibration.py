import math
def clip(p,eps=1e-6): return min(1-eps,max(eps,p))
def logit(p): p=clip(p);return math.log(p/(1-p))
def sigmoid(z): z=max(-35,min(35,z));return 1/(1+math.exp(-z))
def fit_platt(prob,y,l2=.01,lr=.03,steps=4000):
 x=[logit(p) for p in prob];a=1.0;b=0.0;n=len(y)
 for _ in range(steps):
  q=[sigmoid(a*x[i]+b) for i in range(n)]
  ga=sum((q[i]-y[i])*x[i] for i in range(n))/n+l2*(a-1)
  gb=sum(q[i]-y[i] for i in range(n))/n
  a-=lr*ga;b-=lr*gb
 return {"kind":"platt","a":a,"b":b}
def apply_platt(model,prob):return [sigmoid(model["a"]*logit(p)+model["b"]) for p in prob]
def fit_temperature(prob,y,lr=.02,steps=3000):
 x=[logit(p) for p in prob];s=0.0;n=len(y)
 for _ in range(steps):
  t=math.exp(s);q=[sigmoid(v/t) for v in x]
  g=sum((q[i]-y[i])*(-x[i]/t) for i in range(n))/n
  s-=lr*g
 return {"kind":"temperature","temperature":math.exp(s)}
def apply_temperature(model,prob):
 t=model["temperature"];return [sigmoid(logit(p)/t) for p in prob]
