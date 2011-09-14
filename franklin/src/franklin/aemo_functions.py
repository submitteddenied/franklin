'''
Created on 14/09/2011

@author: mjensen
'''

def base_load(time):
    return (time.day % 7) * 1000 + (time.interval % 50) * 500