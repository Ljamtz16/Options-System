from src.options_system.calibration import fit_platt,apply_platt,fit_temperature,apply_temperature
def test_platt_bounds():
 p=apply_platt(fit_platt([.1,.2,.8,.9],[0,0,1,1],steps=500),[.01,.5,.99]);assert all(0<x<1 for x in p)
def test_temperature_bounds():
 p=apply_temperature(fit_temperature([.1,.2,.8,.9],[0,0,1,1],steps=500),[.01,.5,.99]);assert all(0<x<1 for x in p)
