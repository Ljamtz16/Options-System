from src.options_system.probability_baseline import fit_standardizer,transform,fit_logistic,predict,metrics
def test_train_only_standardizer():
 X=[[0.],[2.]];mu,sd=fit_standardizer(X);assert mu==[1.0]
 assert transform([[101.]],mu,sd)[0][0]==100.0
def test_logistic_learns_direction():
 X=[[-2.],[-1.],[1.],[2.]];y=[0,0,1,1];m=fit_logistic(X,y,l2=.01,steps=2000)
 p=predict(m,X);assert p[0]<p[-1] and metrics(y,p)["accuracy"]==1
