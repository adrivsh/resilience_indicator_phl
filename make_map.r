rm(list=ls()) #claers all memory

# WHAT COLUMNS DO WE HAVE?
library(RColorBrewer)
library(plyr)
library(rgeos)
library(maptools)
library(ggplot2)

# MAP
admin_map_raw <- readShapeSpatial("PHL_adm1.shp")

# admin_map_raw = gSimplify(admin_map_raw,0.03, topologyPreserve=TRUE)


admin_map = admin_map_raw
admin_map$NAME_1 <- tolower(admin_map_raw$NAME_1)


df_map <- fortify(admin_map, region = "NAME_1")

# READ IN DATA
df_data <- read.csv("input_data_for_map.csv")

namesInData <- levels(factor(df_data$id))
namesInMap <- levels(factor(df_map$id))

namesInData[which(!namesInData %in% namesInMap)];

missing_data = namesInMap[which(!namesInMap %in% namesInData)]
write.table(missing_data,"missing_admin_zones.txt")

# source("make_map.r", echo=TRUE)

q=ggplot() + geom_map(map = df_map, aes(fill = resilience, map_id =id),data=df_data) 	+ 
	expand_limits(x = df_map$long, y = df_map$lat) +
	theme(panel.border = element_blank(), panel.grid.major = element_blank(), 
		panel.grid.minor = element_blank(), 
		panel.background = element_rect(fill='white'),
		axis.line = element_blank(), 
		axis.text.x = element_blank(), 
		axis.text.y = element_blank(),
		axis.ticks = element_blank(), 
		axis.title.x = element_blank(), 
		axis.title.y = element_blank()
		)+
	scale_fill_gradientn(name= "Capacity" , colours =rev(brewer.pal(5,'Blues')), na.value = "light grey")
# color_palette = 
ggsave(filename="output_map.png",q)



