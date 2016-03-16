import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

############################################################################# 
#######################         FROM SVG              ####################### 
#############################################################################     
    
from bs4 import BeautifulSoup    
from IPython.display import Image, display, HTML, SVG
img_width = 400

import os, shutil
from subprocess import Popen, PIPE, call 

def make_map_from_svg(series_in, svg_file_path, outname, color_maper=plt.cm.get_cmap("Blues"), label = "", outfolder ="img/" , new_title=None, verbose=True):
    """Makes a cloropleth map and a legend from a panda series and a blank svg map. 
    Assumes the index of the series matches the SVG classes
    Saves the map in SVG, and in PNG if Inkscape is installed.
    if provided, new_title sets the title for the new SVG map
    """
    
    #simplifies the index to lower case without space
    series_in.index = series_in.index.str.lower().str.replace(" ","_").str.replace("-","_").str.replace(".","_").str.replace("(","_").str.replace(")","_")
    
    #compute the colors 
    color = data_to_rgb(series_in,color_maper=color_maper)

    #Builds the CCS style for the new map  (todo: this step could get its own function)
    style_base =\
    """.{depname}
    {{  
       fill: {color};
       stroke:#000000;
       stroke-width:2;
    }}"""

    #Default style (for regions which are not in series_in)
    style =\
    """.default
    {
    fill: #bdbdbd;
    stroke:#ffffff;
    stroke-width:2;
    }
    """
    
    #builds the style line by line (using lower case identifiers)
    for c in series_in.index:
        style= style       + style_base.format(depname=c,color=color[c])+ "\n"   

    #output file name
    target_name = outfolder+"map_of_"+outname

    #read input 
    with open(svg_file_path, 'r',encoding='utf8') as svgfile: #MIND UTF8
        soup=BeautifulSoup(svgfile.read(),"xml")

    #names of regions to lower case without space   
    for p in soup.findAll("path"):
        p["class"]=p["class"].lower().replace(" ","_").replace("-","_").replace(".","_").replace("(","_").replace(")","_")
        #Update the title (tooltip) of each region with the numerical value (ignores missing values)
        try:
            p.title.string += "{val:.3%}".format(val=series_in[p["class"]])
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
        
   
    #Link to SVG
    display(HTML("<a target='_blank' href='"+target_name+".svg"+"'>SVG "+new_title+"</a>"))  #Linking to SVG instead of showing SVG directly works around a bug in the notebook where style-based colouring colors all the maps in the NB with a single color scale (due to CSS)
    
    
    #reports missing data        
    if verbose:        
        places_in_soup = [p["class"] for p in soup.findAll("path")]        
        data_missing_in_svg = series_in[~series_in.index.isin(places_in_soup)].index.tolist()
        data_missing_in_series = [p for p in places_in_soup if (p not in series_in.index.tolist())]
        
        back_to_title = lambda x: x.replace("_"," ").title()
    
        if data_missing_in_svg:
            print("Missing in SVG: "+"; ".join(map(back_to_title,data_missing_in_svg)))
        if data_missing_in_series:
            print("Missing in series: "+"; ".join(map(back_to_title,data_missing_in_series)))

    if shutil.which("inkscape") is None:
        print("cannot convert SVG to PNG. Install Inkscape to do so.")
        could_do_png_map = False
    else:
        #Attempts to inkscape SVG to PNG    
        process=Popen("inkscape -f {map}.svg -e {map}.png -d 150".format(map=target_name, outfolder = outfolder) , shell=True, stdout=PIPE,   stderr=PIPE)
        out, err = process.communicate()
        errcode = process.returncode
        if errcode:
            could_do_png_map = False
            print("Could not transform SVG to PNG. Error message was:\n"+err.decode())
        else:
            could_do_png_map = True

    #makes the legend with matplotlib
    l = make_legend(100*series_in,color_maper,label,outfolder+"legend_of_"+outname)
    
    if shutil.which("convert") is None:
        print("Cannot merge map and legend. Install ImageMagick® to do so.")
    elif could_do_png_map:
        #Attempts to downsize to a single width and concatenate using imagemagick
        call("convert "+outfolder+"legend_of_{outname}.png -resize {w} small_legend.png".format(outname=outname,w=img_width), shell=True )
        call("convert "+outfolder+"map_of_{outname}.png -resize {w} small_map.png".format(outname=outname,w=img_width) , shell=True)
        
        merged_path = outfolder+"map_and_legend_of_{outname}.png".format(outname=outname)
        
        call("convert -append small_map.png small_legend.png "+merged_path, shell=True)
        
        #removes temp files
        if os.path.isfile("small_map.png"):
            os.remove("small_map.png")
        if os.path.isfile("small_legend.png"):
            os.remove("small_legend.png")
    
        if os.path.isfile(merged_path):
            return Image(merged_path)
        
    
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
    """This functions transforms  data series into a series of color, using a colormap."""

    data_n = normalizer(serie,norm_param)

    #here matplolib color mappers will just fill nas with the lowest color in the colormap
    colors = pd.DataFrame(color_maper(data_n),index=serie.index, columns=["r","g","b","a"]).applymap(num_to_hex)

    out = "#"+colors.r+colors.g+colors.b
    out[serie.isnull()]=na_color
    return out.str.upper()


    