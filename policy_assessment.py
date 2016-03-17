from fancy_round import *
from progress_reporter import *
import matplotlib.pyplot as plt

from subprocess import Popen  #to call other programs from python
import sys #one function, flush, to force jupyter to print a message immediately
import glob  #to make foldeltas, move files, etc.

import pandas as pd
from res_ind_lib import *

#height of the bars
height = 0.40  

#fonts
font = {'family' : 'sans serif','size'   : 11}
smallfont= {'family' : 'sans serif','size'   : 9}
tinyfont= {'family' : 'sans serif','size'   : 8}

#instructs matplotlib to use that font by default
plt.rc('font', **font)
    
def compute_policies(df_original,pol_increment,pol_assess_set, bounds, **kwargs):
    
    #initialize
    delta = pd.DataFrame(index=df_original.index, columns=pd.MultiIndex.from_product([pol_increment.index,pol_assess_set], names=['inputs', 'outputs']))
    
    #baseline
    fx = compute_resiliences(df_original, **kwargs)[pol_assess_set]
    
    for var in pol_increment.index:
        progress_reporter(var)
    
        df_=df_original.copy(deep=True)
        
        #increments
        df_[var]=df_[var]+pol_increment[var]
        
        #new value
        fxh= compute_resiliences(df_, **kwargs)[pol_assess_set]
        
        #effect
        delta[var] = (fxh-fx)
    
    progress_reporter("done.")       
    
    return delta.stack("inputs").unstack("province").swaplevel('province', 'outputs', axis=1).sort_index(axis=1).dropna(how="all",axis=1)
    

def compute_policies_mh(df_original,multi_hard_info,pol_increment_mh,pol_assess_set, bounds, **kwargs):
    
    #initialize
    delta = pd.DataFrame(index=df_original.index, columns=pd.MultiIndex.from_product([pol_increment_mh.index,pol_assess_set], names=['inputs', 'outputs']))
    
    #baseline
    fx = compute_resiliences(df_original, multihazard_data =multi_hard_info)[pol_assess_set]
        
    for var in pol_increment_mh.index:
        progress_reporter(var)

        mh_=multi_hard_info.copy(deep=True).unstack("hazard")

        #increments
        mh_[eval(var)]=mh_[eval(var)]+pol_increment_mh[var]

        #new value
        fxh= compute_resiliences(df_original, multihazard_data =mh_.stack("hazard"))[pol_assess_set]

        #effect
        delta[var] = (fxh-fx)
 
    
    progress_reporter("done.")       
    
    return delta.stack("inputs").unstack("province").swaplevel('province', 'outputs', axis=1).sort_index(axis=1).dropna(how="all",axis=1)
        
def render_pol_cards(deltas,colors,policy_descriptions,pol_increment,unit,province_list, 
outfolder="cards/"):
    """Rendeltas the policy cards
    deltas: dataframe indexed by (var). Column is multi-indexed: provinces x ["dWtot_currency","dKtot"]. The impact of marginally increasing var in province on dw and dK.
    policy_descriptions. Series index by variable. Explains what the policy is. eg "Decrease poverty to 0.1%" 
    colors: dataframe. Columns: ["dWtot_currency","dKtot"]. Rows: kwargs to pass to plt.barh for formatting the color bars.
    unit: dictionary such as {"multiplier":1000, "string" Thousands }. For the x label.
    province_list: provinces to plot. Should be in deltas.index.
    """
    
    # print("HELLOOOOO")
   
    for p in province_list:
        #Displays current province in the loop 
        progress_reporter(p)    
        
        #select current line in deltas, and scales it.
        toplot = unit["multiplier"]*deltas[p].dropna()  
        
        #assumes the policy is framed in terms of what increases welfare ("decrease poverty", not "increase poverty")
        pol_sign  = -np.sign(toplot.dWtot_currency)
        toplot = toplot.mul(pol_sign,axis=0)
        toplot = toplot[["dWtot_currency","dKtot"]].sort_values("dWtot_currency",ascending=False)       
        
        #number of policy experiments to render
        n=toplot.shape[0]
        
        #new figure
        fig, ax = plt.subplots(figsize=(3.5,n/2))
    
        #actual plotting
        ind=np.arange(n)
        
        rects1 = ax.barh(ind,toplot["dKtot"],height=height, **colors.ix["dKtot"]
               )
        rects2 = ax.barh(ind+height,  toplot["dWtot_currency"],height=height, **colors.ix["dWtot_currency"]
                )

        #0 line
        plt.vlines(0, 0, n, colors="black")    
        
        for k in deltas.index:
            policy_descriptions[k] = policy_descriptions[k].format(sign=("-" if pol_sign[k]<0 else "+"),dh=pol_increment[k])
        
        
        # add some labels, title and axes ticks
        ax.set_xlabel(unit["string"])
        ax.set_yticks(ind+height)
        ax.set_yticklabels(policy_descriptions[toplot.index]+"     "  )
        plt.title(p);

        # remove spines
        # ax.spines['bottom'].set_color('none')
        ax.spines['right'].set_color('none')

        ax.spines['top'].set_color('none')
        ax.spines['left'].set_color("none")

        #removes ticks 
        for tic in ax.xaxis.get_major_ticks() + ax.yaxis.get_major_ticks():
            tic.tick1On = tic.tick2On = False
        
        ax.xaxis.set_ticklabels([])

        #labels (numbers) on the bars
        autolabel(ax,rects1,colors.ix["dKtot","edgecolor"],2,**tinyfont)
        autolabel(ax,rects2,colors.ix["dWtot_currency","edgecolor"],2,**smallfont)

        #annotated "legend"
        ax.annotate("Effect on asset losses",  xy=(0,n-1+height/2),xycoords='data',ha="left",va="center",
                      xytext=(20, -5), textcoords='offset points', 
                        arrowprops=dict(arrowstyle="->",
                                        connectionstyle="arc3,rad=-0.13",color=colors.edgecolor.dKtot
                                        ), **smallfont)

        ax.annotate("Effect on welfare losses",  xy=(0,n-height),xycoords='data',ha="left",va="center",
                      xytext=(20, 3), textcoords='offset points', 
                        arrowprops=dict(arrowstyle="->",
                                        connectionstyle="arc3,rad=+0.13",color=colors.edgecolor.dWtot_currency
                                        ), **smallfont)

        
        glob.os.makedirs(outfolder,exist_ok=True)
        #exports to pdf
        plt.savefig(outfolder+file_name_formater(p)+".pdf",
                    bbox_inches="tight" #ensures the policy label are not cropped out
                    )

def render_pol_cards_per_policy(deltas,colors,policy_descriptions,pol_increment,unit,policy_list, 
outfolder="cards/"):
    """Rendeltas the policy cards
    deltas: dataframe indexed by (var). Column is multi-indexed: provinces x ["dWtot_currency","dKtot"]. The impact of marginally increasing var in province on dw and dK.
    policy_descriptions. Series index by variable. Explains what the policy is. eg "Decrease poverty to 0.1%" 
    colors: dataframe. Columns: ["dWtot_currency","dKtot"]. Rows: kwargs to pass to plt.barh for formatting the color bars.
    unit: dictionary such as {"multiplier":1000, "string" Thousands }. For the x label.
    policy_list: provinces to plot. Should be in deltas.index.
    """
    
    # print("HELLOOOOO")
   
    for pol in policy_list:
        #Displays current province in the loop 
        progress_reporter(pol)    
        
        #select current line in deltas, and scales it.
        toplot = unit["multiplier"]*deltas[pol].dropna()  
        
        #assumes the policy is framed in terms of what increases welfare ("decrease poverty", not "increase poverty")
        pol_sign  = -np.sign(toplot.iloc[0].dWtot_currency)
        toplot = toplot.mul(pol_sign,axis=0)
        toplot = toplot[["dWtot_currency","dKtot"]].sort_values("dWtot_currency",ascending=False)       
        
        #number of PROVINCES experiments to render
        n=toplot.shape[0]
        
        #new figure
        fig, ax = plt.subplots(figsize=(3.5,n/2.1))
    
        #actual plotting
        ind=np.arange(n)
        rects1 = ax.barh(ind,toplot["dKtot"],height=height, **colors.ix["dKtot"]
               )
        rects2 = ax.barh(ind+height,  toplot["dWtot_currency"],height=height, **colors.ix["dWtot_currency"]
                )
                
        ax.legend(["Effect on asset losses", "Effect on welfare losses"],loc="best")

        #0 line
        plt.vlines(0, 0, n, colors="black")    
        
        the_policy_description = policy_descriptions[pol].format(sign=("-" if pol_sign<0 else "+"),dh=pol_increment[pol])
        
        # add some labels, title and axes ticks
        ax.set_xlabel(unit["string"])
        ax.set_yticks(ind+height)
        ax.set_yticklabels(toplot.index+"     "  )
        plt.title(policy_descriptions[pol]);

        # remove spines
        # ax.spines['bottom'].set_color('none')
        ax.spines['right'].set_color('none')

        ax.spines['top'].set_color('none')
        ax.spines['left'].set_color("none")

        #removes ticks 
        for tic in ax.xaxis.get_major_ticks() + ax.yaxis.get_major_ticks():
            tic.tick1On = tic.tick2On = False
        
        ax.xaxis.set_ticklabels([])

        #labels (numbers) on the bars
        autolabel(ax,rects1,colors.ix["dKtot","edgecolor"],2,**tinyfont)
        autolabel(ax,rects2,colors.ix["dWtot_currency","edgecolor"],2,**smallfont)

        #annotated "legend"
        # ax.annotate("Effect on asset losses",  xy=(0,n-1+height/2),xycoords='data',ha="left",va="center",
                      # xytext=(20, -5), textcoords='offset points', 
                        # arrowprops=dict(arrowstyle="->",
                                        # connectionstyle="arc3,rad=-0.13",color=colors.edgecolor.dKtot
                                        # ), **smallfont)

        # ax.annotate("Effect on welfare losses",  xy=(0,n-height),xycoords='data',ha="left",va="center",
                      # xytext=(20, 3), textcoords='offset points', 
                        # arrowprops=dict(arrowstyle="->",
                                        # connectionstyle="arc3,rad=+0.13",color=colors.edgecolor.dWtot_currency
                                        # ), **smallfont)


        glob.os.makedirs(outfolder,exist_ok=True)
        #exports to pdf
        plt.savefig(outfolder+file_name_formater(pol)+".pdf",
                    bbox_inches="tight" #ensures the policy label are not cropped out
                    )
            
def autolabel(ax,rects,color, sigdigits,  **kwargs):
    """attach labels to an existing horizontal bar plot. Passes kwargs to the text (font, color, etc)"""
    
    
    for rect in rects:
        
        #parameters of the rectangle
        h = rect.get_height()
        x = rect.get_x()
        y = rect.get_y()
        w = rect.get_width()
        
        #figures out if it is a negative or positive value
        value = x if x<0 else w

        ####
        # FORMATS LABEL
        
        #truncates the value to sigdigits digits after the coma.
        stri=str(fancy_round(value,sigdigits))
        
        #remove trailing zeros
        if "." in stri:
            while stri.endswith("0"):
                stri=stri[:-1]        
        
        #remove trailing dot
        if stri.endswith("."):
            stri=stri[:-1]        
        
        if stri=="-0":
            stri="0"
        
        #space before or after (pad)
        if value<0:
            stri = stri+' '
        else:
            stri = ' '+stri

        #actual print    
        ax.text(value, y+0.4*h, stri, ha="right" if x<0 else 'left', va='center', color=color , **kwargs)

def check_bounds(df, bounds):
    clip = df.clip(lower=bounds.inf.dropna(),upper=bounds.sup.dropna(),axis=1).fillna(df)
    
    was_diff=(clip!=df) & (df.notnull())
    
    for c in was_diff.columns[was_diff.any()]:
        print("clipped "+c+" in "+"; ".join(was_diff[c][was_diff[c]].index))
    
    return clip
    
def check_bounds_series(s, bounds):

    clip=s

    if not np.isnan(bounds.inf):
        clip = clip.clip_lower(bounds.inf)
    if not np.isnan(bounds.sup):
        clip = clip.clip_upper(bounds.sup)
    
    was_diff=(clip!=s) & (s.notnull())
    
    if was_diff.any():
        print("clipped "+"; ".join(was_diff[was_diff].index))
    
    return clip
    
 
def file_name_formater(string):
    """Ensures string does not contain special characters so it can be used as a file name"""    
    return string.lower().replace(" ","_").replace("\\","")
       

def merge_cardfiles(list,outputname):
    """Merges individual policy card pdf to a single multi page pdf with all the cards. Requires ghostscipt."""
    #implements http://stackoverflow.com/questions/7102090/combining-pdf-files-with-ghostscript-how-to-include-original-file-names

    #builds the command for ghostscript
    command= ""
    i=1
    for name in list:
        command+="({name}) run [ /Page {page} /Title ({simplename}) /OUT pdfmark \n".format(name=name.replace("\\","/"),simplename=glob.os.path.splitext(glob.os.path.basename(name))[0].replace("_"," ").title(),page=i)
        i+=1

    #writes the command for ghostscipt
    with open("control.ps", "w") as text_file:
        text_file.write(command)

    #runs ghostscipt in a new process
    p=Popen("gswin64c -dEPSFitPage -sDEVICE=pdfwrite -o "+outputname+" control.ps");

    print("Merging cards....")
    sys.stdout.flush()

    #waits for GS to finish
    p.communicate()
    print("Merging cards done")
    
    #deletes GS command
    glob.os.remove("control.ps")

def convert_pdf_to_png(folder):
    """Convert individual pdf cards to PNG. Requires imagemagick. 
    Moves the resulting png to a subolfer""" 
    
    folder = glob.os.path.dirname(folder)
        
    #creates the destination subdir
    destinationpath =glob.os.path.join(folder,"png") 
    glob.os.makedirs(destinationpath,exist_ok=True) 
    
    #starts imagemagick in a new process 
    q=Popen("mogrify -density 150 -path {dest} -format png {folder}/*.pdf".format(folder=folder, dest=destinationpath));
    print("Converting cards....")
    sys.stdout.flush()
    
    #waits for imagemagick to finish
    q.communicate()
    print("conversion to png done")





    
    
