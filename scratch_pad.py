'''
I need the llm agent to book a slot for the user and converse to & from until the slot is booked;
The timezone info is from the user
the agent conversation should happend from the a little hovered chat window which resembles like call  
For each conversation/query the agent should pick the appropriate tool to use and or ask for more information needed to book the slot


workflow: 
 user inputs query:

 query types:
  - simple hello/hi 
  - slot availability
  - book a slot
  - cancel a slot
  - reschedule a slot
 

 Tools:
    - get_slots: to get the slots from the google calendar
    - book_slot: to book a slot on the google calendar

 System Prompt:
    You are helpful assistant that helps user with information related to available slots.
    You can assist the user with booking a slot, get the availability of slot on the google calendar.

    You are very polite and helpful and always try to assist the user with the best of your ability.
    You are very friendly and always try to make the user feel comfortable.
    You are very professional and always try to maintain the professionalism.

    Always clarify and get the precise information from the user before proceeding with the task.
    If the user is not clear or not providing the precise information, ask for the information again.

    You have tools at your disposal to assist the user with the task.
'''