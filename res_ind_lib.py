import numpy as np
import pandas as pd
from scipy.special import erf
from scipy.interpolate import interp1d
from sorted_nicely import *

def compute_resiliences(df_in):
    """Main function. Computes all outputs (dK, resilience, dC, etc,.) from inputs"""
    
    df=df_in.copy(deep=True)

    # # # # # # # # # # # # # # # # # # #
    # MACRO
    # # # # # # # # # # # # # # # # # # #
    
    
    #rebuilding exponentially to 95% of initial stock in reconst_duration
    three = np.log(1/0.05) 
    recons_rate = three/ df["T_rebuild_K"]  
    
    #exogenous discount rate
    rho= 5/100
    
    #productivity of capital
    mu= df["avg_prod_k"]

    # Calculation of macroeconomic resilience
    df["macro_multiplier"]=gamma =(mu +recons_rate)/(rho+recons_rate)   
   

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
    df["cr"]=cr=  (1 - df["pov_head"]*df["share1"])/(1-df["pov_head"])  *df["gdp_pc_pp"]
    #Eta
    elast=  df["income_elast"]

    ###########"
    #vulnerabilities from total and bias
    #early-warning-adjusted vulnerability
    df["v_shew"]=   df["v"]   *(1-df["pi"]*df["shew"])
    vs_touse = df["v_s"] *(1-df["pi"]*df["shew"]) * (1-df["nat_buyout"])
        
    #Part of the losses shared at national level
    df["v_shew_shared"]   = df["v_shew"] * (1-df["nat_buyout"])
    
    
    pv=df.pv
    
    #poor and non poor vulnerability "protected" from exposure variations... 
    df["v_p"],df["v_r"] = unpack_v(df["v_shew_shared"],pv,df.faref,df.peref,df.pov_head_ref,df.share1_ref)
    
    vp = df["v_p"]
    vr= df["v_r"]
  

    df["tot_p"]=tot_p=1-(1-df["social_p"])*(1-df["sigma_p"])
    df["tot_r"]=tot_r=1-(1-df["social_r"])*(1-df["sigma_r"])
    
    
    #No protection for ex post analysis
    protection =  df["protection"]

    #reference exposure
    fa=df.fa 
    
    #exposures from total exposure and bias
    pe=df.pe
    fap =df["fap"]=fa*(1+pe)
    far =df["far"]=(fa-ph*fap)/(1-ph)
    
    ######################################
    #Welfare losses from consumption losses
    
    deltaW,dKapparent,dcap,dcar    =calc_delta_welfare(ph,fap,far,vp,vr,vs_touse,cp,cr,tot_p         ,tot_r,mu,gamma,rho,elast)
   
   #Assuming no scale up
    dW_noupscale    ,foo,dcapns,dcarnos  =calc_delta_welfare(ph,fap,far,vp,vr,vs_touse,cp,cr,df["social_p"],df["social_r"],mu,gamma,rho,elast)

    # Assuming no transfers at all
    dW_no_transfers   ,foo,foo,foo  =calc_delta_welfare(ph,fap,far,vp,vr,vs_touse,cp,cr,0             ,0             ,mu,gamma,rho,elast)

    
    #corrects from avoided losses through national risk sharing
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
    #Welfare losses from health costs
    

    
    # health_cost_raw_p = f_health_cost * cp
    # health_cost_raw_r = f_health_cost * cr
    
    health_cost_paid_p =df.axhealth*cp
    health_cost_paid_r =df.axhealth*cr
    

    #individual exposure
    psi_p=df["axfin_p"]
    psi_r=df["axfin_r"]
    
     
    ############################
    #Reference losses
    h=1e-4
    wprime =(welf(df["gdp_pc_pp_nat"]/rho+h,elast)-welf(df["gdp_pc_pp_nat"]/rho-h,elast))/(2*h)
    dWref   = wprime*dK

    #Risk
    
    df["dWsurWprime"]=deltaW/wprime
    
    proba = 1/protection
    df["deltaW_nat"] = deltaW_nat = wprime *  dK * df["nat_buyout"] * df["pop"]/df["pop"].sum()
    
    df["equivalent_cost"] =  proba * (deltaW+deltaW_nat)/wprime 
    
    df["risk"]= df["equivalent_cost"]/(df["gdp_pc_pp_ref"]);
    
    df["total_equivalent_cost"]=df["equivalent_cost"]*df["pop"];
    
    df["total_equivalent_cost_of_nat_buyout"]=df["total_equivalent_cost"]*deltaW_nat/(deltaW)


    ############################
    #Risk and resilience
    
    #resilience
    df["resilience"]                    =dWref/(deltaW + deltaW_nat);
    df["resilience_no_shock"]           =dWref/deltaW;
    df["resilience_no_shock_no_uspcale"]=dWref/dW_noupscale;
    df["resilience_no_shock_no_SP"]     =dWref/dW_no_transfers;

    #risk to assets
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
    d_cur_cnp=fap*v_shared *la_p *kp    #v_shared does not change with v_rich so pv changes only vulnerabilities in the affected zone. 
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