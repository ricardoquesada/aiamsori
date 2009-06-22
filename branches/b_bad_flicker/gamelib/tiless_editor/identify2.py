# This code is so you can run the samples without installing the package( e importar simplejson)
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import simplejson




class MapManipulator(object):
    def __init__(self, output_filename):
	self.output_filename = output_filename

    def read_map(self):
        mapjson = None
        try:
            f = open(self.output_filename)
	    mapjson = simplejson.load(f)
        except:
            print 'error cargando'
        try:
            f.close()
        except:
            pass
        self.map = mapjson

##        if mapjson is None:
##            return
##        layers = mapjson['layers']
            
##        for layer in layers:
##            layer_type = layer['layer_type']
##            print 'layer_type',layer_type
##            print 'layer label:',layer['label']
##            print 'type(layer["data"]):',type(layer['data']) #dict
##            print "len(layer['data']):", len(layer['data']) # 1 , key = 'sprites'
##            cnt = 10
##            for e in layer['data']['sprites']:
##                print '\telem type, value%s:'%e,type(e) 
##                cnt -= 10
##                if not cnt:
##                    break

    def name_instances(self):
        interesting = ['furniture', 'zombie_spawn', 'item_spawn',
                       'waypoints','lights' ]
        layers = self.map['layers']
        for layer in layers:
            layer_type = layer['layer_type']
            if layer_type!='sprite':
                continue
            if layer['label'] not in interesting:
                continue
            # pass one: count labeled sprites
            cnt = 0; max_id = 0
            for e in layer['data']['sprites']:
                if e['label'] != None:
                    i = e['label'].rfind('#')
                    if i>-1:
                        try:
                            n = int(e['label'][i+1:])
                            if n>max_id:
                                max_id = n
                        except:
                            print 'error converting' 
                            pass
                    cnt +=1
            num_sprites = len(layer['data']['sprites'])

            
            print 'layer label:',layer['label']
            print '\tnum_sprites:',num_sprites
            print '\tcnt labeled sprites:',cnt
            print '\tmax_id:',max_id

            # pass two: label the unlabeled sprites as <layername>:<shortname>#num
            def shortname(fname):
                j = fname.rfind('.')
                if j>-1:
                    fname = fname[:j] # strip extension
                i = fname.rfind('/')
                fname = fname[i+1:]
                return fname
                
            prefix = layer['label']
            if cnt == 0:
                num = 0
            else:
                num = max_id + 11
            for e in layer['data']['sprites']:
                if e['label'] is None:
                    e['label'] = '%s:%s#%d'%(prefix,shortname(e['filename']),num)
##                    print 'new label:',e['label']
##                    print 'fname:',e['filename']
                    num +=1

    def dump_interesting_entities(self):
        interesting = ['furniture', 'zombie_spawn', 'item_spawn',
                       'waypoints','lights' ]
        layers = self.map['layers']
        print "#interesting entities"
        for layer in layers:
            layer_type = layer['layer_type']
            if layer_type!='sprite':
                continue
            if layer['label'] not in interesting:
                continue
            print "%s = [\n"%layer['label']
            for e in layer['data']['sprites']:
                if e['label'] != None:
                    print '\t"%s",'%e['label']
            print ']'
        

    def write_json(self):
        if self.map is None:
            return
        try:
            f = open(self.output_filename,'w')
	    simplejson.dump(self.map,f,indent=4)
        except:
            print 'error guardando'
        try:
            f.close()
        except:
            pass
            

if __name__ == '__main__':
    import optparse

    parser = optparse.OptionParser()
    parser.add_option("-f", "--filename", dest="filename", default='map.json',
                      help="output filename", metavar="FILE")
    (options, args) = parser.parse_args()
	
    test = MapManipulator(options.filename)
    test.read_map()
    test.name_instances()
    test.write_json()
    test.dump_interesting_entities()
    
