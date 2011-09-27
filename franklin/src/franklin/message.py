'''
Created on 12/09/2011

@author: Michael
'''

class MessageDispatcher(object):
    def __init__(self):
        '''
        Constructs a new MessageDispatch
        '''
        #maps ids -> message[]
        self.inboxes = {}
    
    def fetch_messages(self, id):
        '''
        Gets all the waiting messages for 'id' and returns them, clearing them
        from 'id's inbox
        '''
        if(not self.inboxes.has_key(id)):
            messages = []
        else:
            #copy the list in inboxes
            messages = list(self.inboxes[id])
            #clear the list
            self.inboxes[id] = []
        return messages
    
    def send(self, message, id):
        '''
        Sends the message to the inbox with the given id.
        '''
        if(not self.inboxes.has_key(id)):
            self.inboxes[id] = []
        
        self.inboxes[id].append(message)

class Message(object):
    '''
    A Message is a bundle of information, structured into an object. They are
    passed around by the MessageDispatcher.
    '''
    nextId = 0
    def __init__(self, sender):
        self.id = Message.nextId
        Message.nextId += 1
        self.sender = sender

class GenerationAmendment(Message):
    '''
    A generation amendment adjusts the amount of power that can be generated, 
    but does not adjust the price. This is to allow generators to run "slow"
    equipment that may need to warm up or cool down
    '''
    
    def __init__(self, sender, time, watts):
        super(GenerationAmendment, self).__init__(sender)
        self.time = time
        self.watts = watts

class Bid(GenerationAmendment):
    '''
    A Bid is a message that is sent to AEMO specifying how much electricity can
    be generated in a time interval and for what price
    '''
    def __init__(self, sender, time, watts, price):
        super(Bid, self).__init__(sender, time, watts)
        self.price = price
        
class LoadPrediction(Message):
    
    def __init__(self, sender, time, watts):
        super(LoadPrediction, self).__init__(sender)
        self.time = time
        self.watts = watts
        
class Dispatch(LoadPrediction):
    pass