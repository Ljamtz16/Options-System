import math
def wilson_interval(k,n,z=1.96):
 if n<=0:return (None,None)
 p=k/n;d=1+z*z/n;c=(p+z*z/(2*n))/d
 h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d
 return max(0,c-h),min(1,c+h)
def conservative_probability(p,bin_event_rate=None,bin_n=0,min_bin_n=30):
 if bin_event_rate is None or bin_n<min_bin_n:return min(p,0.5)
 lo,_=wilson_interval(round(bin_event_rate*bin_n),bin_n)
 return min(p,lo)
