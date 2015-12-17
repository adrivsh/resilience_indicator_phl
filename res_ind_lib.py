import numpy as np
import pandas as pd
from scipy.special import erf
from scipy.interpolate import interp1d
from sorted_nicely import *

def compute_resiliences(df_in,kind="exante"):
    """Main function. Computes all outputs (dK, resilience, dC, etc,.) from inputs"""
    
    df=df_in.copy(deep=True)

    # # # # # # # # # # # # # # # # # # #
    # MACRO
    # # # # # # # # # # # # # # # # # # #
    
    # Effect of production and reconstruction
    ripple_effects= df["alpha"] 
    
    #rebuilding exponentially to 95% of initial stock in reconst_duration
    three = np.log(1/0.05) 
    recons_rate = three/ df["T_rebuild_K"]  
    
    #exogenous discount rate
    rho= 5/100
    
    #productivity of capital
    mu= df["avg_prod_k"]

    # Calculation of macroeconomic resilience
    df["macro_multiplier"]=gamma =(ripple_effects*mu +recons_rate)/(rho+recons_rate)   
   

    # # # # # # # # # # # # # # # # # # #
    # MICRO 
    # # # # # # # # # # # # # # # # # # #
    
    
    ###############################
    #Description of inequalities
    
    #proportion of poor people
    ph = df["pov_head"]
    
    #consumption levels
    
    df["gdp_pc_pp"] = df["rel_gdp_pp"] * df["gdp_pc_pp_nat"]
    
    df["cp"]=cp=   df["share1"] *df["gdp_pc_pp"]
    df["cr"]=cr=(1-df["share1"])*df["gdp_pc_pp"]
    #Eta
    elast=  df["income_elast"]

    ###########"
    #vulnerabilities from total and bias
    if kind=="exante":
        #early-warning-adjusted vulnerability
        v_shew=   df["v"]   *(1-df["pi"]*df["shew"])
        vs_touse = df["v_s"] *(1-df["pi"]*df["shew"]) * (1-df["nat_buyout"])
        
    else:
        v_shew = df["v"]
        vs_touse = df["v_s"]*(1-df["nat_buyout"])
        
    df["v_shew"] = v_shew
    
    
    #Part of the losses shared at national level
    df["v_shew_shared"]   = v_shew * (1-df["nat_buyout"])
    
    
    pv=df.pv
    
    #poor and non poor vulnerability "protected" from exposure variations... 
    df["v_p"],df["v_r"] = unpack_v(df["v_shew_shared"],pv,df.faref,df.peref,df.pov_head_ref,df.share1_ref)
    
    vp = df["v_p"]
    vr= df["v_r"]
  

    # if False:
        # & kind=="exante":
        # Ability and willingness to improve transfers after the disaster
        # df["borrow_abi"]=(df["rating"]+df["finance_pre"])/2 

        # df["sigma_p"]=df["sigma_r"]=df["scale_up_target"]*(df["borrow_abi"]+df["prepare_scaleup"])/2

        
    # df["sigma_p"]=df["sigma_r"]=df["sigma_both"]
        
    df["tot_p"]=tot_p=1-(1-df["social_p"])*(1-df["sigma_p"])
    df["tot_r"]=tot_r=1-(1-df["social_r"])*(1-df["sigma_r"])
    
    
    share_shareable = 1 if kind=="exante" else df["share_nat_income"]
        
    #No protection for ex post analysis
    protection = pd.Series(index=df.index).fillna(0) if kind=="expost" else df["protection"]

    #link between exposure at one return period and other exposures
    if kind=="exante":
        fa_ratios=df[df.columns[df.columns.str.startswith("fa_ratio_")]]
        fa_ratios.columns=map(lambda x:eval(x.split("fa_ratio_")[-1]),fa_ratios.columns)
    else:
        fa_ratios=pd.DataFrame(columns=[1],index=df.index).fillna(1)
    fa_ratios=fa_ratios.sort_index(axis=1)
    
    #########################
    ## Managing new fa_rations (when the derivative introduces protection+epsilon
    old_rps = fa_ratios.columns.tolist()
    all_rps = sorted(list(set(fa_ratios.columns.tolist()+df.dropna().protection .unique().tolist()))) if kind=="exante" else old_rps
    new_rps = [p for p in all_rps if p not in old_rps]

    #add new, interpolated fa_ratios
    x = fa_ratios.columns.values
    y = fa_ratios.values
    
    #assumes exposure to be linear between data points
    # if kind=="exante" :
        # fa_ratios=pd.concat([fa_ratios,pd.DataFrame(interp1d(x,y,fill_value=fa_ratios[x[-1]],bounds_error=False)(new_rps),index=fa_ratios.index, columns=new_rps)],axis=1).sort_index(axis=1) 
        
    #probability of each event
    # q = [0]+[1-1/x for x in all_rps]+[1]
    # proba=pd.Series(np.diff(q),index=[0]+all_rps)
   
    ############################
    #### Parameters for poverty traps
    
    #cost of poverty trap
    three = np.log(1/0.05) 
    recover_rate= three/df["T_rebuild_L"] 
    df["dC_destitution"] =df["gdp_pc_pp_nat"]/(rho+recover_rate)

    #social exposure to poverty traps
    df["institutional_exposure"] = ((1-df["axhealth"])+(1-df["plgp"])+df["unemp"])/3   
    
    #reference exposure
    fa=df.fa 
    
    #exposures from total exposure and bias
    pe=df.pe
    fap =df["fap"]=fa*(1+pe)
    far =df["far"]=(fa-ph*fap)/(1-ph)
    
    ######################################
    #Welfare losses from consumption losses
    
    deltaW,dKapparent,dcap,dcar    =calc_delta_welfare(ph,fap,far,vp,vr,vs_touse,cp,cr,tot_p         ,tot_r,mu,share_shareable,gamma,rho,elast)
    #Assuming no scale up
    dW_noupscale    ,foo,dcapns,dcarnos  =calc_delta_welfare(ph,fap,far,vp,vr,vs_touse,cp,cr,df["social_p"],df["social_r"],mu,share_shareable,gamma,rho,elast)

    # Assuming no transfers at all
    dW_no_transfers   ,foo,foo,foo  =calc_delta_welfare(ph,fap,far,vp,vr,vs_touse,cp,cr,0             ,0             ,mu,share_shareable,gamma,rho,elast)

    
    #corrects from avoided losses thru national risk sharing
    dK = dKapparent/(1-df["nat_buyout"])
    
    
    #output
    df["delta_W"]=deltaW
    df["dW_noupscale"]=dW_noupscale
    df["dW_no_transfers"]=dW_no_transfers
    df["dKpc"]=dK
    df["dcap"]=dcap
    df["dcar"]=dcar
    df["dKtot"]=dK*df["pop"]
    
    #######################################
    #Welfare losses from poverty traps

    #individual exposure
    psi_p=df["axfin_p"]
    psi_r=df["axfin_r"]
    
    #fraction of people with very low income
    trap_treshold = 0.1*df["gdp_pc_pp_nat"]
    
    df["individual_exposure"]= individual_exposure =(
            ph*fap*(1-psi_p)*THETA(cp-trap_treshold,cp*(1-tot_p)*vp,df["H"])+
        (1-ph)*far*(1-psi_r)*THETA(cr-trap_treshold,cr*(1-tot_r)*vr,df["H"])
        )
          
    #total exposure
    df["destitution_exposure"] =tot_exposure =  individual_exposure *  df["institutional_exposure"]

  

    df["dW_destitution"]= dW_destitution =tot_exposure*(welf(df["gdp_pc_pp"]/rho,elast) - welf(df["gdp_pc_pp"]/rho-df["dC_destitution"],elast))
     
    ############################
    #Reference losses
    h=1e-4
    wprime =(welf(df["gdp_pc_pp_nat"]/rho+h,elast)-welf(df["gdp_pc_pp_nat"]/rho-h,elast))/(2*h)
    dWref   = wprime*dK

    #Risk
    
    df["dWsurWprime"]=deltaW/wprime
    
    proba = 1/protection
    df["deltaW_nat"] = deltaW_nat = wprime *  dK * df["nat_buyout"] * df["pop"]/df["pop"].sum()
    
    df["equivalent_cost"] =  proba * (dW_destitution+deltaW+deltaW_nat)/wprime 
    
    df["risk"]= df["equivalent_cost"]/(df["gdp_pc_pp_ref"]);
    
    df["total_equivalent_cost"]=df["equivalent_cost"]*df["pop"];
    df["total_equivalent_cost_of_destitution"]=df["total_equivalent_cost"]*dW_destitution/(dW_destitution+deltaW)
    df["total_equivalent_cost_no_destitution"]=df["total_equivalent_cost"]*        deltaW/(dW_destitution+deltaW)
    df["total_equivalent_cost_of_nat_buyout"]=df["total_equivalent_cost"]*        deltaW_nat/(dW_destitution+deltaW)


    ############################
    #Risk and resilience
    
    #resilience
    df["resilience"]                    =dWref/(dW_destitution+deltaW + deltaW_nat);
    df["resilience_no_shock"]           =dWref/deltaW;
    df["resilience_no_shock_no_uspcale"]=dWref/dW_noupscale;
    df["resilience_no_shock_no_SP"]     =dWref/dW_no_transfers;

    #risk to assets
    df["risk_to_assets"]  =df.resilience* df.risk;
    
    return df
    
def calc_delta_welfare(ph,fap,far,vp,vr,v_shared,cp,cr,la_p,la_r,mu,sh_sh,gamma,rho,elast):
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
    d_cur_cnp=fap*v_shared *la_p *kp *sh_sh   #v_shared does not change with v_rich so pv changes only vulnerabilities in the affected zone. 
    d_cur_cnr=far*v_shared *la_r *kr *sh_sh
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
        
    
def THETA(y,m,H):
    """P(x>y) where x follows log-normal of average=m and Homogeneity=H"""
    #h=med/m = exp(-s**2/2)   log(h) = -s**2/2
    #h=med/m   med = m*h = exp(mu)   mu = log(m*h)
    return .5 * (1-erf(np.log(y/(m*H))/(2*np.sqrt(-np.log(H)))))
   

def unpack_v(v,pv,fa,pe,ph,share1):
#poor and non poor vulnerability from aggregate vulnerability,  exposure and biases
    
    v_p = v*(1+pv)
    
    fap_ref= fa*(1+pe)
    far_ref=(fa-ph*fap_ref)/(1-ph)
    cp_ref=   share1
    cr_ref=(1-share1)
    
    x=ph*cp_ref *fap_ref    
    y=(1-ph)*cr_ref  *far_ref
    
    v_r = ((x+y)*v - x* v_p)/y
    
    return v_p,v_r

def compute_v_fa(df):
    fap = df["fap"]
    far = df["far"]
    
    vp = df.v_p
    vr=df.v_r

    ph = df["pov_head"]
        
    cp=   df["share1"] *df["gdp_pc_pp"]
    cr=(1-df["share1"])*df["gdp_pc_pp"]
    
    fa = ph*fap+(1-ph)*far
    
    x=ph*cp 
    y=(1-ph)*cr 
    
    v=(y*vr+x*vp)/(x+y)
    
    return v,fa
    
    
def def_ref_values(df):
    #fills the "ref" variables (those protected when computing derivatives)
    df["peref"]=df["pe"]
    df["faref"]=df["fa"]
    df["share1_ref"]=df["share1"]
    df["gdp_pc_pp_ref"] = df["gdp_pc_pp"]
    vp,vr =unpack_v(df.v,df.pv,df.fa,df.pe,df.pov_head,df.share1)
    df["v_s"] = vr
    df["pov_head_ref"]=df["pov_head"]
    return df