import numpy as np
import pandas as pd

def compute_resiliences(df_in, fa_ratios=None, multihazard_data =None):
    """Main function. Computes all outputs (dK, resilience, dC, etc,.) from inputs"""

    df=df_in.copy()
    
    #computes dk_{hazard, return} and dW_{hazard, return}
    dkdw=compute_dK_dW(df)
    df[dkdw.columns]=dkdw     #adds dk and dw-like columns to df

    #computes socio economic capacity and risk
    df = calc_risk_and_resilience_from_k_w(df)

    return df
    
def compute_dK_dW(df):  
    '''Computes dk and dW line by line. 
    presence of multiple return period or multihazard data is transparent to this function'''    

    ###############################
    #Description of inequalities
    
    #proportion of poor family
    ph = df["pov_head"]
    
    #consumption levels
    gdp_pc_pp = df["gdp_pc_pp"] 
    
    cp=   df["cp"]
    cr = df["cr"]
    
    ###########
    #exposure for poor and nonpoor
    fap =df["fap"]
    far =df["far"]

    ###########"
    #early-warning-adjusted vulnerability
    
    vp = df["v_p"]*(1-df["pi"]*df["shewp"])
    vr = df["v_r"]*(1-df["pi"]*df["shewr"]) 
    
    #losses shared within the province
    v_shared = df["v_s"] *(1-df["pi"]*df["shew"]) 
    
    # # # # # # # # # # # # # # # # # # #
    # From asset losses to consumption losses
    
    #time it takes to rebuild the damaged asset
    N= df["T_rebuild_K"]

    #discount rate
    rho = df["rho"]

    #productivity of capital
    mu= df["avg_prod_k"]

    # Link between immediate and discounted losses
    gamma =(mu +3/N)/(rho+3/N) 
    
    ###########
    #Ex-post support

    tot_p=1-(1-df["social_p"])*(1-df["sigma_p"])
    tot_r=1-(1-df["social_r"])*(1-df["sigma_r"])
    
    ############"
    #Eta
    elast=  df["income_elast"]
    
    ############
    #Welfare losses 
    
    delta_W,dK,dcap,dcar =calc_delta_welfare(ph,fap,far,vp,vr,v_shared,cp,cr,tot_p,tot_r,mu,gamma,rho,elast)
    
    ###########
    #OUTPUT
    df_out = pd.DataFrame(index=df.index)
    
    #corrects from avoided losses through national risk sharing
    df_out["dK"] = dK

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
    
    #welfare of the average Filipino family
    W_pre_ref = welf(df["gdp_pc_pp_nat"], df["income_elast"])
    
    #after welfare losses in each province
    W_post_ref = W_pre_ref - df["delta_W"]
    
    #equivalent income 
    C_post_ref  = invert_welf(W_post_ref,df["income_elast"])
    
    #equivalent income loss in the event of a disaster
    dc_ref = df["gdp_pc_pp_nat"] - C_post_ref
    
    #expected welfare loss (per family and total)
    df["dWpc_curency"] = dc_ref/df["protection"]
    df["dWtot_currency"]=df["dWpc_curency"]*df["pop"];
    
    #Risk to welfare as percentage of local GDP
    df["risk"]= df["dWpc_curency"]/(df["gdp_pc_pp"]);
    
    ############
    #SOCIO-ECONOMIC CAPACITY)
    
    df["resilience"] =df["dWpc_curency"]/df["dK"];

    ############
    #RISK TO ASSETS
    df["risk_to_assets"]  =df.resilience* df.risk;
    
    return df
    
    
def calc_delta_welfare(ph,fap,far,vp,vr,v_shared,cp,cr,la_p,la_r,mu,gamma,rho,elast):
    """welfare cost from consumption losses"""

    #fractions of family non-poor/poor affected/non affected over total pop
    nap= ph*fap
    nar=(1-ph)*far
    nnp=ph*(1-fap )
    nnr=(1-ph)*(1-far)
    
    #capital from consumption and productivity
    kp = cp/mu
    kr = cr/mu
    
    #total capital losses
    dK = kp*vp*nap+\
         kr*vr*nar
    
    # consumption losses per category of population
    d_cur_cnp=fap*v_shared *la_p *kp   
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
    """"Iso-elastic welfare function.
    See https://en.wikipedia.org/wiki/Isoelastic_utility"""
    
    u=(c**(1-elast)-1)/(1-elast)
    
    cond = elast==1
    u[cond] = np.log(c[cond]) 
    
    return u
    
def invert_welf(u,elast):
    """ Invert function of the welfare function """
    
    c=((1-elast)*u+1)**(1/(1-elast))
    
    c[elast==1]=np.exp(cond)
    
    return c
    
    
def def_ref_values(df):
    #fills the "ref" variables (those protected when computing derivatives)
    
    df["v_s"] = df["v_r"] 
    
    return df

