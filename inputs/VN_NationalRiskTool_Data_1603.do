***************************************************************************************
********** ASSESSING WELFARE RISKS AND SOCIO-ECONOMIC RESILIENCE IN VIETNAM  ********** 
***************************************************************************************


*** Data set used: VHLSS2014 + VHLSS2012 + VHLSS2010 + various geo-spatial datasets

clear mata
#delimit ;
drop _all;
set mem 100m;
set matsize 1100;
set more off;
capture log close;

global datafile "C:\CCPovVietnam_P152574\Analysis\EnvRisk\Data\Do-files+dta\2016_02\VN_EnvRisk_Dataset_HH_FINAL_1602.dta";
global path 		"L:\P155824_CC&GGVietnam\NationalRiskTool";
global hhdata 		"VN_NationaRiskTool_Data_1603.dta";

***************************************************************;
******************** DATASET PREPARATION   ********************;
***************************************************************;

************************************************************;
********** 1. CONSTRUCT HOUSEHOLD-LEVEL VARIABLES **********;
************************************************************;
use $datafile;

*** REGION CORRECTION ***;
drop if mi(region);

*** EXPRESS INCOME VALUES (MEAUSRED in 2010 VDN) IN 2011 PPP VALUES ***;
*** from WDI:	PPP Conversion factor (LCU per international $) 2011 = 6709.19157781948 ***; 
*** from WDI: 	CPI 2011 = 118.67747712054 (CPI2010 = 100) ***;
gen pcinc_ppp = ipc_tot*1.187	*(1000/6709);

*** CALCULATE NUMBER OF PEOPLE BELOW POVERTY LINE ***;
gen povline = 3.49*365;
gen poor = (pcexp_ppp)<povline;

*** HOUSING MATERIAL ***; 
tab hs_pole, gen(hs_pole);
tab hs_wall, gen(hs_wall);
tab hs_roof, gen(hs_roof);

*** SHARE OF INCOME FROM TRANSFERS ***;
rename ish_trans transfers;

*** EARLY WARNING ***; 
rename a_radio info_radio;
rename a_tv info_tv;
rename a_mobile info_cell;

*** SOCIAL PROTECTION ***;
rename support sp_scheme;
gen sp_remit = earnrein>0;

global var "pcinc_ppp povline poor transfers sp_scheme sp_remit 
			info_radio info_cell info_tv
			hs_pole1 hs_pole2 hs_pole3 hs_pole4 hs_pole5 
			hs_wall1 hs_wall2 hs_wall3 hs_wall4 hs_wall5 hs_wall6
			hs_roof1 hs_roof2 hs_roof3 hs_roof4 hs_roof5";

**********************************************************;
********** 2. CALCULATE REGIONAL-LEVEL AVERAGES **********;
**********************************************************;		

*** RESHAPE DATASET TO WIDE FORMAT ***;
keep  year regid region province district commune HID10 weight hhsweight $var;
reshape wide $var weight hhsweight, i(regid region province district commune HID10) j(year);	

*** CALCULATE AVERAGE PER REGION ***;
forval i = 1/8 { ;
foreach x of global var { ;	
forval y = 2010 (2) 2014 { ;
		summarize `x'`y' [w=hhsweight`y'] if regid == `i', detail ;
		replace `x'`y' = r(mean) if regid == `i' ;
}; }; } ;

*** PREPARE PROVINCE-LEVEL DATASET ***;
forval y = 2010 (2) 2014 { ;
global var`y' 	"pcinc_ppp`y' povline`y' poor`y' transfers`y' sp_scheme`y' sp_remit`y' 
				info_radio`y' info_cell`y' info_tv`y'
				hs_pole1`y' hs_pole2`y' hs_pole3`y' hs_pole4`y' hs_pole5`y' 
				hs_wall1`y' hs_wall2`y' hs_wall3`y' hs_wall4`y' hs_wall5`y' hs_wall6`y'
				hs_roof1`y' hs_roof2`y' hs_roof3`y' hs_roof4`y' hs_roof5`y'";	
};
collapse (mean) $var2010 $var2012 $var2014, by(regid region province);
	
		
*** LABEL VARIABLES ***;
forval y = 2010 (2) 2014 { ;
label var pcinc_ppp`y' 	"`y' per-capita income in 2011 PPP";
label var povline`y' 	"`y' national poverty line = $3.49-a-day in 2011 PPP";
label var poor`y' 		"`y' number of people below national poverty line" ; 
label var transfers`y' 	"`y' share of income from transfers";

label var info_tv`y'	"`y' ownership of tv";
label var info_radio`y' "`y' ownership of radio";
label var info_cell`y' 	"`y' ownership of cell phones";

label var sp_scheme`y' 	"`y' participation in aid schemes";
label var sp_remit`y'  	"`y' income from international remittances";

label var hs_pole1`y' 	"`y' material of housing poles = concrete";
label var hs_pole2`y'  	"`y' material of housing poles = stone";
label var hs_pole3`y' 	"`y' material of housing poles = iron/steel/good wood";
label var hs_pole4`y' 	"`y' material of housing poles = poor quality wood/bamboo";
label var hs_pole5`y' 	"`y' material of housing poles = others";
label var hs_wall1`y' 	"`y' material of housing wall = concrete";
label var hs_wall2`y'  	"`y' material of housing wall = bricks/stone";
label var hs_wall3`y' 	"`y' material of housing wall = wood/metal";
label var hs_wall4`y' 	"`y' material of housing wall = soil/straw";
label var hs_wall5`y' 	"`y' material of housing wall = bamboo";
label var hs_wall6`y' 	"`y' material of housing wall = others";
label var hs_roof1`y' 	"`y' material of housing roof = concrete";
label var hs_roof2`y' 	"`y' material of housing roof = tiles";
label var hs_roof3`y' 	"`y' material of housing roof = slabs";
label var hs_roof4`y' 	"`y' material of housing roof = leave/straw";
label var hs_roof5`y' 	"`y' material of housing roof = others";
};

saveold $hhdata,replace;


