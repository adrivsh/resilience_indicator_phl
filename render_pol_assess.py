from fancy_round import *
from progress_reporter import *
import matplotlib.pyplot as plt

height = 0.40  

font = {'family' : 'sans serif','size'   : 11}

smallfont= {'family' : 'sans serif','size'   : 9}
cursfont= {'family' : 'cursive','size'   : 9}
tinyfont= {'family' : 'sans serif','size'   : 8}

plt.rc('font', **font)

def autolabel(ax,rects,color, sigdigits,  **kwargs):
    # attach some data labels
    for rect in rects:
        h = rect.get_height()
        x = rect.get_x()
        y = rect.get_y()
        w = rect.get_width()
        value = x if x<0 else w
        stri=str(fancy_round(value,sigdigits))
        
        #remove trailing zeros
        if "." in stri:
            while stri.endswith("0"):
                stri=stri[:-1]        
        
        if stri.endswith("."):
            stri=stri[:-1]        
        
        if value<0:
            stri = stri+' '
        else:
            stri = ' '+stri
        # print(value,stri)        
        ax.text(value, y+0.4*h, stri, ha="right" if x<0 else 'left', va='center', color=color , **kwargs)

        
def render_pol_cards(ders,colors,policy_descriptions,unit,size,province_list=None):
    if province_list is None:
        province_list=ders.unstack("var").index
    
    for p in province_list:
        progress_reporter(p)    
            
        toplot = unit["multiplier"]*(ders.ix[p].mul(size,axis=0)).dropna()   #.div(base.ix[p],axis=0)
        toplot = toplot.mul(-np.sign(toplot.dWtot_currency),axis=0)
        toplot = toplot[["dWtot_currency","dKtot"]].sort_values("dWtot_currency",ascending=False)       

        labels = toplot.index
        n=len(labels)

        ind=np.arange(n)
        fig, ax = plt.subplots(figsize=(7,n/2))

        plt.vlines(0, 0, n, colors="black")    

        rects1 = ax.barh(ind,toplot["dKtot"],height=height, **colors.ix["dKtot"]
               )
        rects2 = ax.barh(ind+height,  toplot["dWtot_currency"],height=height, **colors.ix["dWtot_currency"]
                )

        # add some text for labels, title and axes ticks
        ax.set_xlabel(unit["string"])
        ax.set_yticks(ind+height)
        ax.set_yticklabels(policy_descriptions[labels]+"   "  )

        # plt.xlim(-1.15,1.15)


        # remove ticks 
        # ax.spines['bottom'].set_color('none')
        ax.spines['right'].set_color('none')

        ax.spines['top'].set_color('none')
        ax.spines['left'].set_color("none")
        #removes ticks 
        for tic in ax.xaxis.get_major_ticks() + ax.yaxis.get_major_ticks():
            tic.tick1On = tic.tick2On = False
        # ax.xaxis.set_visible(False )

        autolabel(ax,rects1,colors.ix["dKtot","edgecolor"],2,**tinyfont)
        autolabel(ax,rects2,colors.ix["dWtot_currency","edgecolor"],2,**smallfont)

        # ax.legend( (rects2[0],rects1[0]), ( 'Effect on welfare','Avoided asset losses'), loc="lower right",frameon=False )


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

        plt.title(p);

        plt.savefig("cards/"+file_name_formater(p)+".pdf", bbox_inches="tight")
            
       
def file_name_formater(x):
    return x.lower().replace(" ","_").replace("\\","")
       
#implements http://stackoverflow.com/questions/7102090/combining-pdf-files-with-ghostscript-how-to-include-original-file-names
import glob
from subprocess import call, Popen
import sys
from IPython.display import clear_output


def merge_cardfiles(country_list,outputname):

    #goes to the write directory
    glob.os.chdir("cards/")

    command= ""
    i=1
    for name in country_list:
        command+="({name}) run [ /Page {page} /Title ({name}) /OUT pdfmark \n".format(name=file_name_formater(name)+".pdf",page=i)
        i+=1

    with open("control.ps", "w") as text_file:
        text_file.write(command)

    #merges all eps to a PDF
    p=Popen("gswin64c -dEPSFitPage -sDEVICE=pdfwrite -o "+outputname+" control.ps");
    print("Merging cards....")
    sys.stdout.flush()

    p.communicate()

    print("Merging cards done")
    glob.os.chdir("..")