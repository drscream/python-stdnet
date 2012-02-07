'''Experimental!
This is an experimental module for converting ColumnTS into
dynts.timeseries.
'''
from stdnet.apps.columnts import models as columnts
from stdnet import orm 

import numpy as ny

from dynts import timeseries, tsname


class ColumnTS(columnts.ColumnTS):
    '''Integrate stdnet timeseries with dynts_ TimeSeries'''
    
    def front(self, *fields):
        '''Return the front pair of the structure'''
        ts = self.irange(0, 0, fields = fields)
        if ts:
            return ts.start(),ts[0]
    
    def back(self, *fields):
        '''Return the back pair of the structure'''
        ts = self.irange(-1, -1, fields = fields)
        if ts:
            return ts.end(),ts[0]
        
    def load_data(self, result):
        loads = self.pickler.loads
        vloads = self.value_pickler.loads
        dt,va = result
        if result[0]:
            dates = ny.array([loads(t) for t in dt])
            # fromiter does not work for object arrays
            #dates = ny.fromiter((loads(t) for t in dt),
            #                    self.pickler.type,
            #                    len(dt)) 
            fields = []
            vals = []
            for f,data in va:
                fields.append(f)
                vals.append([vloads(d) for d in data])
            values = ny.array(vals).transpose()
            name = tsname(*fields)
        else:
            name = None
            dates = None
            values = None
        return timeseries(name = name,
                          date = dates,
                          data = values)
    
    def _get(self, result):
        ts = self.load_data(result)
        return ts.front()
    

class TS(orm.TS):
    
    def irange(self, start = 0, end = -1, **kwargs):
        kwargs['raw'] = True
        return super(TS,self).irange(start, end, **kwargs)
    
    def range(self, start, stop, **kwargs):
        kwargs['raw'] = True
        return super(TS,self).range(start, stop, **kwargs)
    
    def load_data(self, response):
        loads = self.pickler.loads
        vloads = self.value_pickler.loads
        times = [loads(float(t)) for t in response[::2]]
        values = [vloads(v) for v in response[1::2]]
        return timeseries(date = times,
                          data = values,
                          name = self.id,
                          val_type = None)        
        

class TimeSeriesField(orm.TimeSeriesField):
    
    def structure_class(self):
        return TS
    
    
class ColumnTSField(columnts.ColumnTSField):
    
    def structure_class(self):
        return ColumnTS
    