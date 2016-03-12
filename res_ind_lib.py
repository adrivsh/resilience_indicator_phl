import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

def compute_resiliences(df_in, fa_ratios=None, multihazard_data =None):
    """Main function. Computes all outputs (dK, resilience, dC, etc,.) from inputs"""

    df=df_in.copy()
    
    #blends multihazard data
    dfh = broadcast_hazard(multihazard_data, df)
   
    #interpolate fa rations and blends far ratios data
    fa_ratios = interpolate_faratios(fa_ratios, df_in.protection.unique().tolist())
    dfhr = broadcast_return_periods(fa_ratios, dfh)
   
    #computes dk_{hazard, return} and dW_{hazard, return}
    dkdwhr=compute_dK_dW(dfhr)
    
    #dk_{hazard} and dW_{hazard}
    dkdwh = average_over_rp(dkdwhr,dfhr["protectionref"])
    
    #Sums over hazard dk, dW
    dkdw = sum_over_hazard(dkdwh)

    #adds dk and dw-like columns to df
    df[dkdw.columns]=dkdw
    
    #computes socio economic capacity and risk
    df = calc_risk_and_resilience_from_k_w(df)

    return df
    
def broadcast_hazard(hazard_info, df_in):    
    if hazard_info is None:
        return df_in
    
    hazard_info=hazard_info.reset_index()
    
    hazard_list = hazard_info.hazard.unique()
    
    nb_hazards =len(hazard_list)
    df = pd.concat(
        [df_in]*nb_hazards,
        axis=1, keys=hazard_list, names=["hazard","var"]
        ).stack("hazard").sort_index().sortlevel()#.reset_index("hazard")
    
    # copies multi hazard info in the casted dataframe
    mh = hazard_info.set_index(["province","hazard"])
    df[mh.columns]=mh
    
    return df.dropna()
    
    
def broadcast_return_periods(fa_ratios, df_in):    
    #builds a dataframe "multi-indexed" by return period  ((province,rp), var)
    
    if fa_ratios is None:
        return df_in
    
    nrps =len(fa_ratios.columns)
    df = pd.concat(
        [df_in.copy(deep=True)]*nrps,
        axis=1, keys=fa_ratios.columns, names=["rp","var"]
        ).swaplevel("var","rp",axis=1).sortlevel(0,axis=1).stack("rp")#Reshapes into ((province,rp), vars) 
    
    #introduces different exposures for different return periods
    df["fap"]=df["fap"]*fa_ratios.stack("rp")
    df["far"]=df["far"]*fa_ratios.stack("rp")
    
    
    # df=df#.reset_index("rp")#.set_index(["province","rp"])
    
    return df.dropna()
    


def compute_dK_dW(df):  
    '''Computes dk and dW line by line.
    presence of multiple return period or multihazard data is transparent to this function'''    

    
    # # # # # # # # # # # # # # # # # # #
    # MACRO MULTIPLIER
    
    #rebuilding exponentially to 95% of initial stock in reconst_duration
    three = np.log(1/0.05) 
    recons_rate = three/ df["T_rebuild_K"]  
    
    #discount rate
    rho = df["rho"]
    
    #productivity of capital
    mu= df["avg_prod_k"]

    # Calculation of macroeconomic resilience
    gamma =(mu +recons_rate)/(rho+recons_rate)   
   
    ###############################
    #Description of inequalities
    
    #proportion of poor people
    ph = df["pov_head"]
    
    #consumption levels
    
    gdp_pc_pp = df["rel_gdp_pp"] * df["gdp_pc_pp_nat"]
    
    cp=   df["share1"] *gdp_pc_pp
    cr=  (1 - df["pov_head"]*df["share1"])/(1-df["pov_head"]) *gdp_pc_pp
    
    ###########
    #exposure for poor and nonpoor
    fap =df["fap"]
    far =df["far"]

    ###########"
    #vulnerabilities from total and bias
    #early-warning-adjusted vulnerability
    vp = df["v_p"]*(1-df["pi"]*df["shew"])* (1-df["nat_buyout"])
    vr = df["v_r"]*(1-df["pi"]*df["shew"]) * (1-df["nat_buyout"])
    
    #losses shared within the province
    v_shared = df["v_s"] *(1-df["pi"]*df["shew"]) * (1-df["nat_buyout"])
    
    ###########
    #Ex-post support

    tot_p=1-(1-df["social_p"])*(1-df["sigma_p"])
    tot_r=1-(1-df["social_r"])*(1-df["sigma_r"])
    
    ############"
    #Eta
    elast=  df["income_elast"]
    
    ############
    #Welfare losses 
    
    delta_W,dKapparent,dcap,dcar =calc_delta_welfare(ph,fap,far,vp,vr,v_shared,cp,cr,tot_p,tot_r,mu,gamma,rho,elast)
    
    ###########
    #OUTPUT
    df_out = pd.DataFrame(index=df.index)
    
    #corrects from avoided losses through national risk sharing
    df_out["dK"] = dKapparent/(1-df["nat_buyout"])

    df_out["delta_W"]=delta_W
    df_out["dcap"]=dcap
    df_out["dcar"]=dcar
    df_out["dKtot"]=df_out["dK"]*df["pop"]/df["protection"]    
   
    return df_out
        
def calc_risk_and_resilience_from_k_w(df): 
    """Computes risk and resilience from dk, dw and protection. Line by line: multiple return periods or hazard is transparent to this function"""
    
    df=df.copy()    
    
    ############################
    #Expressing welfare losses in currency 
    
    #discount rate
    rho = df["rho"]
    h=1e-4
    wprime =(welf(df["gdp_pc_pp_nat"]/rho+h,df["income_elast"])-welf(df["gdp_pc_pp_nat"]/rho-h,df["income_elast"]))/(2*h)

    #Risk to welfare
    df["deltaW_nat"] = wprime * df["dK"]* df["nat_buyout"]* df["pop"]/df["pop"].sum()
    df["dWpc_curency"] =  (df["delta_W"]+df["deltaW_nat"])/wprime /df["protection"]
    df["risk"]= df["dWpc_curency"]/(df["gdp_pc_pp_ref"]);
    df["dWtot_currency"]=df["dWpc_curency"]*df["pop"];
    
    ############
    #SOCIO-ECONOMIC CAPACITY)
    
    #reference losses
    dWref   = wprime*df["dK"]
    
    df["resilience"]                    =dWref/(df["delta_W"] + df["deltaW_nat"]);

    ############
    #RISK TO ASSETS
    df["risk_to_assets"]  =df.resilience* df.risk;
    
    return df
    
    
def calc_delta_welfare(ph,fap,far,vp,vr,v_shared,cp,cr,la_p,la_r,mu,gamma,rho,elast):
    """welfare cost from consumption losses"""

    #fractions of people non-poor/poor affected/non affected over total pop
    nap= ph*fap
    nar=(1-ph)*far
    nnp=ph*(1-fap )
    nnr=(1-ph)*(1-far)
    
    #capital from consumption and productivity
    kp = cp/mu
    kr = cr/mu
    
    #total capital losses
    dK = kp*vp*fap*ph+\
         kr*vr*far*(1-ph)
    
    # consumption losses per category of population
    d_cur_cnp=fap*v_shared *la_p *kp    #v_shared does not change with v_rich so vr changes only vulnerabilities in the affected zone. 
    d_cur_cnr=far*v_shared *la_r *kr 
    d_cur_cap=vp*(1-la_p)*kp + d_cur_cnp
    d_cur_car=vr*(1-la_r)*kr + d_cur_cnr
    
    #losses in NPV after reconstruction 
    d_npv_cnp= gamma*d_cur_cnp
    d_npv_cnr= gamma*d_cur_cnr
    d_npv_cap= gamma*d_cur_cap
    d_npv_car= gamma*d_cur_car
    
    #welfare cost 
    Wpre =ph* welf(cp/rho,elast) + (1-ph)*welf(cr/rho,elast)
    Wpost=  nap*welf(cp/rho-d_npv_cap,elast) + \
            nnp*welf(cp/rho-d_npv_cnp,elast) + \
            nar*welf(cr/rho-d_npv_car,elast)+ \
            nnr*welf(cr/rho-d_npv_cnr,elast)
    dW =Wpre -Wpost #counting losses as +

    return dW,dK, d_cur_cap, d_cur_car
    
   
def welf(c,elast):
    """"Welfare function"""
    
    scale=1e4 #for numerical precision
    y=scale*(c**(1-elast)-1)/(1-elast)
    
    cond = elast==1
    y[cond] = scale*np.log(c[cond]) 
    
    return y
        
    
def def_ref_values(df):
    #fills the "ref" variables (those protected when computing derivatives)
    
    df["protectionref"]=df["protection"]  #avoid numerical errors when computing derivatives with respect to protection
    
    df["gdp_pc_pp_ref"] = df["gdp_pc_pp"] #risk expressed as fraction of current income
    
    df["v_s"] = df["v_r"] 
    
    return df


def interpolate_faratios(fa_ratios,protection_list):
    if fa_ratios is None:
        return None
 
    #figures out all the return periods to be included
    all_rps = list(set(protection_list+fa_ratios.columns.tolist()))

    fa_ratios_rps = fa_ratios.copy()
    
    #extrapolates linear towards the 0 return period exposure  (this creates negative exposure that is tackled after interp) (mind the 0 rp when computing probas)
    fa_ratios_rps[0]=fa_ratios_rps.iloc[:,0]- fa_ratios_rps.columns[0]*(
        fa_ratios_rps.iloc[:,1]-fa_ratios_rps.iloc[:,0])/(
        fa_ratios_rps.columns[1]-fa_ratios_rps.columns[0])
    
    
    #add new, interpolated values for fa_ratios, assuming constant exposure on the right
    x = fa_ratios_rps.columns.values
    y = fa_ratios_rps.values
    fa_ratios_rps= pd.concat(
        [pd.DataFrame(interp1d(x,y,bounds_error=False)(all_rps),index=fa_ratios_rps.index, columns=all_rps)]
        ,axis=1).sort_index(axis=1).clip(lower=0).fillna(method="pad",axis=1)
    fa_ratios_rps.columns.name="rp"

    return fa_ratios_rps
        
 
def average_over_rp(df,protection):        
    ###AGGREGATION OF THE OUTPUTS OVER RETURN PERIODS
    
    #does nothing if df does not contain data on return periods
    try:
        if "rp" not in df.index.names:
            return df
    except(TypeError):
        pass
    
    df=df.copy().reset_index("rp")
    protection=protection.copy().reset_index("rp",drop=True)
    
    #computes probability of each return period
    return_periods=np.unique(df["rp"].dropna())

    proba = pd.Series(np.diff(np.append(1/return_periods,0)[::-1])[::-1],index=return_periods) #removes 0 from the rps

    #matches return periods and their probability
    proba_serie=df["rp"].replace(proba)

    #removes events below the protection level
    proba_serie[protection>df.rp] =0

    #handles cases with multi index and single index (works around pandas limitation)
    idxlevels = list(range(df.index.nlevels))
    if idxlevels==[0]:
        idxlevels =0
        
    #average weighted by proba
    averaged = df.mul(proba_serie,axis=0).sum(level=idxlevels).div(proba_serie.sum(level=idxlevels),axis=0)
    
    return averaged.drop("rp",axis=1)


def sum_over_hazard(df):  
    #does nothing if df does not contain data on multiple hazards 
    try:
        if "hazard" not in df.index.names:
            return df
    except(TypeError):
        pass
    
    df=df.reset_index("hazard")
    
    #handles cases with multi index and single index (works around pandas limitation)
    idxlevels = list(range(df.index.nlevels))
    if idxlevels==[0]:
        idxlevels =0
    
    return df.sum(level=idxlevels)
        
    
   
#function
def make_tiers(series,labels=["Low","Mid","High"]):
    return pd.cut(series,[series.min()-1e3]+series.quantile([1/3,2/3]).tolist()+[series.max()+1e3],labels=labels).sort_values() #This magically orders the in the "Low", "Mid", "High" order, i wonder why

def categories_to_formated_excel_file(df_cat,filename="tiers.xlsx"):
    #Outputs resilience tiers to excel
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        workbook=writer.book
        # Add a format. Light red fill with dark red text.
        red = workbook.add_format({#'bg_color': '#f4a582',
                                       'font_color': '#ca0020'})
        orange = workbook.add_format({#'bg_color': '#f7f7f7',
                                       'font_color': '#000000'})

        blue = workbook.add_format({#'bg_color': '#92c5de',
                                       'font_color': '#0571b0'})
        df_cat.to_excel(writer,sheet_name="tiers")
        worksheet=writer.sheets["tiers"]
        worksheet.conditional_format('B2:B600', {'type':     'text',
                                       'criteria': 'containing',
                                    'value':    "Low",
                                    'format':   red})
        writer.sheets["tiers"].conditional_format('B2:B600', {'type':     'text',
                                    'criteria': 'containing',
                                    'value':    "High",
                                    'format':   blue})
        writer.sheets["tiers"].conditional_format('C2:C600', {'type':     'text',
                                       'criteria': 'containing',
                                    'value':    "Low",
                                    'format':   blue})
        writer.sheets["tiers"].conditional_format('C2:C600', {'type':     'text',
                                    'criteria': 'containing',
                                    'value':    "High",
                                    'format':   red})
        writer.sheets["tiers"].conditional_format('B2:C600', {'type':     'text',
                                    'criteria': 'containing',
                                    'value':    "Mid",
                                    'format':   orange}) 
        worksheet.autofilter('A1:C1')
        worksheet.set_column(0, 0, 20)
        worksheet.set_column(1, 1, 14)
        worksheet.set_column(2, 2, 8)
        writer.sheets["tiers"].freeze_panes(1, 1)