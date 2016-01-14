import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import pandas as pd
from subprocess import call
import numpy as np

def n_to_one_normalizer(s,n=0):
  #affine transformation from s to [n,1]      
    y =(s-s.min())/(s.max()-s.min())
    return n+(1-n)*y
    
def bins_normalizer(x,n=7):
  #bins the data in n regular bins (no clue how this is better than pd.bin)     
    n=n-1
    y= n_to_one_normalizer(x,0)  #0 to 1 numbe
    return np.floor(n*y)/n

def quantile_normalizer(column, nb_quantile=5):
  #bbins in quintiles      
    return (pd.qcut(column, nb_quantile,labels=False))/(nb_quantile-1)

def num_to_hex(x):
    h = hex(int(255*x)).split('x')[1]
    if len(h)==1:
        h="0"+h
    return h

def data_to_rgb(serie,color_maper=plt.cm.get_cmap("Blues_r"), normalizer = n_to_one_normalizer, norm_param = 0, na_color = "#e0e0e0"):
    
    data_n = normalizer(serie,norm_param)

    #here matplolib color mappers will just fill nas with the lowest color in the colormap
    colors = pd.DataFrame(color_maper(data_n),index=serie.index, columns=["r","g","b","a"]).applymap(num_to_hex)
    
    out = "#"+colors.r+colors.g+colors.b
    out[serie.isnull()]=na_color
    return out.str.upper()
    
############################################################################# 
#######################         FROM SVG              ####################### 
#############################################################################     
    
from bs4 import BeautifulSoup    
from IPython.display import Image, display, HTML, SVG
img_width = 400
import os

def make_map_from_svg(series_in, svg_file_path, outname, color_maper=plt.cm.get_cmap("Blues"), label = "", new_title=None):
    """Makes a cloropleth map and a legend from a panda series and a blank svg map. 
    Assumes the index of the series matches the SVG classes
    Saves the map in SVG, and in PNG if Inksscape is inkscape.
    if provided, new_title sets the title for the new SVG map
    """
    
    #simplifies the index to lower case without space
    series_in.index = series_in.index.str.lower().str.replace(" ","_")
    
    #compute the colors 
    color = data_to_rgb(series_in,color_maper=color_maper)

    #Builds the CCS style for the new map  (todo: this step could get its own function)
    style_base =\
    """.{depname}
    {{  
       fill: {color};
       stroke:#000000;
       stroke-width:2;
       fill-rule:evenodd;
    }}"""

    #Default style (for regions which are not in series_in)
    style =\
    """.default
    {
    fill: #e0e0e0;
    stroke:#ffffff;
    stroke-width:2;
    fill-rule:evenodd;
    }
    """

    
    #builds the style line by line (using lower case identifiers)
    for c in series_in.index:
        style= style       + style_base.format(depname=c,color=color[c])+ "\n"   


    #makes the legend
    l = make_legend(100*series_in,color_maper,label,"legend_of_"+outname)
    
    #makes the map
    # m= append_styles_to_map(svg_file_path,style,"map_of_"+outname,new_title)    

    target_name = "map_of_"+outname

    # def append_styles_to_map(svg_file_path,style,target_name,new_title=None):
    
    #read input MIND UTF8
    with open(svg_file_path, 'r',encoding='utf8') as svgfile:
        soup=BeautifulSoup(svgfile.read(),"xml")

    #names of regions to lower case without space   
    for p in soup.findAll("path"):
        p["class"]=p["class"].lower().replace(" ","_")
        #Update the title (tooltip) of each region with the numerical value (ignores missing values)
        try:
            p.title.string += "{val:.1%}".format(val=series_in[p["class"]])
        except:
            pass

    #remove the existing style attribute (unimportant)
    del soup.svg["style"]
    
    #append style
    soup.style.string = style
    
    #Maybe update the title
    if new_title is not None:
        soup.title.string = new_title
    else:
        new_title = ""
        
    #write output
    with open(target_name+".svg", 'w', encoding="utf-8") as svgfile:
        svgfile.write(soup.prettify())
        
    #inkscapes SVG to PNG    
    call("inkscape -f {map}.svg -e {map}.png -d 150".format(map=target_name), shell=True) 
    
    #Works around a bug in the notebook where style-based colouring colors all the maps  in the NB with a single color scale
    # m= SVG("{map}.svg".format(map=target_name))
    m= Image("{map}.png".format(map=target_name) ,width=img_width)  
    display(HTML("<a target='_blank' href='"+target_name+".svg"+"'>SVG "+new_title+"</a>"))

    #Attempts to downsize to a fix width and concatenate using imagemagick
    call("convert legend_of_{outname}.png -resize {w} small_legend.png".format(outname=outname,w=img_width), shell=True )
    call("convert map_of_{outname}.png -resize {w} small_map.png".format(outname=outname,w=img_width) , shell=True)
    call("convert -append small_map.png small_legend.png map_and_legend_of_{outname}.png".format(outname=outname) , shell=True)
    
    #removes temp files
    if os.path.isfile("small_map.png"):
        os.remove("small_map.png")
    if os.path.isfile("small_legend.png.png"):
        os.remove("small_legend.png.png")
        
    if os.path.isfile("map_and_legend_of_{outname}.png".format(outname=outname)):
        return Image("map_and_legend_of_{outname}.png".format(outname=outname))
        
    
import matplotlib as mpl

def make_legend(serie,cmap,label="",path=None):
    
    #todo: log flag
        
    fig = plt.figure(figsize=(8,3))
    ax1 = fig.add_axes([0.05, 0.80, 0.9, 0.15])

    vmin=serie.min()
    vmax=serie.max()

    # define discrete bins and normalize
    # bounds =np.linspace(vmin,vmax,5)
    # norm = mpl.colors.BoundaryNorm(bounds, cmap.N)

    #continuous legend
    norm = mpl.colors.Normalize(vmin=vmin, vmax=vmax)

    cb = mpl.colorbar.ColorbarBase(ax1, cmap=cmap, norm=norm, orientation='horizontal')
    #cb.ax.set_xticklabels(['0.01%','0.1%','1%','10%'])
    cb.set_label(label)
    if path is not None:
        plt.savefig(path+".png",bbox_inches="tight",transparent=True)  
    plt.close(fig)    
    return Image(path+".png", width=img_width   )  
    
############################################################################# 
#######################            FROM R             ####################### 
#############################################################################
import glob, sys, shutil
from subprocess import call, Popen, PIPE

def map_with_r(df_maps,map_name,**kwargs):
    
    df_maps.index =df_maps.index.str.lower()
    df_maps.index.name="id"
    df_maps.to_csv("input_data_for_map.csv",header=True)

    #Writes the new R code with the arguments given to this function
    with open("make_map.r", "wt") as fout:
        with open("make_map.r.model", "rt") as fin:
            for line in fin:
                fout.write(line.format(**kwargs))
    
    
    p=Popen("rscript make_map.r", stdout=PIPE);
    print("Making the map....")
    sys.stdout.flush()

    (output, err) = p.communicate()
    exit_code = p.wait()

    if exit_code:
        print(err,output)    
    else:
        print("Map done")

        
    print("There was no data for the following districts: "+", ".join(pd.read_csv("missing_admin_zones.txt",sep=" ",encoding="latin-1",squeeze=True)))    
    
    shutil.copy("output_map.png",map_name)
    
    return 

############################################################################# 
#######################         FROM GEOPANDAS        ####################### 
############################################################################# 
import geopandas as gpd
def map_from_gpd(df,title="Risk to assets",col_to_plot="risk_to_assets",figname="risk_to_assets.png",cm="BuPu"):

    plt.figure(figsize=(9,9))

    df.plot(column=col_to_plot,colormap=cm)

    plt.axis("off")

    plt.title(title)
    
    plt.savefig(figname)