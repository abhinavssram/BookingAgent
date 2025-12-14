import datetime
from langchain.tools import tool

@tool()
def get_current_date():
    ''' Gives you user exact time with Date YYYY-MM-DD HH:MM:SS.mmmm+HH:MM  
        example: 2025-12-14 12:54:49.769122+05:30 The last part after + is 05:30  that means GMT+5:30 which is Asia/kolkata 
        
        You can infer the current user exact time with Date
    '''
    return "Here is the user current time: "+ str(datetime.datetime.now().astimezone()) + " understand the format and get the timezone"