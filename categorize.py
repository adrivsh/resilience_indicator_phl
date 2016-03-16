import pandas as pd

def make_tiers(series,labels=["Low","Mid","High"]):
    """Cuts data in top, middle, and bottom tier"""
    return pd.cut(series,[series.min()-1e3]+series.quantile([1/3,2/3]).tolist()+[series.max()+1e3],labels=labels).sort_values() 

def categories_to_formated_excel_file(df_cat,filename="tiers.xlsx"):
    """outputs tier categories in format excel file"""
    
    with pd.ExcelWriter(filename, engine='xlsxwriter') as writer:
        workbook=writer.book
        
        # Add a format. Light red fill with dark red text.
        red = workbook.add_format({#'bg_color': '#f4a582',
                                       'font_color': '#ca0020'})
        orange = workbook.add_format({#'bg_color': '#f7f7f7',
                                       'font_color': '#000000'})

        blue = workbook.add_format({#'bg_color': '#92c5de',
                                       'font_color': '#0571b0'})
        
        #new sheet with data
        df_cat.to_excel(writer,sheet_name="tiers")
        
        #conditional format
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

        #width of the columns
        worksheet.set_column(0, 0, 20)
        worksheet.set_column(1, 1, 14)
        worksheet.set_column(2, 2, 8)
        
        #filter
        worksheet.autofilter('A1:C1')
        
        #freeze panes
        writer.sheets["tiers"].freeze_panes(1, 1)